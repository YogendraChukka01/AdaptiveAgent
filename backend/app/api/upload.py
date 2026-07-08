from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, UploadFile

from app.services.retrieval.embeddings.embedder import embed_texts
from app.services.retrieval.vector_store.chroma_store import add_documents

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def _extract_text(file: UploadFile) -> str:
    content = file.file.read()
    if file.filename and file.filename.endswith(".pdf"):
        try:
            import io

            import fitz

            doc = fitz.open(stream=content, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        except ImportError:
            return content.decode("utf-8", errors="ignore")
    elif file.filename and file.filename.endswith(".docx"):
        try:
            import io

            from docx import Document

            doc = Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return content.decode("utf-8", errors="ignore")
    else:
        return content.decode("utf-8", errors="ignore")


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
        if start >= len(words):
            break
    return chunks


@router.post("")
async def upload_document(file: UploadFile):
    if not file.filename:
        return {"error": "No filename provided"}

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"error": f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}"}

    text = _extract_text(file)
    chunks = _chunk_text(text)

    ids = [str(uuid.uuid4()) for _ in chunks]
    embeddings = embed_texts(chunks)
    metadatas = [{"source": file.filename, "chunk": i} for i in range(len(chunks))]

    add_documents(
        collection_name="safeagent_docs",
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    return {
        "filename": file.filename,
        "chunks": len(chunks),
        "total_characters": len(text),
    }
