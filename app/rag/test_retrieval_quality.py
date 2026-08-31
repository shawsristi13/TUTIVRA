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


def main():

    print()
    print("========== TUTIVRA RETRIEVAL QUALITY TEST ==========")

    vector_store = VectorStore()
    vector_store.load("rag_storage")

    retriever = Retriever(vector_store)

    print(f"\nLoaded documents: {len(vector_store.documents)}")

    for number, question in enumerate(QUESTIONS, start=1):

        print()
        print("=" * 60)
        print(f"QUESTION {number}")
        print(question)
        print("=" * 60)

        results = retriever.retrieve(
            query=question,
            top_k=3,
        )

        for rank, result in enumerate(results, start=1):

            document = result["document"]

            print(
                f"\nRank {rank}"
                f"\nPage: {document['page']}"
                f"\nChunk: {document['chunk_id']}"
                f"\nScore: {result['score']:.4f}"
                f"\nDistance: {result['distance']:.4f}"
            )

            print(
                f"Text: {document['text'][:180]}..."
            )

    print()
    print("=" * 60)
    print("RETRIEVAL QUALITY TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()