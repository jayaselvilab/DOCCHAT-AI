"""The RAG pipeline: index documents, retrieve passages, generate an answer."""

import anthropic

from . import config
from .chunker import Chunk, chunk_text
from .llm import ask_claude, label
from .loader import load_folder
from .retriever import Hit, Retriever

NOT_FOUND = "I could not find anything about that in the uploaded documents."


class RagService:
    def __init__(self) -> None:
        self.documents: dict[str, str] = {}
        self.retriever = Retriever()

    # ---- indexing -------------------------------------------------------
    def _rebuild(self) -> None:
        chunks: list[Chunk] = []
        for name, text in self.documents.items():
            chunks.extend(
                chunk_text(name, text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
            )
        self.retriever.build(chunks)

    def load_folder(self, folder=None) -> None:
        self.documents.update(load_folder(folder or config.DOCS_DIR))
        self._rebuild()

    def add_document(self, name: str, text: str) -> None:
        self.documents[name] = text
        self._rebuild()

    def remove_document(self, name: str) -> bool:
        removed = self.documents.pop(name, None) is not None
        if removed:
            self._rebuild()
        return removed

    def list_documents(self) -> list[dict]:
        counts: dict[str, int] = {}
        for chunk in self.retriever.chunks:
            counts[chunk.source] = counts.get(chunk.source, 0) + 1
        return [{"name": n, "chunks": counts.get(n, 0)} for n in self.documents]

    # ---- answering ------------------------------------------------------
    def ask(self, question: str) -> dict:
        hits = self.retriever.search(question, config.TOP_K, config.MIN_SCORE)
        sources = [
            {"label": label(h), "score": round(h.score, 3), "text": h.chunk.text}
            for h in hits
        ]
        if not hits:
            return {"answer": NOT_FOUND, "mode": "no_match", "sources": []}

        if not config.ANTHROPIC_API_KEY:
            return {
                "answer": self._retrieval_only_answer(hits),
                "mode": "retrieval_only",
                "sources": sources,
            }

        try:
            answer = ask_claude(question, hits)
            return {"answer": answer, "mode": "claude", "sources": sources}
        except anthropic.APIError as exc:
            note = f"(Claude API error: {exc.__class__.__name__}. Showing matching passages instead.)\n\n"
            return {
                "answer": note + self._retrieval_only_answer(hits),
                "mode": "retrieval_only",
                "sources": sources,
            }

    @staticmethod
    def _retrieval_only_answer(hits: list[Hit]) -> str:
        passages = "\n\n".join(f"[{label(h)}]\n{h.chunk.text}" for h in hits[:2])
        return (
            f"Best matching passages:\n\n{passages}\n\n"
            "(Set ANTHROPIC_API_KEY to get a written answer from Claude.)"
        )
