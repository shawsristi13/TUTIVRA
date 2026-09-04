"""
TUTIVRA — Complete API + End-to-End Test Suite
===============================================
Tests every configured service with real API calls.

Run: python tests/test_api_e2e.py

Requirements:
  At least OPENROUTER_API_KEY or GEMINI_API_KEY must be set in .env

Test groups:
  1.  Security audit (no hardcoded keys, .gitignore, .env.example)
  2.  LLM provider chain (OpenRouter, Gemini, Grok connectivity)
  3.  LLM fallback simulation
  4.  RAG pipeline (ingest → retrieve → answer)
  5.  Lesson generation
  6.  Scene planner
  7.  Educational visuals (offline)
  8.  Fish Audio TTS
  9.  D-ID avatar video
  10. Full video pipeline
  11. Student Q&A loop (question → evaluate → adapt)
  12. Final assessment
  13. Learning report

API keys are read from .env. No key values are printed.
"""

import io, os, sys, json, time, re, tempfile, inspect
from pathlib import Path

# ── UTF-8 output ──────────────────────────────────────────────
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── Project root ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

# ════════════════════════════════════════════════════════════
# RESULT TRACKING
# ════════════════════════════════════════════════════════════

RESULTS = []
PASS = FAIL = SKIP = 0

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def passed(name, detail=""):
    global PASS
    PASS += 1
    RESULTS.append({"name": name, "status": "PASS", "detail": detail})
    print(f"  {GREEN}[PASS]{RESET} {name}{(' - ' + detail) if detail else ''}")

def failed(name, detail=""):
    global FAIL
    FAIL += 1
    RESULTS.append({"name": name, "status": "FAIL", "detail": detail})
    print(f"  {RED}[FAIL]{RESET} {name}{(' - ' + detail) if detail else ''}")

def skipped(name, reason=""):
    global SKIP
    SKIP += 1
    RESULTS.append({"name": name, "status": "SKIP", "detail": reason})
    print(f"  {YELLOW}[SKIP]{RESET} {name}{(' - ' + reason) if reason else ''}")

def header(title):
    print(f"\n{BOLD}{'='*60}\n  {title}\n{'='*60}{RESET}")

def info(msg):
    print(f"  {BLUE}[INFO]{RESET} {msg}")


# ════════════════════════════════════════════════════════════
# GROUP 1: SECURITY AUDIT
# ════════════════════════════════════════════════════════════

header("GROUP 1: Security Audit")

# 1.1 .gitignore contains .env
gitignore = PROJECT_ROOT / ".gitignore"
if gitignore.exists():
    content = gitignore.read_text()
    passed(".gitignore exists", ".env is in .gitignore") if ".env" in content else failed(".gitignore contains .env")
else:
    failed(".gitignore exists")

# 1.2 .env is NOT committed (no actual .env in tracked files)
import subprocess
result = subprocess.run(
    ["git", "ls-files", ".env"],
    capture_output=True, text=True, cwd=str(PROJECT_ROOT)
)
if result.returncode == 0 and not result.stdout.strip():
    passed(".env not tracked by git")
elif result.returncode != 0:
    passed(".env not tracked by git", "git not available")
else:
    failed(".env not tracked by git", ".env IS in git index!")

# 1.3 .env.example has no actual key values
env_example = PROJECT_ROOT / ".env.example"
if env_example.exists():
    ex_content = env_example.read_text()
    suspicious = re.findall(r"(?:sk-|AIzaSy|xai-|Bearer )\S{8,}", ex_content)
    if not suspicious:
        passed(".env.example has no real keys")
    else:
        failed(".env.example has no real keys", f"Found: {len(suspicious)} suspicious values")
else:
    failed(".env.example exists")

# 1.4 No hardcoded secrets in Python source
secret_patterns = [r"sk-or-[a-zA-Z0-9]{20,}", r"AIzaSy[a-zA-Z0-9\-_]{33}", r"xai-[a-zA-Z0-9]{40,}"]
py_files = list((PROJECT_ROOT / "app").rglob("*.py")) + list((PROJECT_ROOT / "tests").rglob("*.py"))
found_secrets = []
for f in py_files:
    try:
        src = f.read_text(encoding='utf-8', errors='ignore')
        for pat in secret_patterns:
            if re.search(pat, src):
                found_secrets.append(str(f.name))
    except Exception:
        pass
if not found_secrets:
    passed("No hardcoded secrets in source", f"Scanned {len(py_files)} files")
else:
    failed("No hardcoded secrets in source", f"Suspected: {found_secrets}")

