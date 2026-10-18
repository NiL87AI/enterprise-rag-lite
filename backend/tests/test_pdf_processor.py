import pytest
from app.services.pdf_processor import PDFProcessor


@pytest.fixture
def processor():
    return PDFProcessor(chunk_size=200, chunk_overlap=50)


def test_split_into_chunks_basic(processor):
    text = " ".join(f"parola{i}" for i in range(200))
    chunks = processor.split_into_chunks(text)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c["content"]) <= 200


def test_chunk_metadata_indices(processor):
    text = " ".join("token" for _ in range(150))
    chunks = processor.split_into_chunks(text)
    for i, c in enumerate(chunks):
        assert c["metadata"]["chunk_index"] == i
        assert c["metadata"]["total_chunks"] == len(chunks)


def test_split_empty_text(processor):
    assert processor.split_into_chunks("") == []


def test_short_text_single_chunk(processor):
    chunks = processor.split_into_chunks("Testo breve.")
    assert len(chunks) == 1
    assert chunks[0]["content"] == "Testo breve."
