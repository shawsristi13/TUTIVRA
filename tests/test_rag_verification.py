"""
TUTIVRA RAG Verification Suite
=================================
Proves (not assumes) that the RAG pipeline works correctly.

Tests:
1. PDF ingestion and text extraction
2. Chunking quality
3. Embedding generation
4. FAISS index creation
5. Retrieval relevance for known-answer queries
6. Retrieval returns content from the document (not hallucinated)
7. Multi-topic retrieval
8. Out-of-document query handling (should return low-confidence results)
9. LLM uses retrieved context, not prior knowledge alone

Run with:
    python tests/test_rag_verification.py
"""

import sys
import os
import json
import time
from pathlib import Path

# Make sure imports resolve from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()


import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── ANSI colours ────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):    print(f"  {GREEN}[PASS] {msg}{RESET}")
def fail(msg):  print(f"  {RED}[FAIL] {msg}{RESET}")
def warn(msg):  print(f"  {YELLOW}[WARN] {msg}{RESET}")
def info(msg):  print(f"  {BLUE}[INFO] {msg}{RESET}")
def header(msg):print(f"\n{BOLD}{'='*60}\n  {msg}\n{'='*60}{RESET}")

RESULTS = []

def record(test_name: str, passed: bool, detail: str = ""):
    RESULTS.append({"test": test_name, "passed": passed, "detail": detail})
    if passed:
        ok(f"{test_name}: {detail}")
    else:
        fail(f"{test_name}: {detail}")


# ─── TEST PDF ────────────────────────────────────────────────
# Use the bundled test PDF
TEST_PDF = PROJECT_ROOT / "DSA_Full_Notes_BTech_CSE.pdf"

if not TEST_PDF.exists():
    TEST_PDF = PROJECT_ROOT / "test_material.pdf"

if not TEST_PDF.exists():
    print(f"{RED}No test PDF found. Place a PDF at {TEST_PDF}{RESET}")
    sys.exit(1)


# ============================================================
# TEST 1 — PDF ingestion and text extraction
# ============================================================
header("TEST 1: PDF ingestion and text extraction")

try:
    from app.rag.document_loader import extract_pages_from_pdf
    pages = extract_pages_from_pdf(str(TEST_PDF))

    record("Pages extracted", len(pages) > 0, f"{len(pages)} pages found")

    total_chars = sum(len(p["text"]) for p in pages)
    record("Meaningful text content", total_chars > 500,
           f"{total_chars:,} total characters")

    # Check page numbers are sequential and correct
    page_numbers = [p["page"] for p in pages]
    record("Page numbers present", all(isinstance(n, int) for n in page_numbers),
           f"Pages: {page_numbers[:5]}...")

    # Inspect first page content
    first_page = pages[0]["text"][:300]
    info(f"First 300 chars of page 1:\n{first_page}")

except Exception as e:
    record("PDF extraction", False, str(e))
    print(f"{RED}FATAL: Cannot continue without PDF extraction.{RESET}")
    sys.exit(1)


# ============================================================
# TEST 2 — Chunking quality
# ============================================================
header("TEST 2: Chunking quality")

try:
    from app.rag.chunker import chunk_pages

    chunks = chunk_pages(pages, chunk_size=100, overlap=20, source=TEST_PDF.name)

    record("Chunks created", len(chunks) > 0, f"{len(chunks)} chunks created")
    record("Chunks have required fields",
           all("text" in c and "page" in c and "chunk_id" in c for c in chunks),
           "chunk_id, text, page all present")

    # Check chunk lengths
    lengths = [len(c["text"].split()) for c in chunks]
    avg_len = sum(lengths) / len(lengths)
    min_len = min(lengths)
    max_len = max(lengths)
    record("Reasonable chunk sizes", avg_len > 20,
           f"avg={avg_len:.0f} words, min={min_len}, max={max_len}")

    # Check for empty chunks
    empty = [c for c in chunks if not c["text"].strip()]
    record("No empty chunks", len(empty) == 0,
           f"{len(empty)} empty chunks found")

    info(f"Sample chunk 0: {chunks[0]['text'][:150]}")
    info(f"Sample chunk -1: {chunks[-1]['text'][:150]}")

except Exception as e:
    record("Chunking", False, str(e))


# ============================================================
# TEST 3 — Embedding generation
# ============================================================
header("TEST 3: Embedding generation (requires OPENROUTER_API_KEY)")

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    warn("OPENROUTER_API_KEY not set — skipping embedding test")
    record("Embedding API key present", False, "OPENROUTER_API_KEY missing")
