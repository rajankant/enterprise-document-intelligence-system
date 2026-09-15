from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any


class RAGService:
    """A lightweight local RAG service for document retrieval.

    This version intentionally keeps dependencies minimal and uses a simple
    keyword-overlap retrieval strategy so users can test RAG functionality even
    without a full vector DB or external embedding service.
    """

    def __init__(self, docs_dir: str | None = None):
        self.docs_dir = Path(docs_dir) if docs_dir else Path(__file__).resolve().parents[1] / "app" / "input"
        self._documents: List[Dict[str, Any]] = []

    def _read_text(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        if path.suffix.lower() == ".pdf":
            try:
                import PyPDF2

                reader = PyPDF2.PdfReader(str(path))
                pages = []
                for page in reader.pages:
                    text = page.extract_text() or ""
                    pages.append(text)
                return "\n\n".join(pages)
            except Exception:
                return ""

        return path.read_text(encoding="utf-8", errors="ignore")

    def _split_text(self, text: str, chunk_size: int = 500) -> List[str]:
        cleaned = " ".join(text.split())
        if len(cleaned) <= chunk_size:
            return [cleaned] if cleaned else []

        chunks: List[str] = []
        for idx in range(0, len(cleaned), chunk_size):
            chunk = cleaned[idx: idx + chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def _score_chunk(self, query: str, chunk: str) -> float:
        q_tokens = {token.lower() for token in query.replace("?", " ").split() if token}
        c_tokens = {token.lower() for token in chunk.split() if token}
        if not q_tokens:
            return 0.0

        overlap = q_tokens & c_tokens
        if not overlap:
            return 0.0

        return len(overlap) / max(1, len(q_tokens))

    def index_documents(self, document_paths: List[str]) -> None:
        self._documents = []
        for document_path in document_paths:
            text = self._read_text(document_path)
            for chunk in self._split_text(text):
                self._documents.append(
                    {
                        "id": f"{document_path}:{len(self._documents)}",
                        "path": document_path,
                        "text": chunk,
                    }
                )

    def query(self, question: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self._documents:
            default_docs = [
                str(Path(__file__).resolve().parents[1] / "app" / "input" / "JD-AIPython (1).pdf"),
            ]
            if os.path.exists(default_docs[0]):
                self.index_documents(default_docs)
            else:
                return []

        scored = []
        for doc in self._documents:
            score = self._score_chunk(question, doc["text"])
            if score > 0:
                scored.append({"id": doc["id"], "text": doc["text"], "score": round(score, 4), "path": doc["path"]})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def index_directory(self, directory: str) -> None:
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        files = [str(p) for p in path.iterdir() if p.is_file()]
        self.index_documents(files)