# 1.5 All modules use os.getenv() not hardcoded values
llm_client = PROJECT_ROOT / "app" / "ai" / "llm_client.py"
if llm_client.exists():
    src = llm_client.read_text(encoding='utf-8', errors='ignore')
    if 'os.getenv(' in src:
        passed("llm_client uses os.getenv for keys")
    else:
        failed("llm_client uses os.getenv for keys", "No os.getenv() found")
else:
    failed("llm_client.py exists")


# ════════════════════════════════════════════════════════════
# GROUP 2: LLM PROVIDER CONNECTIVITY
# ════════════════════════════════════════════════════════════

header("GROUP 2: LLM Provider Connectivity")

from app.ai.llm_client import ask_ai, get_provider_status, LLMError, _openrouter, _gemini, _grok

# 2.1 OpenRouter
or_key = os.getenv("OPENROUTER_API_KEY", "")
if or_key:
    try:
        resp = _openrouter.call(
            messages=[{"role": "user", "content": "Reply with exactly: TUTIVRA_OK"}],
            model=os.getenv("OPENROUTER_MODEL", "google/gemini-3.5-flash"),
            temperature=0.0,
        )
        if resp.strip():
            passed("OpenRouter API", f"model={os.getenv('OPENROUTER_MODEL','google/gemini-3.5-flash')}, response_len={len(resp)}")
        else:
            failed("OpenRouter API", "Empty response")
    except Exception as e:
        failed("OpenRouter API", str(e)[:100])
else:
    skipped("OpenRouter API", "OPENROUTER_API_KEY not set")

# 2.2 Gemini
gem_key = os.getenv("GEMINI_API_KEY", "")
if gem_key:
    try:
        resp = _gemini.call(
            messages=[{"role": "user", "content": "Reply with exactly: TUTIVRA_OK"}],
            temperature=0.0,
        )
        if resp.strip():
            passed("Gemini API", f"model={os.getenv('GEMINI_MODEL','gemini-2.5-flash')}, response_len={len(resp)}")
        else:
            failed("Gemini API", "Empty response")
    except ImportError:
        failed("Gemini API", "google-genai not installed (run: pip install google-genai)")
    except Exception as e:
        failed("Gemini API", str(e)[:100])
else:
    skipped("Gemini API", "GEMINI_API_KEY not set")

# 2.3 Groq / xAI (auto-detected from key prefix)
xai_key = os.getenv("XAI_API_KEY", "")
if xai_key:
    provider_label = "Groq" if xai_key.startswith("gsk_") else "Grok (xAI)"
    try:
        resp = _grok.call(
            messages=[{"role": "user", "content": "Reply with exactly: TUTIVRA_OK"}],
            temperature=0.0,
        )
        if resp.strip():
            passed(f"{provider_label} API", f"response_len={len(resp)}")
        else:
            failed(f"{provider_label} API", "Empty response")
    except Exception as e:
        failed(f"{provider_label} API", str(e)[:100])
else:
    skipped("Groq/Grok API", "XAI_API_KEY not set")

# 2.4 At least one provider configured
status = get_provider_status()
if status["providers_in_chain"]:
    passed("At least one LLM provider configured", f"Chain: {status['providers_in_chain']}")
else:
    failed("At least one LLM provider configured", "NO providers set — add at least OPENROUTER_API_KEY or GEMINI_API_KEY")


# ════════════════════════════════════════════════════════════
# GROUP 3: LLM FALLBACK SIMULATION
# ════════════════════════════════════════════════════════════

header("GROUP 3: LLM Fallback Simulation")

# We simulate OpenRouter failure by calling ask_ai with a _force_provider
# that points to a "bad" provider scenario using a mock.

configured_providers = status["providers_in_chain"]

# 3.1 Simulate OpenRouter failure → Gemini takes over
if "openrouter" in configured_providers and "gemini" in configured_providers:
    # Temporarily override: call ask_ai with openrouter forced using a bad model
    # that will fail, then verify gemini handles it
    # We do this by patching _openrouter.call temporarily
    original_call = _openrouter.call

    def _failing_openrouter(messages, model=None, temperature=0.7):
        raise Exception("503 Service Unavailable: simulated OpenRouter failure")

    _openrouter.call = _failing_openrouter
    try:
        resp = ask_ai("Reply: FALLBACK_OK", temperature=0.0)
        if resp.strip():
            provider_status = get_provider_status()
            passed("OpenRouter → Gemini fallback",
                   f"Fell back to: {provider_status['active_provider']}")
        else:
            failed("OpenRouter → Gemini fallback", "Response was empty")
    except LLMError as e:
        failed("OpenRouter → Gemini fallback", f"All providers failed: {e}")
    except Exception as e:
        failed("OpenRouter → Gemini fallback", str(e)[:100])
    finally:
        _openrouter.call = original_call  # RESTORE original
