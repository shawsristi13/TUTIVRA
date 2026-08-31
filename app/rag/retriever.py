import re

from app.rag.vector_store import VectorStore


class Retriever:
    """
    Hybrid retriever for TUTIVRA.

    Uses:
    1. FAISS semantic similarity
    2. Exact topic matching
    3. Keyword overlap
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def _normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _detect_topic(self, query: str) -> str | None:

        topics = {
            "binary search tree": [
                "binary search tree",
                "bst",
            ],

            "binary search": [
                "binary search",
                "sorted array",
                "sorted search space",
            ],

            "linked list": [
                "linked list",
                "reverse a linked list",
            ],

            "stack queue": [
                "stack",
                "queue",
            ],

            "bfs": [
                "bfs",
                "breadth first search",
                "breadth first traversal",
            ],

            "dfs": [
                "dfs",
                "depth first search",
                "depth first traversal",
            ],

            "merge sort": [
                "merge sort",
            ],

            "backtracking": [
                "backtracking",
            ],

            "array access": [
                "array access",
                "accessing an array element",
            ],

            "study order": [
                "study order",
                "recommended progression",
            ],
        }

        # Longest / most specific topics first
        for topic, phrases in topics.items():

            for phrase in phrases:

                if phrase in query:
                    return topic

        return None

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:

        query_text = self._normalize(query)

        # Get all available candidates.
        candidates = self.vector_store.search(
            query=query,
            top_k=len(self.vector_store.documents),
        )

        if not candidates:
            return []

        query_words = set(query_text.split())

        stop_words = {
            "what",
            "is",
            "are",
            "the",
            "a",
            "an",
            "why",
            "does",
            "do",
            "how",
            "and",
            "of",
            "to",
            "in",
            "for",
            "on",
            "can",
            "you",
            "difference",
            "between",
            "require",
        }

        meaningful_words = {
            word
            for word in query_words
            if word not in stop_words
            and len(word) > 2
        }

        query_topic = self._detect_topic(query_text)

        scored = []

        for item in candidates:

            document = item["document"]

            text = self._normalize(
                document.get("text", "")
            )

            distance = item["distance"]

            # -------------------------------------------------
            # 1. Semantic score
            # -------------------------------------------------

            if distance >= 900:
                semantic_score = 0.0
            else:
                # Smaller FAISS distance = better.
                semantic_score = max(
                    0.0,
                    2.0 - distance,
                )

            # -------------------------------------------------
            # 2. Keyword overlap
            # -------------------------------------------------

            document_words = set(text.split())

            keyword_matches = len(
                meaningful_words & document_words
            )

            keyword_score = min(
                keyword_matches * 1.5,
                6.0,
            )

            # -------------------------------------------------
            # 3. Topic score
            # -------------------------------------------------

            topic_score = 0.0

            if query_topic:

                topic_phrases = {
                    "binary search tree": [
                        "binary search tree",
                        "bst",
                    ],

                    "binary search": [
                        "binary search",
                        "sorted array",
                        "sorted search space",
                    ],

                    "linked list": [
                        "linked list",
                        "reverse a linked list",
                    ],

                    "stack queue": [
                        "stack",
                        "queue",
                    ],

                    "bfs": [
                        "bfs",
                        "breadth first search",
                        "breadth first traversal",
                    ],

                    "dfs": [
                        "dfs",
                        "depth first search",
                        "depth first traversal",
                    ],

                    "merge sort": [
                        "merge sort",
                    ],

                    "backtracking": [
                        "backtracking",
                    ],

                    "array access": [
                        "array access",
                    ],

                    "study order": [
                        "study order",
                        "recommended progression",
                    ],
                }

                matched = False

                for phrase in topic_phrases[query_topic]:

                    if phrase in text:
                        matched = True
                        break

                if matched:
                    topic_score = 10.0
                else:
                    topic_score = -3.0

            # -------------------------------------------------
            # 4. Question-specific relevance
            # -------------------------------------------------

            question_score = 0.0

            if query_topic == "binary search":

                if (
                    "binary search" in text
                    and (
                        "sorted" in text
                        or "sorted array" in text
                    )
                ):
                    question_score += 8.0

            elif query_topic == "array access":

                if "array access" in text:
                    question_score += 8.0

            elif query_topic == "linked list":

                if "reverse a linked list" in text:
                    question_score += 8.0

            elif query_topic == "stack queue":

                if (
                    "stack" in text
                    and "queue" in text
                ):
                    question_score += 8.0

            elif query_topic == "binary search tree":

                if "binary search tree" in text:
                    question_score += 8.0

            elif query_topic == "bfs":

                if (
                    "bfs" in text
                    or "breadth first search" in text
                ):
                    question_score += 8.0

            elif query_topic == "dfs":

                if (
                    "dfs" in text
                    or "depth first search" in text
                ):
                    question_score += 8.0

            elif query_topic == "merge sort":

                if "merge sort" in text:
                    question_score += 8.0

            elif query_topic == "backtracking":

                if "backtracking" in text:
                    question_score += 8.0

            elif query_topic == "study order":

                if (
                    "study order" in text
                    or "recommended progression" in text
                ):
                    question_score += 8.0

            # -------------------------------------------------
            # Final score
            # -------------------------------------------------

            final_score = (
                semantic_score
                + keyword_score
                + topic_score
                + question_score
            )

            scored.append(
                {
                    "document": document,
                    "distance": distance,
                    "keyword_matches": keyword_matches,
                    "score": final_score,
                }
            )

        # Highest score first
        scored.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return scored[:top_k]