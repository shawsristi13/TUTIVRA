import pytest

from app.rag.document_loader import extract_pages_from_pdf
from app.rag.chunker import chunk_pages
from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever
from app.rag.rag_generator import RAGGenerator


PDF_PATH = "DSA_Full_Notes_BTech_CSE.pdf"


def test_pdf_can_be_loaded():
    pages = extract_pages_from_pdf(PDF_PATH)

    assert pages
    assert len(pages) > 0

    for page in pages:
        assert "page" in page
        assert "text" in page
        assert page["text"].strip()


def test_pdf_can_be_chunked():
    pages = extract_pages_from_pdf(PDF_PATH)

    chunks = chunk_pages(
        pages,
        source=PDF_PATH,
    )

    assert chunks
    assert len(chunks) > 0

    for chunk in chunks:
        assert "chunk_id" in chunk
        assert "text" in chunk
        assert "page" in chunk
        assert "source" in chunk
        assert chunk["text"].strip()


@pytest.mark.integration
def test_rag_generation():
    pages = extract_pages_from_pdf(PDF_PATH)

    assert pages

    chunks = chunk_pages(
        pages,
        source=PDF_PATH,
    )

    assert chunks

    vector_store = VectorStore()

    vector_store.add_documents(chunks)

    assert vector_store.index is not None
    assert len(vector_store.documents) == len(chunks)

    retriever = Retriever(vector_store)

    question = (
        "Why does binary search require a sorted array?"
    )

    results = retriever.retrieve(
        query=question,
        top_k=3,
    )

    assert results
    assert len(results) <= 3

    generator = RAGGenerator(
        retriever
    )

    answer = generator.answer(
        question=question,
        top_k=3,
    )

    assert answer
    assert isinstance(answer, str)
    assert len(answer.strip()) > 20