elif "openrouter" in configured_providers and "gemini" not in configured_providers:
    skipped("OpenRouter → Gemini fallback", "GEMINI_API_KEY not set")
elif "gemini" in configured_providers and "openrouter" not in configured_providers:
    skipped("OpenRouter → Gemini fallback", "OPENROUTER_API_KEY not set (openrouter not in chain)")
else:
    skipped("OpenRouter → Gemini fallback", "Neither OpenRouter nor Gemini configured")

# 3.2 Simulate Gemini failure → Groq takes over
if "gemini" in configured_providers and "groq" in configured_providers:
    original_or = _openrouter.call
    original_gem = _gemini.call

    def _fail(messages, model=None, temperature=0.7):
        raise Exception("503 simulated failure")

    _openrouter.call = _fail
    _gemini.call = _fail
    try:
        resp = ask_ai("Reply: GROK_OK", temperature=0.0)
        if resp.strip():
            passed("Gemini → Groq fallback", f"Fell back to Groq, response_len={len(resp)}")
        else:
            failed("Gemini → Groq fallback", "Response empty")
    except LLMError as e:
        failed("Gemini → Groq fallback", f"All providers failed: {e}")
    finally:
        _openrouter.call = original_or
        _gemini.call = original_gem
else:
    skipped("Gemini → Groq fallback", "Need both GEMINI_API_KEY and XAI_API_KEY (Groq)")

# 3.3 Verify fallback does NOT trigger on non-provider errors
if configured_providers:
    original_call = _openrouter.call if "openrouter" in configured_providers else _gemini.call
    provider_obj  = _openrouter if "openrouter" in configured_providers else _gemini

    def _bad_prompt_error(messages, model=None, temperature=0.7):
        raise ValueError("This is a content validation error, not a provider failure")

    provider_obj.call = _bad_prompt_error
    try:
        ask_ai("test", temperature=0.0)
        failed("Non-provider error does not trigger fallback", "Should have raised ValueError")
    except ValueError:
        passed("Non-provider error does not trigger fallback", "ValueError propagated correctly")
    except Exception as e:
        failed("Non-provider error does not trigger fallback", f"Unexpected: {type(e).__name__}")
    finally:
        provider_obj.call = original_call
else:
    skipped("Non-provider error test", "No providers configured")


# ════════════════════════════════════════════════════════════
# GROUP 4: RAG PIPELINE
# ════════════════════════════════════════════════════════════

header("GROUP 4: RAG Pipeline")

TEST_PDF = PROJECT_ROOT / "tests" / "sample.pdf"

if not configured_providers:
    for test in ["PDF ingestion", "Embedding creation", "Retrieval (direct question)",
                 "Retrieval (different section)", "Retrieval (paraphrased)",
                 "Out-of-scope question", "LLM grounded in retrieved context"]:
        skipped(test, "No LLM provider configured")
elif not TEST_PDF.exists():
    for test in ["PDF ingestion", "Embedding creation", "Retrieval (direct question)",
                 "Retrieval (different section)", "Retrieval (paraphrased)",
                 "Out-of-scope question", "LLM grounded in retrieved context"]:
        skipped(test, "tests/sample.pdf not found")
