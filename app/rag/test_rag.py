from app.rag.chunker import chunk_pages


def test_chunk_pages():
    pages = [
        {
            "page": 1,
            "text": (
                "Arrays store elements in contiguous memory. "
                "Array indexing provides fast access to elements."
            ),
        },
        {
            "page": 2,
            "text": (
                "Binary search works on sorted data. "
                "It repeatedly divides the search space."
            ),
        },
    ]

    chunks = chunk_pages(
        pages,
        chunk_size=10,
        overlap=2,
        source="test.pdf",
    )

    assert chunks
    assert len(chunks) > 0

    for chunk in chunks:
        assert "chunk_id" in chunk
        assert "text" in chunk
        assert "page" in chunk
        assert "source" in chunk

        assert chunk["text"].strip()
        assert chunk["source"] == "test.pdf"


def test_chunk_pages_preserves_page_numbers():
    pages = [
        {
            "page": 3,
            "text": (
                "Linked lists contain nodes. "
                "Each node stores data and a reference."
            ),
        }
    ]

    chunks = chunk_pages(
        pages,
        chunk_size=5,
        overlap=1,
        source="linked_list.pdf",
    )

    assert chunks

    for chunk in chunks:
        assert chunk["page"] == 3
        assert chunk["source"] == "linked_list.pdf"