import sys
import os

from app.rag.document_loader import extract_pages_from_pdf
from app.rag.chunker import chunk_pages
from app.rag.vector_store import VectorStore


STORAGE_DIR = "rag_storage"


def ingest_pdf(pdf_path: str):

    print("=" * 50)
    print("TUTIVRA PDF INGESTION")
    print("=" * 50)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    print("\n1. Extracting pages...")

    pages = extract_pages_from_pdf(
        pdf_path
    )

    print(f"   Pages extracted: {len(pages)}")

    print("\n2. Creating chunks...")

    chunks = chunk_pages(
        pages,
        source=os.path.basename(pdf_path),
    )

    print(f"   Chunks created: {len(chunks)}")

    print("\n3. Creating embeddings...")

    vector_store = VectorStore()

    vector_store.add_documents(
        chunks
    )

    print(
        f"   Documents embedded: "
        f"{len(vector_store.documents)}"
    )

    print("\n4. Saving vector store...")

    vector_store.save(
        STORAGE_DIR
    )

    print(
        f"   Saved to: {STORAGE_DIR}"
    )

    print("\n" + "=" * 50)
    print("INGESTION COMPLETE")
    print("=" * 50)


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage:"
            "\npython -m app.rag.ingest_pdf <pdf_path>"
        )

        sys.exit(1)

    ingest_pdf(
        sys.argv[1]
    )