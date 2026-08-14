"""Document-parser seam: Docling (real) ↔ passthrough stub.

Used by RagOrchestrator ingestion to turn an uploaded PDF/image/text into markdown
chunks before embedding. Parsing runs in a worker thread and is launched as a background
task (the upload endpoint returns 202 immediately).
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParsedDoc:
    markdown: str
    title: str = ""


class DocumentParser(ABC):
    name = "base"
    is_stub = False

    @abstractmethod
    def parse(self, path: str, *, mime: Optional[str] = None) -> ParsedDoc:
        ...


class StubParser(DocumentParser):
    """Reads UTF-8 text files verbatim; for other types returns a placeholder."""

    name = "stub"
    is_stub = True

    def parse(self, path: str, *, mime: Optional[str] = None) -> ParsedDoc:
        title = os.path.basename(path)
        if mime and mime.startswith("text") or path.lower().endswith((".txt", ".md")):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    return ParsedDoc(markdown=fh.read(), title=title)
            except Exception:  # noqa: BLE001
                pass
        return ParsedDoc(markdown=f"[uploaded file: {title} — install the parse extra to read it]", title=title)


class DoclingParser(DocumentParser):
    name = "docling"

    def __init__(self) -> None:
        try:
            from docling.document_converter import DocumentConverter  # type: ignore  # noqa: F401
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("docling not installed (pip install -e .[parse])") from exc
        self._Converter = __import__("docling.document_converter", fromlist=["DocumentConverter"]).DocumentConverter

    def parse(self, path: str, *, mime: Optional[str] = None) -> ParsedDoc:
        conv = self._Converter()
        result = conv.convert(path)
        md = result.document.export_to_markdown()
        return ParsedDoc(markdown=md, title=os.path.basename(path))


def chunk_markdown(markdown: str, *, target_chars: int = 800, overlap: int = 80) -> List[str]:
    """Greedy paragraph/size chunker with overlap."""
    paragraphs = [p for p in markdown.split("\n\n") if p.strip()]
    chunks: List[str] = []
    buf = ""
    for para in paragraphs:
        if len(buf) + len(para) > target_chars and buf:
            chunks.append(buf.strip())
            buf = buf[-overlap:] if overlap else ""
        buf = (buf + "\n\n" + para).strip() if buf else para.strip()
    if buf.strip():
        chunks.append(buf.strip())
    return chunks or [markdown.strip()]
