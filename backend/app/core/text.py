"""Helpers for normalising LangChain message content.

LLM ``content`` values are typed as ``str | list[ContentBlock]``; downstream
code (``.strip()``, ``.split()``, ``json.loads``) needs plain text. Centralising
the normalisation avoids repeated casts and crashes when a provider returns a
list of content blocks instead of a plain string.
"""

from __future__ import annotations

from typing import Any


def content_to_str(content: Any) -> str:
    """Return a plain-text representation of an LLM message ``content`` value.

    Handles:
    - ``str`` (the common case, returned unchanged)
    - ``list`` of content blocks, e.g. ``[{"type": "text", "text": "..."}]``
    - ``None`` (returned as ``""``)
    - anything else, stringified defensively
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return "" if content is None else str(content)
