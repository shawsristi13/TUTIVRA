import re


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 100,
    overlap: int = 20,
    source: str = "unknown",
) -> list[dict]:
    """
    Create smaller, page-aware chunks for semantic retrieval.

    Each chunk contains:
    - chunk_id
    - text
    - page
    - source
    """

    chunks = []
    chunk_id = 0

    for page in pages:

        page_number = page["page"]
        text = page["text"]

        # Clean whitespace
        text = re.sub(r"\r\n?", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        # Split page into paragraphs
        paragraphs = [
            p.strip()
            for p in re.split(r"\n\s*\n", text)
            if p.strip()
        ]

        # If PDF extraction doesn't preserve paragraphs well,
        # fall back to sentence-like blocks.
        if len(paragraphs) <= 1:
            paragraphs = re.split(
                r"(?<=[.!?])\s+",
                text
            )

        words = []

        for paragraph in paragraphs:

            paragraph_words = paragraph.split()

            if not paragraph_words:
                continue

            # Add words from paragraph
            words.extend(paragraph_words)

            # Create chunks whenever enough words accumulate
            while len(words) >= chunk_size:

                chunk_words = words[:chunk_size]

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "text": " ".join(chunk_words),
                        "page": page_number,
                        "source": source,
                    }
                )

                chunk_id += 1

                # Keep overlap
                words = words[
                    chunk_size - overlap:
                ]

        # Save remaining words
        if words:

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": " ".join(words),
                    "page": page_number,
                    "source": source,
                }
            )

            chunk_id += 1

    return chunks