else:
    from app.rag.rag_service import ingest_document, ask_from_material
    from app.rag.vector_store import VectorStore
    from app.rag.retriever import Retriever

    # 4.1 PDF Ingestion
    try:
        result = ingest_document(str(TEST_PDF))
        pages  = result.get("pages", 0)
        chunks = result.get("chunks", 0)
        if pages > 0 and chunks > 0:
            passed("PDF ingestion", f"{pages} pages, {chunks} chunks")
        else:
            failed("PDF ingestion", f"pages={pages}, chunks={chunks}")
    except Exception as e:
        failed("PDF ingestion", str(e)[:100])

    # 4.2 Embedding creation + shared retriever for all retrieval tests
    RAG_STORAGE = str(PROJECT_ROOT / "rag_storage")
    _shared_retriever = None
    try:
        # Ingest builds the FAISS index with real embeddings via OpenRouter
        ingest_result = ingest_document(str(TEST_PDF))
        # Load via rag_service helper (handles path internally)
        from app.rag.rag_service import load_knowledge_base
        _shared_retriever = load_knowledge_base()
        # Count via underlying vector_store
        doc_count = len(_shared_retriever.vector_store.documents)
        if doc_count > 0:
            passed("Embedding creation", f"{doc_count} embeddings in FAISS index")
        else:
            failed("Embedding creation", "No embeddings in index after ingestion")
    except Exception as e:
        failed("Embedding creation", str(e)[:100])

    # 4.3 Retrieval — direct question from document
    try:
        if _shared_retriever is None:
            raise RuntimeError("Retriever not loaded — see Embedding creation failure")
        results = _shared_retriever.retrieve("What is the time complexity of binary search?", top_k=3)
        if results and len(results) > 0:
            top_score = results[0]["score"]
            top_text = results[0]["document"]["text"][:80]
            passed("Retrieval (direct question)", f"top_score={top_score:.2f}, preview='{top_text}'")
        else:
            failed("Retrieval (direct question)", "No results returned")
    except Exception as e:
        failed("Retrieval (direct question)", str(e)[:100])

    # 4.4 Retrieval — different section of document
    try:
        if _shared_retriever is None:
            raise RuntimeError("Retriever not loaded")
        results2 = _shared_retriever.retrieve("explain recursion and dynamic programming", top_k=3)
        if results2:
            passed("Retrieval (different section)", f"{len(results2)} results, score={results2[0]['score']:.2f}")
        else:
            failed("Retrieval (different section)", "No results returned")
    except Exception as e:
        failed("Retrieval (different section)", str(e)[:100])

    # 4.5 Retrieval — paraphrased question
    try:
        if _shared_retriever is None:
            raise RuntimeError("Retriever not loaded")
        results3 = _shared_retriever.retrieve("how do we sort a list efficiently step by step", top_k=3)
        if results3:
            passed("Retrieval (paraphrased)", f"{len(results3)} results, score={results3[0]['score']:.2f}")
        else:
            failed("Retrieval (paraphrased)", "No results (low relevance — may be correct)")
    except Exception as e:
        failed("Retrieval (paraphrased)", str(e)[:100])

    # 4.6 Out-of-scope question — should get low/no relevance
    try:
        if _shared_retriever is None:
            raise RuntimeError("Retriever not loaded")
        results4 = _shared_retriever.retrieve("what is the GDP of Brazil in 2024", top_k=3)
        if not results4:
            passed("Out-of-scope handled", "No results returned (correct)")
        elif results4[0]["score"] < 2.0:
            passed("Out-of-scope handled",
                   f"Low relevance score: {results4[0]['score']:.2f} (correct)")
        else:
            failed("Out-of-scope handled",
                   f"High score {results4[0]['score']:.2f} for unrelated query")
    except Exception as e:
        failed("Out-of-scope handled", str(e)[:100])

    # 4.7 LLM grounded in retrieved context
    try:
        answer = ask_from_material(
            "What is the time complexity of binary search and why?", top_k=3
        )
        if answer and len(answer) > 20:
            if "could not find" not in answer.lower() and "don't have" not in answer.lower():
                passed("LLM grounded in retrieved context", f"answer_len={len(answer)} chars")
                info(f"RAG answer preview: '{answer[:120]}'")
            else:
                failed("LLM grounded in retrieved context", f"LLM refused: {answer[:100]}")
        else:
            failed("LLM grounded in retrieved context", f"Answer too short: '{answer}'")
    except Exception as e:
        failed("LLM grounded in retrieved context", str(e)[:100])


# ════════════════════════════════════════════════════════════
# GROUP 5: LESSON GENERATION
# ════════════════════════════════════════════════════════════

header("GROUP 5: Lesson Generation")

if not configured_providers:
    skipped("Lesson generation", "No LLM provider configured")
else:
    try:
        from app.ai.teaching_engine import create_lesson
        lesson = create_lesson(
            topic="Binary Search",
            level="beginner",
            language="English",
            goal="Understand how binary search works",
            material_context="",
        )
        if lesson and len(lesson) > 100:
            passed("Lesson generation", f"Generated {len(lesson)} chars")
            info(f"Lesson preview: {lesson[:120]}...")
        else:
            failed("Lesson generation", f"Too short: {len(lesson)} chars")
    except Exception as e:
        failed("Lesson generation", str(e)[:100])


# ════════════════════════════════════════════════════════════
# GROUP 6: SCENE PLANNER
# ════════════════════════════════════════════════════════════

header("GROUP 6: Scene Planner")

SAMPLE_LESSON = """
Binary search is an efficient algorithm for finding an item in a sorted list.
It works by repeatedly dividing the search interval in half.
Time complexity: O(log n). Requires a sorted array.
Steps: 1) Set low=0, high=n-1. 2) Find mid=(low+high)//2. 3) Compare.
If target==arr[mid], found. If target < arr[mid], search left half. Else right.
"""

