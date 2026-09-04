"""
TUTIVRA — Semantic Retriever (topic-agnostic)

BUGS FIXED vs original:
- Removed ALL hardcoded topic detection (was DSA-only, broken for any other subject)
- Removed hardcoded topic_phrases and question_score DSA overrides
- Scoring now uses pure semantic + keyword overlap, working for ANY subject
- Added confidence score normalisation so out-of-scope queries return low scores
- Added minimum score threshold to filter truly irrelevant results
"""

import re


class Retriever:
    """
    Topic-agnostic semantic retriever.

    Scoring: semantic distance from FAISS + keyword overlap bonus.
    No hardcoded domain logic — works for any subject.
    """

    # Minimum combined score to include a result.
    # Results below this are considered too irrelevant to return.
    MIN_RELEVANCE_SCORE = 0.5

    def __init__(self, vector_store):
        self.vector_store = vector_store

    # --------------------------------------------------
    # NORMALISE
    # --------------------------------------------------

    def _normalize(self, text: str) -> str:
        """Lowercase + collapse whitespace."""
        return re.sub(r"\s+", " ", text.lower()).strip()

    # --------------------------------------------------
    # STOP WORDS
    # --------------------------------------------------

    STOP_WORDS = {
        "what", "is", "are", "the", "a", "an", "why",
        "does", "do", "how", "and", "of", "to", "in",
        "for", "on", "can", "you", "difference", "between",
        "require", "with", "that", "this", "which", "from",
        "has", "have", "was", "were", "will", "be", "been",
        "it", "its", "at", "by", "up", "or", "but", "not",
        "so", "if", "as", "into", "through", "during",
        "before", "after", "above", "below", "he", "she",
        "they", "we", "me", "him", "her", "them", "us",
        "my", "your", "his", "our", "their", "who", "whom",
    }

    def _meaningful_words(self, text: str) -> set[str]:
        """Extract meaningful (non-stop) words longer than 2 chars."""
        words = self._normalize(text).split()
        return {
            w for w in words
            if w not in self.STOP_WORDS and len(w) > 2
        }

    # --------------------------------------------------
    # RETRIEVE
    # --------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Retrieve the top-k most relevant chunks for a query.

        Returns list of dicts:
          {document, distance, keyword_matches, score}
        """

        if not query.strip():
            return []

        if not self.vector_store.documents:
            return []

        # Fetch all candidates so we can re-rank.
        n_candidates = len(self.vector_store.documents)
        candidates = self.vector_store.search(
            query=query,
            top_k=n_candidates,
        )

        if not candidates:
            return []

        query_words = self._meaningful_words(query)

        scored = []

        for item in candidates:
            document = item["document"]
            text = self._normalize(document.get("text", ""))
            distance = item["distance"]

            # -------------------------------------------------
            # 1. Semantic score from FAISS L2 distance
            #    For text-embedding-3-small, typical distances:
            #    < 0.5  = very similar
            #    0.5–1  = related
            #    1–2    = loosely related
            #    > 2    = likely different topic
            # -------------------------------------------------

            if distance <= 0:
                semantic_score = 4.0
            elif distance < 0.5:
                semantic_score = 3.5
            elif distance < 1.0:
                semantic_score = 2.5
            elif distance < 1.5:
                semantic_score = 1.5
            elif distance < 2.0:
                semantic_score = 0.8
            else:
                # Exponential decay for large distances
                semantic_score = max(0.0, 2.0 - distance)

            # -------------------------------------------------
            # 2. Keyword overlap bonus (topic-agnostic)
            #    Rewards chunks that share meaningful words
            #    with the query.
            # -------------------------------------------------

            doc_words = self._meaningful_words(text)
            keyword_matches = len(query_words & doc_words)

            # Scale: each match = +0.4, capped at 4.0
            keyword_score = min(keyword_matches * 0.4, 4.0)

            # -------------------------------------------------
            # 3. Phrase match bonus
            #    If the full query (normalised, stopwords kept)
            #    appears verbatim in the chunk, give a bonus.
            # -------------------------------------------------

            norm_query = self._normalize(query)
            phrase_score = 2.0 if norm_query in text else 0.0

            # -------------------------------------------------
            # 4. Final combined score
            # -------------------------------------------------

            final_score = semantic_score + keyword_score + phrase_score

            scored.append(
                {
                    "document": document,
                    "distance": distance,
                    "keyword_matches": keyword_matches,
                    "score": final_score,
                }
            )

        # Sort highest score first.
        scored.sort(key=lambda x: x["score"], reverse=True)

        # Filter results below minimum relevance threshold.
        relevant = [
            r for r in scored
            if r["score"] >= self.MIN_RELEVANCE_SCORE
        ]

        return relevant[:top_k]