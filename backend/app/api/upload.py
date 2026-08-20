from __future__ import annotations

import hashlib
import io
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.core.auth import require_api_key
from app.core.config import settings
from app.services.retrieval.embeddings.embedder import embed_texts
from app.services.retrieval.vector_store.factory import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

_MAX_FILE_SIZE_MB = 50
_MAX_FILE_SIZE = _MAX_FILE_SIZE_MB * 1024 * 1024
_CHUNK_SIZE = 500  # characters per chunk
_CHUNK_OVERLAP = 50

ALLOWED_MIME_TYPES = {
    "text/plain",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
    "text/csv",
}


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    if not text.strip():
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def _extract_text(content: bytes, content_type: str, filename: str) -> str:
    if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(content))
            return "\n\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            logger.warning("pypdf not installed; treating PDF as plain text")
    if content_type in (
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ) or filename.lower().endswith((".doc", ".docx")):
        try:
            import docx

            doc = docx.Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            logger.warning("python-docx not installed; treating as plain text")
    return content.decode("utf-8", errors="replace")


@router.post("")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    _auth: str = Depends(require_api_key),
) -> dict[str, Any]:
    # Validate size
    raw = await file.read()
    if len(raw) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {_MAX_FILE_SIZE_MB} MB.",
        )

    content_type = file.content_type or "text/plain"
    filename = file.filename or "upload"

    # Extract text
    try:
        text = _extract_text(raw, content_type, filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract text: {e}") from e

    if not text.strip():
        raise HTTPException(status_code=422, detail="Document appears to be empty or unreadable.")

    # Chunk
    chunks = _chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=422, detail="No usable content found in document.")

    # Embed (batch)
    try:
        import asyncio
        embeddings = await asyncio.to_thread(embed_texts, chunks)
    except Exception as e:
        logger.exception("Embedding failed for %s", filename)
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}") from e

    # Store via factory (not hardcoded Chroma)
    file_hash = hashlib.sha256(raw).hexdigest()[:16]
    base_id = f"{uuid.uuid4().hex[:8]}-{file_hash}"
    ids = [f"{base_id}-chunk{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source": filename,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "file_hash": file_hash,
            "content_type": content_type,
        }
        for i in range(len(chunks))
    ]

    try:
        store = get_vector_store()
        store.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
    except Exception as e:
        logger.exception("Vector store write failed for %s", filename)
        raise HTTPException(status_code=500, detail=f"Storage failed: {e}") from e

    logger.info("Uploaded %s: %d chunks stored (file_hash=%s)", filename, len(chunks), file_hash)
    return {
        "status": "ok",
        "filename": filename,
        "chunks": len(chunks),
        "file_hash": file_hash,
        "document_ids": ids,
    }
