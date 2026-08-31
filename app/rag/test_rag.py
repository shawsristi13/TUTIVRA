from app.rag.document_loader import extract_text_from_pdf
from app.rag.chunker import chunk_text
from app.rag.vector_store import VectorStore


PDF_PATH = "DSA_Full_Notes_BTech_CSE.pdf"


def main():
    print("\n========== TUTIVRA RAG TEST ==========\n")

    # -----------------------------------
    # 1. Load PDF
    # -----------------------------------

    print("Loading PDF...")

    text = extract_text_from_pdf(PDF_PATH)

    print(f"Extracted characters: {len(text)}")

    # -----------------------------------
    # 2. Chunk text
    # -----------------------------------

    print("\nChunking document...")

    chunks = chunk_text(
        text,
        chunk_size=500,
        overlap=50,
    )

    print(f"Total chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i + 1} ---")
        print(chunk[:500])

    # -----------------------------------
    # 3. Create vector store
    # -----------------------------------

    print("\nCreating vector store...")

    vector_store = VectorStore()

    vector_store.add_documents(chunks)

    print("Documents added to FAISS.")

    # -----------------------------------
    # 4. Test semantic retrieval
    # -----------------------------------

    query = "Why does binary search require a sorted array?"

    print("\n========== RETRIEVAL TEST ==========")

    print(f"\nQuery:\n{query}")

    results = vector_store.search(
        query,
        top_k=3,
    )

    print("\nRelevant chunks:")

    for i, result in enumerate(results):
        print(f"\n--- Result {i + 1} ---")
        print(result[:1000])

    print("\n========== RAG TEST COMPLETE ==========\n")


if __name__ == "__main__":
    main()