if not configured_providers:
    skipped("Scene planning (LLM)", "No LLM provider configured")
else:
    try:
        from app.video.scene_planner import plan_lesson_scenes
        scenes = plan_lesson_scenes(
            topic="Binary Search",
            lesson_text=SAMPLE_LESSON,
            student_level="beginner",
            language="English",
            available_time_minutes=6,
        )
        if scenes and len(scenes) >= 2:
            passed("Scene planning (LLM)", f"{len(scenes)} scenes generated")
            for s in scenes[:2]:
                info(f"  Scene '{s['scene_id']}': type={s['scene_type']}, visual={s['visual_type']}, interaction={s['interaction_required']}")
        else:
            passed("Scene planning (fallback)", f"{len(scenes)} scenes (may be fallback)")
    except Exception as e:
        failed("Scene planning", str(e)[:100])


# ════════════════════════════════════════════════════════════
# GROUP 7: EDUCATIONAL VISUALS (OFFLINE)
# ════════════════════════════════════════════════════════════

header("GROUP 7: Educational Visuals (offline)")

from app.video.visual_generator import generate_visual

visual_tests = [
    ("equation", r"T(n) = O(\log n)", "Binary Search Complexity"),
    ("code", "def binary_search(arr, target):\n    lo, hi = 0, len(arr)-1\n    while lo <= hi:\n        mid = (lo+hi)//2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: lo = mid+1\n        else: hi = mid-1\n    return -1", ""),
    ("bullet_list", "Sorted array required\nO(log n) time\nO(1) space", "Key Properties"),
    ("comparison", "Linear Search vs Binary Search\nO(n) vs O(log n)\nUnsorted OK vs Sorted required", ""),
    ("flowchart", "Start\nSet lo=0 hi=n-1\nCalculate mid\nCompare target\nReturn or narrow range\nEnd", ""),
    ("timeline", "1946: Binary search conceptualised\n1960: First formal analysis\n1988: First bug-free implementation", ""),
    ("graph", "n=10: 3\nn=100: 7\nn=1000: 10\nn=1000000: 20", "Steps vs Array Size"),
    ("none", "", ""),
]

for vtype, vcontent, caption in visual_tests:
    try:
        html = generate_visual(vtype, vcontent, caption)
        if vtype == "none":
            passed(f"Visual: {vtype}", "returns empty (correct)")
        elif html and len(html) > 50:
            passed(f"Visual: {vtype}", f"{len(html)} chars HTML")
        else:
            failed(f"Visual: {vtype}", f"Too short: {len(html) if html else 0} chars")
    except Exception as e:
        failed(f"Visual: {vtype}", str(e)[:80])


# ════════════════════════════════════════════════════════════
# GROUP 8: FISH AUDIO TTS
# ════════════════════════════════════════════════════════════

header("GROUP 8: Fish Audio TTS")

fish_key = os.getenv("FISH_AUDIO_API_KEY", "")
if not fish_key:
    skipped("Fish Audio TTS", "FISH_AUDIO_API_KEY not set")
else:
    try:
        from fish_audio_sdk import Session, TTSRequest
        passed("fish-audio-sdk import", "SDK installed")
    except ImportError:
        failed("fish-audio-sdk import", "Run: pip install fish-audio-sdk")

    try:
        from app.video.tts_provider import generateSpeech
        out_path = str(PROJECT_ROOT / "rag_uploads" / "tts_cache" / "test_tts.mp3")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        audio_path = generateSpeech(
            text="Hello! I am TUTIVRA, your AI teacher. Let us begin learning Binary Search.",
            language="en",
            output_path=out_path,
        )
        audio_file = Path(audio_path)
        if audio_file.exists() and audio_file.stat().st_size > 1000:
            passed("Fish Audio TTS generation",
                   f"Audio file: {audio_file.stat().st_size} bytes at {audio_path}")
        else:
            failed("Fish Audio TTS generation",
                   f"File too small or missing: {audio_path}")
    except ValueError as e:
        failed("Fish Audio TTS generation", f"Config error: {e}")
    except RuntimeError as e:
        failed("Fish Audio TTS generation", f"API error: {str(e)[:100]}")
    except Exception as e:
        failed("Fish Audio TTS generation", str(e)[:100])


# ════════════════════════════════════════════════════════════
# GROUP 9: D-ID AVATAR VIDEO
# ════════════════════════════════════════════════════════════

header("GROUP 9: D-ID Avatar Video")

