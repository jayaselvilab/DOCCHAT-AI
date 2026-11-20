import pytest

from app.chunker import chunk_text
from app.retriever import Retriever


def test_chunk_sizes_and_overlap():
    text = " ".join(f"w{i}" for i in range(100))
    chunks = chunk_text("a.txt", text, size=40, overlap=10)
    assert [len(c.text.split()) for c in chunks] == [40, 40, 40]
    # last 10 words of chunk 0 are the first 10 words of chunk 1
    assert chunks[0].text.split()[-10:] == chunks[1].text.split()[:10]
    assert [c.index for c in chunks] == [0, 1, 2]


def test_chunk_short_text_is_single_chunk():
    chunks = chunk_text("a.txt", "just a few words", size=40, overlap=10)
    assert len(chunks) == 1


def test_chunk_empty_text():
    assert chunk_text("a.txt", "   ") == []


def test_chunk_rejects_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("a.txt", "x y z", size=5, overlap=5)


def test_retriever_ranks_relevant_chunk_first():
    chunks = (
        chunk_text("leave.txt", "Annual leave is 18 days per year and sick leave is 12 days.")
        + chunk_text("remote.txt", "Remote work needs a VPN and an encrypted laptop at all times.")
    )
    retriever = Retriever()
    retriever.build(chunks)
    hits = retriever.search("how many days of annual leave", top_k=2, min_score=0.0)
    assert hits[0].chunk.source == "leave.txt"
    assert hits[0].score > hits[1].score


def test_retriever_ignores_unrelated_question():
    retriever = Retriever()
    retriever.build(chunk_text("leave.txt", "Annual leave is 18 days per year."))
    assert retriever.search("quantum chromodynamics", min_score=0.05) == []


def test_retriever_empty_index():
    assert Retriever().search("anything") == []
