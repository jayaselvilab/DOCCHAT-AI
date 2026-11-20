"""TF-IDF retrieval: find the chunks most relevant to a question."""

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .chunker import Chunk


@dataclass
class Hit:
    chunk: Chunk
    score: float


class Retriever:
    """Builds a TF-IDF index over chunks and searches it by cosine similarity."""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None

    def build(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        if not chunks:
            self._vectorizer, self._matrix = None, None
            return
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self._matrix = self._vectorizer.fit_transform(c.text for c in chunks)

    def search(self, question: str, top_k: int = 4, min_score: float = 0.05) -> list[Hit]:
        if self._vectorizer is None or self._matrix is None:
            return []
        query_vec = self._vectorizer.transform([question])
        scores = cosine_similarity(query_vec, self._matrix).ravel()
        ranked = scores.argsort()[::-1][:top_k]
        return [
            Hit(chunk=self.chunks[i], score=float(scores[i]))
            for i in ranked
            if scores[i] >= min_score
        ]