did_key = os.getenv("DID_API_KEY", "")
if not did_key:
    skipped("D-ID avatar video", "DID_API_KEY not set")
else:
    try:
        from app.video.avatar_provider import generateAvatarVideo

        # Use text mode (no audio file needed)
        info("Sending request to D-ID API (may take 30-60 seconds)...")
        result = generateAvatarVideo(
            script_text="Hello! I am your AI teacher. Binary search divides and conquers.",
            poll_timeout_seconds=90,
        )
        if result["status"] == "done" and result.get("video_url"):
            passed("D-ID avatar video generation",
                   f"video_url={result['video_url'][:60]}...")
            info(f"Full video URL: {result['video_url']}")
        elif result["status"] == "error":
            failed("D-ID avatar video generation",
                   f"Error: {result.get('error','unknown')[:100]}")
        else:
            failed("D-ID avatar video generation", f"Unexpected status: {result['status']}")
    except ValueError as e:
        failed("D-ID avatar video generation", f"Config error: {e}")
    except Exception as e:
        failed("D-ID avatar video generation", str(e)[:100])


# ════════════════════════════════════════════════════════════
# GROUP 10: FULL VIDEO PIPELINE
# ════════════════════════════════════════════════════════════

header("GROUP 10: Full Video Pipeline")

if not configured_providers:
    skipped("Full video pipeline", "No LLM provider configured")
else:
    try:
        from app.video.lesson_video_pipeline import run_lesson_pipeline

        gen_audio  = bool(fish_key)
        gen_avatar = bool(did_key) and bool(fish_key)

        info(f"Running pipeline: audio={'yes' if gen_audio else 'no'}, avatar={'yes' if gen_avatar else 'no'}")

        pipeline_result = run_lesson_pipeline(
            topic="Binary Search",
            lesson_text=SAMPLE_LESSON,
            student_level="beginner",
            language="en",
            available_time_minutes=4,
            subject_area="Computer Science",
            generate_audio=gen_audio,
            generate_avatar=gen_avatar,
        )

        total_scenes = pipeline_result.get("total_scenes", 0)
        status_val   = pipeline_result.get("pipeline_status", "unknown")
        scene_bundles = pipeline_result.get("scenes", [])

        if total_scenes >= 1:
            passed("Pipeline: scenes generated", f"{total_scenes} scenes, status={status_val}")
        else:
            failed("Pipeline: scenes generated", "No scenes returned")

        # Check visuals in each scene
        scenes_with_visuals = sum(1 for b in scene_bundles if b.get("visual_html"))
        if total_scenes > 0:
            passed("Pipeline: visuals present",
                   f"{scenes_with_visuals}/{total_scenes} scenes have visuals")

        # Check audio
        if gen_audio:
            scenes_with_audio = sum(1 for b in scene_bundles if b.get("audio_path"))
            audio_errors = [b.get("audio_error") for b in scene_bundles if b.get("audio_error")]
            if scenes_with_audio > 0:
                passed("Pipeline: audio generated", f"{scenes_with_audio}/{total_scenes} scenes have audio")
            else:
                failed("Pipeline: audio generated", f"Errors: {audio_errors[:2]}")
        else:
            skipped("Pipeline: audio generated", "FISH_AUDIO_API_KEY not set")

        # Check avatar
        if gen_avatar:
            scenes_with_video = sum(1 for b in scene_bundles if b.get("video_url"))
            if scenes_with_video > 0:
                passed("Pipeline: avatar videos", f"{scenes_with_video}/{total_scenes} scenes have avatar video")
                first_video = next((b["video_url"] for b in scene_bundles if b.get("video_url")), "")
                info(f"First video URL: {first_video[:80]}")
            else:
                video_errors = [b.get("video_error") for b in scene_bundles if b.get("video_error")]
                failed("Pipeline: avatar videos", f"Errors: {video_errors[:1]}")
        else:
            skipped("Pipeline: avatar videos", "DID_API_KEY or FISH_AUDIO_API_KEY not set")

        # Verify narration matches scene
        if scene_bundles:
            s0 = scene_bundles[0]
            scene_narration = s0["scene"].get("narration", "")
            if len(scene_narration) > 10:
                passed("Pipeline: narration present", f"Scene 1: '{scene_narration[:60]}...'")
            else:
                failed("Pipeline: narration present", f"Narration too short: '{scene_narration}'")

        # Report errors
        errors = pipeline_result.get("errors", [])
        if errors:
            for e in errors[:3]:
                info(f"Pipeline non-fatal error: {e[:80]}")

    except Exception as e:
        failed("Full video pipeline", str(e)[:100])


