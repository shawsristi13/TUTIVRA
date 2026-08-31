from app.ai.openrouter_client import ask_ai
from app.rag.retriever import Retriever


class RAGGenerator:
    """
    Generates answers grounded in the student's study material.
    """

    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    def answer(
        self,
        question: str,
        top_k: int = 3,
    ) -> str:

        relevant_chunks = self.retriever.retrieve(
            query=question,
            top_k=top_k,
        )

        if not relevant_chunks:
            return (
                "I could not find relevant information "
                "in your uploaded study material."
            )

        context_parts = []

        for i, result in enumerate(relevant_chunks, start=1):

            document = result["document"]

            context_parts.append(
                f"""
[Study Material {i}]
Source: {document["source"]}
Page: {document["page"]}

{document["text"]}
"""
            )

        context = "\n".join(context_parts)

        prompt = f"""
You are Tutivra, an adaptive AI learning tutor.

Answer the student's question using the provided study material.

IMPORTANT RULES:

1. Use the study material as the primary source.
2. Do not invent facts that are not supported by the study material.
3. Explain the answer clearly and educationally.
4. You may reorganize or simplify the material to make it easier
   for a student to understand.
5. If the material does not contain enough information to answer
   the question, clearly say that the uploaded material does not
   provide enough information.
6. Do not mention FAISS, embeddings, vector databases, retrieval,
   RAG, or internal implementation details.
7. At the end, provide the source page(s) used.

STUDY MATERIAL:

{context}

STUDENT QUESTION:

{question}

Give a clear, accurate educational answer.
"""

        answer = ask_ai(prompt)

        return answer