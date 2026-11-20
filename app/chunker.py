"""Split documents into overlapping word-based chunks."""

from dataclasses import dataclass


@dataclass
class Chunk:
    source: str   # file the chunk came from
    index: int    # position of the chunk inside that file
    text: str


def chunk_text(source: str, text: str, size: int = 120, overlap: int = 30) -> list[Chunk]:
    """Split text into chunks of `size` words, sharing `overlap` words.

    Overlap keeps a sentence that straddles a boundary retrievable
    from at least one chunk.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and smaller than size")

    words = text.split()
    if not words:
        return []

    step = size - overlap
    chunks: list[Chunk] = []
    for index, start in enumerate(range(0, len(words), step)):
        piece = words[start:start + size]
        chunks.append(Chunk(source=source, index=index, text=" ".join(piece)))
        if start + size >= len(words):
            break
    return chunks