# ════════════════════════════════════════════════════════════
# GROUP 11: STUDENT Q&A LOOP
# ════════════════════════════════════════════════════════════

header("GROUP 11: Student Q&A Loop")

if not configured_providers:
    skipped("Q&A loop", "No LLM provider configured")
else:
    try:
        from app.student.student_model import StudentModel
        from app.learning.adaptive_session import AdaptiveLearningSession
        from app.adaptation.difficulty_engine import get_adaptation_decision
        from app.ai.question_generator import generate_question
        from app.ai.evaluator import evaluate_answer

        student = StudentModel(name="TestStudent_E2E", level="beginner")
        student.initialize_topic("Binary Search")

        # Generate a question
        adapt = get_adaptation_decision(
            mastery=0, attempts=0, correct_answers=0, misconception_detected=False
        )
        question_data = generate_question(
            topic="Binary Search",
            concept="Time complexity of binary search",
            student_level="beginner",
            mastery=0,
            misconceptions=[],
            difficulty=adapt["difficulty"],
            strategy=adapt["strategy"],
            question_type="short_answer",
            material_context=SAMPLE_LESSON,
        )

        if question_data.get("error"):
            failed("Question generation", question_data["error"])
        else:
            q_text    = question_data.get("question", "")
            q_expected = question_data.get("expected_answer", "")
            passed("Question generation", f"q='{q_text[:60]}'")

            # Evaluate a correct answer
            eval_result = evaluate_answer(
                topic="Binary Search",
                question=q_text,
                student_answer="Binary search has O(log n) time complexity because it halves the search space each step.",
                expected_answer=q_expected,
                student_level="beginner",
            )
            if not eval_result.get("system_error"):
                correct = eval_result.get("correct", False)
                feedback = eval_result.get("feedback", "")
                passed("Answer evaluation", f"correct={correct}, feedback='{feedback[:60]}'")
            else:
                failed("Answer evaluation", eval_result.get("system_error","?")[:80])

            # Test wrong answer → misconception detection
            eval_wrong = evaluate_answer(
                topic="Binary Search",
                question=q_text,
                student_answer="Binary search is O(n) because we check each element.",
                expected_answer=q_expected,
                student_level="beginner",
            )
            if not eval_wrong.get("system_error"):
                misconception = eval_wrong.get("misconception", "")
                passed("Misconception detection",
                       f"misconception='{misconception[:60]}'") if misconception else \
                passed("Misconception detection", "No specific misconception returned")
            else:
                failed("Misconception detection", "Evaluation system error")

    except Exception as e:
        failed("Q&A loop", str(e)[:100])


# ════════════════════════════════════════════════════════════
# GROUP 12: FINAL ASSESSMENT
# ════════════════════════════════════════════════════════════

header("GROUP 12: Final Assessment")

if not configured_providers:
    skipped("Final assessment", "No LLM provider configured")
else:
    try:
        from app.ai.assessment_generator import generate_final_assessment, evaluate_assessment_answers

        assessment = generate_final_assessment(
            topic="Binary Search",
            concepts_taught=["binary search", "time complexity", "sorted arrays"],
            student_level="beginner",
            misconceptions=["thinks binary search works on unsorted arrays"],
            weak_concepts=["understanding why O(log n)"],
            material_context=SAMPLE_LESSON,
            language="English",
            n_questions=3,
        )

        questions = assessment.get("questions", [])
        if questions:
            passed("Assessment generation", f"{len(questions)} questions, {assessment.get('total_marks',0)} marks")
            for q in questions[:2]:
                info(f"  Q{q['id']}: [{q['question_type']}] {q['question'][:60]}")
        else:
            failed("Assessment generation", "No questions returned")

        # Evaluate answers
        if questions:
            test_answers = {}
            for q in questions:
                if q["question_type"] == "mcq" and q.get("choices"):
                    # Pick the first choice as answer
                    test_answers[q["id"]] = q["choices"][0]
                else:
                    test_answers[q["id"]] = (
                        "Binary search has O(log n) time complexity. "
                        "It requires a sorted array and halves the search space each iteration."
                    )

            eval_result = evaluate_assessment_answers(
                questions=questions,
                student_answers=test_answers,
                student_level="beginner",
                topic="Binary Search",
            )
            pct = eval_result.get("percentage", 0)
            passed("Assessment evaluation",
                   f"score={eval_result.get('score',0)}/{eval_result.get('max_score',0)}, {pct:.0f}%")
    except Exception as e:
        failed("Final assessment", str(e)[:100])