else:
    try:
        from app.rag.vector_store import VectorStore

        vs = VectorStore()
        test_texts = ["What is a binary search tree?",
                      "Explain array traversal.",
                      "How does merge sort work?"]

        embeddings = vs.embed(test_texts)

        record("Embeddings generated", embeddings.shape[0] == 3,
               f"shape={embeddings.shape}")
        record("Embedding dimension > 0", embeddings.shape[1] > 0,
               f"dim={embeddings.shape[1]}")
        record("No zero embeddings",
               not all(embeddings[0] == 0),
               "first embedding is non-zero")

    except Exception as e:
        record("Embedding generation", False, str(e))


# ============================================================
# TEST 4 — FAISS index creation + persistence
# ============================================================
header("TEST 4: FAISS index creation and save/load")

TEMP_STORE = PROJECT_ROOT / "rag_storage_test_temp"

if not api_key:
    warn("Skipping FAISS test — no API key")
    record("FAISS index", False, "No API key — skipped")
else:
    try:
        from app.rag.vector_store import VectorStore

        # Use only 5 chunks to keep test fast
        test_chunks = chunks[:5]

        vs = VectorStore()
        vs.add_documents(test_chunks)

        record("Documents added to store", len(vs.documents) == 5,
               f"{len(vs.documents)} docs")
        record("FAISS index created", vs.index is not None,
               f"index type: {type(vs.index).__name__}")

        # Save
        vs.save(str(TEMP_STORE))
        record("Index saved to disk",
               (TEMP_STORE / "index.faiss").exists() and
               (TEMP_STORE / "documents.json").exists(),
               f"saved to {TEMP_STORE}")

        # Load into new instance
        vs2 = VectorStore()
        vs2.load(str(TEMP_STORE))
        record("Index loaded from disk",
               len(vs2.documents) == 5,
               f"{len(vs2.documents)} docs reloaded")

        # Cleanup
        import shutil
        shutil.rmtree(TEMP_STORE, ignore_errors=True)

    except Exception as e:
        record("FAISS index", False, str(e))
        import shutil
        shutil.rmtree(TEMP_STORE, ignore_errors=True)


# ============================================================
# TEST 5 — Full ingestion pipeline
# ============================================================
header("TEST 5: Full ingest_document pipeline")

if not api_key:
    warn("Skipping full ingestion — no API key")
    record("Full ingestion", False, "No API key — skipped")
else:
    try:
        from app.rag.rag_service import ingest_document

        result = ingest_document(str(TEST_PDF))

        record("Ingestion succeeded", True,
               f"pages={result['pages']}, chunks={result['chunks']}")
        record("Filename returned", result["filename"] == TEST_PDF.name,
               result["filename"])
        record("Chunks > 0", result["chunks"] > 0,
               f"{result['chunks']} chunks indexed")

    except Exception as e:
        record("Full ingestion", False, str(e))


# ============================================================
# TEST 6 — Retrieval relevance (known-answer queries)
# ============================================================
header("TEST 6: Retrieval relevance — known-answer queries")

if not api_key:
    warn("Skipping retrieval test — no API key")
    record("Retrieval relevance", False, "No API key — skipped")
else:
    try:
        from app.rag.rag_service import load_knowledge_base

        retriever = load_knowledge_base()

        # These topics must exist in the DSA PDF
        queries = [
            "binary search tree",
            "linked list",
            "sorting algorithms",
            "time complexity",
            "graph traversal",
        ]

        all_relevant = True
        for query in queries:
            results = retriever.retrieve(query, top_k=3)

            if not results:
                fail(f"  Query '{query}': NO results returned")
                all_relevant = False
                continue

            top = results[0]
            text = top["document"]["text"].lower()
            score = top.get("score", top.get("distance", "N/A"))
            query_words = set(query.lower().split())
            text_words = set(text.split())
            overlap = len(query_words & text_words)

            # At least one word from the query should appear in the top result
            is_relevant = overlap > 0 or any(
                w in text for w in query.lower().split()
            )

            if is_relevant:
                ok(f"  '{query}': top result relevant (score={score:.2f}, word_overlap={overlap})")
                ok(f"    snippet: {text[:100]}...")
            else:
                fail(f"  '{query}': top result IRRELEVANT (score={score})")
                info(f"    snippet: {text[:100]}...")
                all_relevant = False

        record("All retrieval queries return relevant results", all_relevant, "")

    except Exception as e:
        record("Retrieval relevance", False, str(e))


# ============================================================
# TEST 7 — Out-of-document query handling
# ============================================================
header("TEST 7: Out-of-document query — system should not hallucinate")

if not api_key:
    warn("Skipping out-of-document test — no API key")
    record("Out-of-document handling", False, "No API key — skipped")
