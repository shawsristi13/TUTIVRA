import pymupdf


def extract_pages_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text from a PDF while preserving page numbers.
    """

    document = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text()

        if text.strip():
            pages.append(
                {
                    "page": page_number,
                    "text": text.strip(),
                }
            )

    document.close()

    return pages


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Backward-compatible helper that returns all PDF text.
    """

    pages = extract_pages_from_pdf(pdf_path)

    return "\n".join(
        page["text"]
        for page in pages
    )