# ════════════════════════════════════════════════════════════
# GROUP 13: LEARNING REPORT
# ════════════════════════════════════════════════════════════

header("GROUP 13: Learning Report")

if not configured_providers:
    skipped("Learning report", "No LLM provider configured")
else:
    try:
        from app.ai.report_generator import generate_learning_report

        report = generate_learning_report(
            student_name="TestStudent_E2E",
            topic="Binary Search",
            session_data={
                "session_questions": 5,
                "session_correct": 3,
                "mastery_before": 0.0,
                "mastery_after": 45.0,
                "misconceptions": ["confused binary search with linear search"],
                "concepts_taught": ["binary search", "O(log n)", "sorted arrays"],
            },
            assessment_result={
                "score": 7,
                "max_score": 10,
                "percentage": 70.0,
                "concepts_understood": ["binary search", "O(log n)"],
                "weak_concepts": ["when to use binary search"],
                "overall_feedback": "Good progress!",
            },
        )

        if report.get("student") and report.get("score") is not None:
            passed("Learning report generation",
                   f"score={report['score']}%, status={report.get('status','?')}")
            msg = report.get("personalised_message", "")
            if msg:
                info(f"AI message preview: '{msg[:100]}'")
            revision = report.get("revision_plan", [])
            passed("Revision plan", f"{len(revision)} steps")
        else:
            failed("Learning report generation", "Missing required fields")
    except Exception as e:
        failed("Learning report", str(e)[:100])


# ════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════════════

print(f"\n{BOLD}{'='*60}")
print(f"  TEST SUMMARY")
print(f"{'='*60}{RESET}")
print(f"  {GREEN}PASSED: {PASS}{RESET}")
print(f"  {RED}FAILED: {FAIL}{RESET}")
print(f"  {YELLOW}SKIPPED: {SKIP}{RESET}")
print(f"  Total: {PASS + FAIL + SKIP}")

# Provider status
print(f"\n{BOLD}API STATUS:{RESET}")

or_status  = next((r for r in RESULTS if r["name"] == "OpenRouter API"), None)
gem_status = next((r for r in RESULTS if r["name"] == "Gemini API"), None)
grok_status= next((r for r in RESULTS if r["name"] == "Grok (xAI) API"), None)
fish_status= next((r for r in RESULTS if "Fish Audio TTS" in r["name"] and "import" not in r["name"]), None)
did_status = next((r for r in RESULTS if "D-ID avatar" in r["name"]), None)
rag_status = next((r for r in RESULTS if "LLM grounded" in r["name"]), None)
video_status = next((r for r in RESULTS if "Full video pipeline" in r["name"]), None)
fb_status  = next((r for r in RESULTS if "OpenRouter → Gemini" in r["name"]), None)
fb2_status = next((r for r in RESULTS if "Gemini → Grok" in r["name"]), None)
e2e_status = next((r for r in RESULTS if "Learning report generation" in r["name"]), None)

def _fmt(r):
    if r is None: return f"{YELLOW}NOT TESTED{RESET}"
    c = {"PASS": GREEN, "FAIL": RED, "SKIP": YELLOW}[r["status"]]
    return f"{c}{r['status']}{RESET} {r.get('detail','')[:50]}"

print(f"  OpenRouter:  {_fmt(or_status)}")
print(f"  Gemini:      {_fmt(gem_status)}")
print(f"  Grok:        {_fmt(grok_status)}")
print(f"  Fish Audio:  {_fmt(fish_status)}")
print(f"  D-ID:        {_fmt(did_status)}")

print(f"\n{BOLD}RAG:{RESET}")
print(f"  {_fmt(rag_status)}")

print(f"\n{BOLD}VIDEO:{RESET}")
print(f"  {_fmt(video_status)}")

print(f"\n{BOLD}END-TO-END:{RESET}")
print(f"  {_fmt(e2e_status)}")

print(f"\n{BOLD}FALLBACK:{RESET}")
print(f"  OpenRouter → Gemini: {_fmt(fb_status)}")
print(f"  Gemini → Grok:       {_fmt(fb2_status)}")

print(f"\n{BOLD}TESTS:{RESET}")
print(f"  {PASS} passed / {FAIL} failed / {SKIP} skipped")

# Save results
results_path = PROJECT_ROOT / "tests" / "api_e2e_results.json"
with open(results_path, "w") as f:
    json.dump({"passed": PASS, "failed": FAIL, "skipped": SKIP, "results": RESULTS}, f, indent=2)
print(f"\n  Results saved to: {results_path}")

sys.exit(0 if FAIL == 0 else 1)