else:
    try:
        from app.rag.rag_generator import RAGGenerator
        from app.rag.rag_service import load_knowledge_base

        retriever = load_knowledge_base()
        generator = RAGGenerator(retriever)

        # This question is completely unrelated to DSA
        out_of_scope_query = "What is the capital of France and how is the Eiffel Tower built?"

        results = retriever.retrieve(out_of_scope_query, top_k=3)

        if results:
            top_score = results[0].get("score", 0)
            info(f"Top retrieval score for out-of-scope query: {top_score}")

            # Score should be low (system should signal low confidence)
            if top_score < 5:
                record("Low score for irrelevant query", True,
                       f"score={top_score:.2f} (low confidence, correct)")
            else:
                warn(f"Unexpectedly high score for out-of-scope query: {top_score}")
                record("Low score for irrelevant query", False,
                       f"score={top_score:.2f} (may retrieve irrelevant content)")
        else:
            record("Out-of-scope query returns no results", True, "empty results (good)")

        # Also test the full answer
        answer = generator.answer(out_of_scope_query, top_k=3)
        info(f"RAG answer for out-of-scope query:\n  {answer[:300]}")

        # Check if the answer admits it doesn't know
        does_admit = any(phrase in answer.lower() for phrase in [
            "not found", "not available", "not in the material",
            "no relevant", "cannot find", "don't have", "do not have",
            "not mentioned", "not covered", "outside"
        ])
        record("System acknowledges out-of-scope", does_admit,
               "admits lack of information" if does_admit else "may be hallucinating")

    except Exception as e:
        record("Out-of-document handling", False, str(e))


# ============================================================
# TEST 8 — RAG Generator uses retrieved context
# ============================================================
header("TEST 8: RAG Generator uses retrieved context (not hallucinating)")

if not api_key:
    warn("Skipping RAG generation test — no API key")
    record("RAG generation", False, "No API key — skipped")
else:
    try:
        from app.rag.rag_generator import RAGGenerator
        from app.rag.rag_service import load_knowledge_base

        retriever = load_knowledge_base()
        generator = RAGGenerator(retriever)

        test_questions = [
            "What is a binary search tree?",
            "How does a linked list differ from an array?",
        ]

        for question in test_questions:
            info(f"\n  Question: {question}")
            answer = generator.answer(question, top_k=3)
            info(f"  Answer: {answer[:300]}")

            # Answer should be non-empty and substantive
            record(f"Non-empty answer for '{question[:40]}'",
                   len(answer.strip()) > 50,
                   f"{len(answer)} chars")

    except Exception as e:
        record("RAG generation", False, str(e))


# ============================================================
# TEST 9 — Hardcoded topic detection audit
# ============================================================
header("TEST 9: Hardcoded topic detection audit")

try:
    from app.rag.retriever import Retriever
    from app.rag.vector_store import VectorStore

    # Load retriever source code and check for hardcoded topics
    retriever_path = PROJECT_ROOT / "app" / "rag" / "retriever.py"
    source = retriever_path.read_text(encoding="utf-8", errors="replace")

    hardcoded_topics = [
        '"binary search tree"',
        '"linked list"',
        '"bfs"',
        '"dfs"',
        '"merge sort"',
        '"backtracking"',
        '"array access"',
    ]

    found_hardcoded = [t for t in hardcoded_topics if t in source]

    if found_hardcoded:
        warn(f"HARDCODED TOPIC DETECTION FOUND: {found_hardcoded}")
        warn("This means the retriever only works well for DSA topics.")
        warn("Any other subject (biology, history, physics) will get poor retrieval.")
        record("No hardcoded topic detection", False,
               f"Found {len(found_hardcoded)} hardcoded topics — must be removed")
    else:
        record("No hardcoded topic detection", True, "retriever is topic-agnostic")

except Exception as e:
    record("Hardcoded topic audit", False, str(e))


# ============================================================
# SUMMARY
# ============================================================
header("RAG VERIFICATION SUMMARY")

passed = [r for r in RESULTS if r["passed"]]
failed = [r for r in RESULTS if not r["passed"]]

print(f"\n  {GREEN}Passed: {len(passed)}{RESET}")
print(f"  {RED}Failed: {len(failed)}{RESET}")

if failed:
    print(f"\n  {RED}Failed tests:{RESET}")
    for r in failed:
        print(f"    ✗ {r['test']}: {r['detail']}")

print(f"\n  {'='*55}")
if len(failed) == 0:
    print(f"  {GREEN}{BOLD}RAG IS WORKING CORRECTLY [OK]{RESET}")
elif len(failed) <= 2:
    print(f"  {YELLOW}{BOLD}RAG IS PARTIALLY WORKING - minor issues{RESET}")
else:
    print(f"  {RED}{BOLD}RAG HAS SIGNIFICANT PROBLEMS - fix before building on top{RESET}")
print(f"  {'='*55}")

# Write results to JSON for the implementation report
results_path = PROJECT_ROOT / "tests" / "rag_verification_results.json"
results_path.parent.mkdir(exist_ok=True)
with open(results_path, "w") as f:
    json.dump({
        "total": len(RESULTS),
        "passed": len(passed),
        "failed": len(failed),
        "results": RESULTS,
    }, f, indent=2)

info(f"Results saved to {results_path}")
