import json
import os

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class VectorStore:
    """
    Persistent FAISS vector store using OpenRouter embeddings.
    Stores chunk text together with metadata.
    """

    def __init__(
        self,
        model: str = "openai/text-embedding-3-small",
    ):
        self.model = model

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is missing. "
                "Check your .env file."
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        self.index = None
        self.documents = []

    def embed(self, texts: list[str]) -> np.ndarray:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        embeddings = [
            item.embedding
            for item in response.data
        ]

        return np.array(
            embeddings,
            dtype="float32",
        )

    def add_documents(self, documents: list[dict]):
        """
        Add metadata-aware document chunks.

        Each document should contain:
        - chunk_id
        - text
        - page
        - source
        """

        if not documents:
            return

        texts = [
            document["text"]
            for document in documents
        ]

        embeddings = self.embed(texts)

        dimension = embeddings.shape[1]

        if self.index is None:
            self.index = faiss.IndexFlatL2(dimension)

        self.index.add(embeddings)

        self.documents.extend(documents)

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Retrieve relevant chunks with metadata.
        """

        if self.index is None or not self.documents:
            return []

        query_embedding = self.embed([query])

        distances, indices = self.index.search(
            query_embedding,
            min(top_k, len(self.documents)),
        )

        results = []

        for distance, index in zip(distances[0], indices[0]):
            if index != -1:
                results.append(
                    {
                        "document": self.documents[index],
                        "distance": float(distance),
                    }
                )

        return results

    def save(self, directory: str):
        """
        Save FAISS index and metadata.
        """

        if self.index is None:
            raise ValueError(
                "Cannot save an empty vector store."
            )

        os.makedirs(
            directory,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            os.path.join(
                directory,
                "index.faiss",
            ),
        )

        with open(
            os.path.join(
                directory,
                "documents.json",
            ),
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.documents,
                file,
                ensure_ascii=False,
                indent=2,
            )

    def load(self, directory: str):
        """
        Load FAISS index and metadata.
        """

        index_path = os.path.join(
            directory,
            "index.faiss",
        )

        documents_path = os.path.join(
            directory,
            "documents.json",
        )

        if not os.path.exists(index_path):
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}"
            )

        if not os.path.exists(documents_path):
            raise FileNotFoundError(
                f"Documents file not found: {documents_path}"
            )

        self.index = faiss.read_index(
            index_path
        )

        with open(
            documents_path,
            "r",
            encoding="utf-8",
        ) as file:

            self.documents = json.load(file)