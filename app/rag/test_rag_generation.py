from app.rag.document_loader import extract_pages_from_pdf
from app.rag.chunker import chunk_pages
from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever
from app.rag.rag_generator import RAGGenerator

PDF_PATH = "DSA_Full_Notes_BTech_CSE.pdf"

def main():

    print()
    print("========== TUTIVRA RAG GENERATION TEST ==========")

# ------------------------------------------------
# 1. Load PDF pages
# ------------------------------------------------

print("\nLoading PDF...")

pages = extract_pages_from_pdf(PDF_PATH)

print(f"Pages extracted: {len(pages)}")

# ------------------------------------------------
# 2. Create page-aware chunks
# ------------------------------------------------

print("\nChunking document...")

chunks = chunk_pages(
    pages,
    source=PDF_PATH,
)

print(f"Total chunks: {len(chunks)}")

# ------------------------------------------------
# 3. Create vector store
# ------------------------------------------------

print("\nCreating vector store...")

vector_store = VectorStore()

vector_store.add_documents(chunks)

print("Documents added to FAISS.")

# ------------------------------------------------
# 4. Create retriever
# ------------------------------------------------

retriever = Retriever(vector_store)

# ------------------------------------------------
# 5. Create RAG generator
# ------------------------------------------------

generator = RAGGenerator(retriever)

# ------------------------------------------------
# 6. Ask question
# ------------------------------------------------

question = "Why does binary search require a sorted array?"

print("\n========== STUDENT QUESTION ==========")
print(question)

# ------------------------------------------------
# 7. Show retrieved sources
# ------------------------------------------------

print("\nRetrieving relevant study material...")

results = retriever.retrieve(
    query=question,
    top_k=3,
)

print("\n========== RETRIEVED SOURCES ==========")

for i, result in enumerate(results, start=1):

    document = result["document"]

    print(
        f"\nResult {i}"
        f"\nPage: {document['page']}"
        f"\nChunk: {document['chunk_id']}"
        f"\nScore: {result['score']:.4f}"
        f"\nDistance: {result['distance']:.4f}"
    )

    print(f"Text: {document['text'][:300]}")

# ------------------------------------------------
# 8. Generate grounded answer
# ------------------------------------------------

print("\nGenerating grounded answer...")

answer = generator.answer(
    question=question,
    top_k=3,
)

print("\n========== TUTIVRA ANSWER ==========")
print(answer)

print("\n======================================")
print("RAG GENERATION TEST COMPLETE")

if __name__ == "__main__":
    main()

