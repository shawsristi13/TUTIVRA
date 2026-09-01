import pytest

from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever


QUESTIONS = [
    "Why does binary search require a sorted array?",
    "What is the time complexity of accessing an array element?",
    "How do you reverse a linked list?",
    "What is the difference between a stack and a queue?",
    "What is a binary search tree?",
    "What is BFS?",
    "What is the difference between BFS and DFS?",
    "What is the time complexity of merge sort?",
    "What is backtracking?",
    "What is the recommended DSA study order?",
]


@pytest.fixture
def retriever():
    vector_store = VectorStore()

    vector_store.load(
        "rag_storage"
    )

    return Retriever(
        vector_store
    )


@pytest.mark.integration
def test_retrieval_returns_results(
    retriever,
):

    for question in QUESTIONS:

        results = retriever.retrieve(
            query=question,
            top_k=3,
        )

        assert results
        assert len(results) <= 3

        for result in results:

            assert "document" in result
            assert "score" in result
            assert "distance" in result

            document = result["document"]

            assert "text" in document
            assert "page" in document
            assert "chunk_id" in document

            assert document["text"].strip()


@pytest.mark.integration
def test_retrieval_result_structure(
    retriever,
):

    question = (
        "Why does binary search require "
        "a sorted array?"
    )

    results = retriever.retrieve(
        query=question,
        top_k=3,
    )

    assert results

    first_result = results[0]

    assert isinstance(
        first_result["score"],
        (int, float),
    )

    assert isinstance(
        first_result["distance"],
        (int, float),
    )

    assert isinstance(
        first_result["document"],
        dict,
    )