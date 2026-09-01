import os
from pathlib import Path

from app.rag.document_loader import extract_pages_from_pdf
from app.rag.chunker import chunk_pages
from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever
from app.rag.rag_generator import RAGGenerator


BASE_DIR = Path(__file__).resolve().parents[2]

RAG_STORAGE_DIR = BASE_DIR / "rag_storage"


def ingest_document(pdf_path: str) -> dict:
    """
    Process a PDF and create/update the TUTIVRA knowledge base.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    # --------------------------------------------------
    # 1. Extract pages
    # --------------------------------------------------

    pages = extract_pages_from_pdf(
        str(pdf_path)
    )

    if not pages:
        raise ValueError(
            "No readable text was found in the PDF."
        )

    # --------------------------------------------------
    # 2. Create chunks
    # --------------------------------------------------

    chunks = chunk_pages(
        pages,
        source=pdf_path.name,
    )

    if not chunks:
        raise ValueError(
            "No usable text chunks were created."
        )

    # --------------------------------------------------
    # 3. Create vector store
    # --------------------------------------------------

    vector_store = VectorStore()

    vector_store.add_documents(
        chunks
    )

    # --------------------------------------------------
    # 4. Save vector store
    # --------------------------------------------------

    vector_store.save(
        str(RAG_STORAGE_DIR)
    )

    return {
        "filename": pdf_path.name,
        "pages": len(pages),
        "chunks": len(chunks),
        "storage": str(RAG_STORAGE_DIR),
    }


def load_knowledge_base() -> Retriever:
    """
    Load the saved TUTIVRA knowledge base.
    """

    index_path = RAG_STORAGE_DIR / "index.faiss"
    documents_path = RAG_STORAGE_DIR / "documents.json"

    if not index_path.exists():
        raise FileNotFoundError(
            "No knowledge base exists yet. "
            "Upload a study PDF first."
        )

    if not documents_path.exists():
        raise FileNotFoundError(
            "Knowledge base metadata is missing."
        )

    vector_store = VectorStore()

    vector_store.load(
        str(RAG_STORAGE_DIR)
    )

    return Retriever(
        vector_store
    )


def ask_from_material(
    question: str,
    top_k: int = 3,
) -> str:
    """
    Answer a question using uploaded study material.
    """

    if not question.strip():
        return "Please enter a question."

    retriever = load_knowledge_base()

    generator = RAGGenerator(
        retriever
    )

    return generator.answer(
        question=question,
        top_k=top_k,
    )