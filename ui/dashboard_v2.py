# ============================================================
# TUTIVRA v2 — AI TEACHER DASHBOARD
# Full teaching pipeline: Lesson → Scenes → TTS → Avatar → Q&A → Assessment
# ============================================================

import sys
import os
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

# ── TUTIVRA imports ──────────────────────────────────────────
from app.student.student_model import StudentModel
from app.learning.adaptive_session import AdaptiveLearningSession
from app.learning.learning_roadmap import create_learning_roadmap
from app.ai.teaching_engine import create_lesson
from app.ai.question_generator import generate_question
from app.adaptation.difficulty_engine import get_adaptation_decision
from app.rag.rag_service import ingest_document, ask_from_material, load_knowledge_base
from app.video.scene_planner import plan_lesson_scenes
from app.video.visual_generator import generate_visual
from app.video.tts_provider import generateSpeech, get_provider_info
from app.video.avatar_provider import generateAvatarVideo, get_avatar_provider_info
from app.ai.assessment_generator import generate_final_assessment, evaluate_assessment_answers
from app.ai.report_generator import generate_learning_report


# ════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="TUTIVRA — AI Teacher",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ════════════════════════════════════════════════════════════
# GLOBAL CSS
# ════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, .stApp {
  font-family: 'Inter', sans-serif !important;
  background: #0a0a16 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important;
  border-right: 1px solid rgba(167,139,250,0.2);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { color: #94a3b8 !important; font-size: 0.85em !important; }

/* ── Header ── */
.tutivra-header {
  background: linear-gradient(135deg, #1e1b4b, #312e81, #1e3a8a);
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 24px;
  border: 1px solid rgba(167,139,250,0.3);
  display: flex;
  align-items: center;
  gap: 20px;
}
.tutivra-header h1 {
  font-size: 2.2em;
  font-weight: 700;
  background: linear-gradient(135deg, #a78bfa, #60a5fa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}
.tutivra-header p { color: #94a3b8; margin: 4px 0 0; font-size: 1em; }

/* ── Cards ── */
.card {
  background: linear-gradient(135deg, #1e1b4b22, #312e8122);
  border: 1px solid rgba(167,139,250,0.2);
  border-radius: 14px;
  padding: 20px;
  margin-bottom: 16px;
  backdrop-filter: blur(10px);
}

/* ── Lesson text ── */
.lesson-box {
  background: #0f172a;
  border: 1px solid rgba(99,102,241,0.3);
  border-radius: 12px;
  padding: 24px;
  color: #e2e8f0;
  font-size: 0.95em;
  line-height: 1.7;
  white-space: pre-wrap;
}

/* ── Scene card ── */
.scene-card {
  background: linear-gradient(135deg, #1e1b4b, #1e3a5f);
  border: 1px solid rgba(167,139,250,0.25);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
}
.scene-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.scene-badge {
  background: linear-gradient(135deg, #7c3aed, #2563eb);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.scene-narration {
  color: #cbd5e1;
  font-size: 1em;
  line-height: 1.6;
  border-left: 3px solid #7c3aed;
  padding-left: 16px;
  margin: 12px 0;
}

/* ── Status badges ── */
.badge-success { background: #065f46; color: #6ee7b7; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; }
.badge-warning { background: #78350f; color: #fcd34d; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; }
.badge-error   { background: #7f1d1d; color: #fca5a5; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; }
.badge-info    { background: #1e3a5f; color: #93c5fd; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; }

/* ── Question box ── */
.question-box {
  background: linear-gradient(135deg, #1e3a5f, #1e1b4b);
  border: 1px solid rgba(96,165,250,0.4);
  border-radius: 14px;
  padding: 24px;
  margin: 16px 0;
}
.question-box h3 { color: #bfdbfe; font-size: 1.1em; margin: 0; line-height: 1.5; }

/* ── Progress bar ── */
.progress-track {
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  height: 8px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #7c3aed, #2563eb);
  border-radius: 8px;
  transition: width 0.5s ease;
}

/* ── Evaluation boxes ── */
.eval-correct {
  background: #064e3b;
  border: 1px solid #34d399;
  border-radius: 12px;
  padding: 16px;
}
.eval-incorrect {
  background: #450a0a;
  border: 1px solid #ef4444;
  border-radius: 12px;
  padding: 16px;
}

/* ── Report card ── */
.report-card {
  background: linear-gradient(135deg, #0f172a, #1e293b);
  border: 1px solid rgba(167,139,250,0.3);
  border-radius: 16px;
  padding: 28px;
}
.report-score {
  font-size: 3em;
  font-weight: 700;
  background: linear-gradient(135deg, #a78bfa, #60a5fa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-align: center;
}

/* ── Buttons override ── */
.stButton > button {
  background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
  border: none !important;
  color: white !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.9 !important; }

/* ── Streamlit element overrides ── */
.stTextArea textarea {
  background: #1e293b !important;
  color: #e2e8f0 !important;
  border: 1px solid rgba(99,102,241,0.4) !important;
  border-radius: 10px !important;
}
.stTextInput input {
  background: #1e293b !important;
  color: #e2e8f0 !important;
  border: 1px solid rgba(99,102,241,0.4) !important;
  border-radius: 8px !important;
}
.stSelectbox > div > div {
  background: #1e293b !important;
  border: 1px solid rgba(99,102,241,0.4) !important;
  color: #e2e8f0 !important;
}
div[data-testid="stMarkdownContainer"] p { color: #e2e8f0; }

/* ── Metrics ── */
[data-testid="stMetric"] {
  background: #1e293b;
  border-radius: 12px;
  padding: 12px 16px;
  border: 1px solid rgba(99,102,241,0.2);
}
[data-testid="stMetricValue"] { color: #a78bfa !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.85em !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════

DEFAULTS = {
    # Student
    "student": None,
    "student_name": "",
    "topic": "",
    "student_level": "beginner",
    "language": "en",
    "available_time": 10,
    "subject_area": "",
    "learning_objective": "",

    # Flow state
    "phase": "setup",  # setup | lesson | scenes | qa | assessment | report

    # RAG
    "rag_ready": False,
    "rag_filename": "",
    "rag_pages": 0,
    "rag_chunks": 0,
    "material_context": "",

    # Lesson
    "lesson_text": "",
    "learning_roadmap": None,

    # Scenes
    "scenes": [],
    "current_scene_idx": 0,
    "scene_bundles": [],

    # Q&A session
    "learning_session": None,
    "question_data": None,
    "last_result": None,
    "session_questions": 0,
    "session_correct": 0,
    "mastery_before": 0.0,
    "concepts_taught": [],

    # Assessment
    "assessment": None,
    "assessment_answers": {},
    "assessment_result": None,

    # Report
    "learning_report": None,
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🎓 TUTIVRA")
    st.caption("AI Teacher — Adaptive Learning Platform")
    st.divider()

    # API status
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    has_fish       = bool(os.getenv("FISH_AUDIO_API_KEY"))
    has_did        = bool(os.getenv("DID_API_KEY"))

    st.markdown("**API Status**")
    st.markdown(
        f"{'🟢' if has_openrouter else '🔴'} OpenRouter LLM  \n"
        f"{'🟢' if has_fish else '🔴'} Fish Audio TTS  \n"
        f"{'🟢' if has_did else '🔴'} D-ID Avatar"
    )

    if not has_openrouter:
        st.error("Add OPENROUTER_API_KEY to .env to use TUTIVRA.")

    st.divider()

    # Navigation
    st.markdown("**Session Progress**")
    phases = ["setup", "lesson", "scenes", "qa", "assessment", "report"]
    labels = ["⚙️ Setup", "📖 Lesson", "🎬 Scenes", "❓ Q&A", "📝 Assessment", "📊 Report"]
    current = st.session_state.phase
    for p, l in zip(phases, labels):
        idx = phases.index(p)
        cur_idx = phases.index(current)
        if idx < cur_idx:
            st.success(l)
        elif idx == cur_idx:
            st.info(l)
        else:
            st.caption(f"   {l}")

    st.divider()

    if st.session_state.student_name:
        st.markdown(f"**Student:** {st.session_state.student_name}")
    if st.session_state.topic:
        st.markdown(f"**Topic:** {st.session_state.topic}")
    if st.session_state.student:
        mastery = st.session_state.student.get_mastery(st.session_state.topic)
        st.markdown(f"**Mastery:** {mastery:.1f}%")

    st.divider()
    if st.button("🔄 New Session", use_container_width=True):
        for key, val in DEFAULTS.items():
            st.session_state[key] = val
        st.rerun()


# ════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════

st.markdown("""
<div class="tutivra-header">
  <div>
    <h1>🎓 TUTIVRA</h1>
    <p>AI Teacher — Personalized Adaptive Learning Through Video</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PHASE 1: SETUP
# ════════════════════════════════════════════════════════════

if st.session_state.phase == "setup":

    st.markdown("## ⚙️ Setup Your Learning Session")
    st.markdown("Tell TUTIVRA about yourself and what you want to learn.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👤 Student Profile")
        name = st.text_input("Your name", placeholder="e.g. Riya", key="input_name")
        level = st.selectbox(
            "Your learning level",
            ["beginner", "intermediate", "advanced"],
            key="input_level",
        )
        language = st.selectbox(
            "Teaching language",
            ["en", "hi", "zh", "ja", "ko", "fr", "de", "ar"],
            format_func=lambda x: {
                "en": "🇬🇧 English",
                "hi": "🇮🇳 Hindi",
                "zh": "🇨🇳 Chinese",
                "ja": "🇯🇵 Japanese",
                "ko": "🇰🇷 Korean",
                "fr": "🇫🇷 French",
                "de": "🇩🇪 German",
                "ar": "🇸🇦 Arabic",
            }.get(x, x),
            key="input_language",
        )

    with col2:
        st.markdown("### 📚 What to Learn")
        topic = st.text_input(
            "Topic", placeholder="e.g. Binary Search Trees, Newton's Laws, World War II",
            key="input_topic",
        )
        subject_area = st.text_input(
            "Subject area (optional)",
            placeholder="e.g. Computer Science, Physics, History",
            key="input_subject",
        )
        learning_objective = st.text_input(
            "Learning objective (optional)",
            placeholder="e.g. Understand how BSTs work and implement one",
            key="input_objective",
        )
        available_time = st.slider(
            "Available time (minutes)", 5, 30, 10, key="input_time"
        )

    st.divider()
    st.markdown("### 📄 Upload Study Material (Optional)")
    st.caption(
        "Upload a PDF (textbook, notes, slides) and TUTIVRA will teach from your material."
    )

    uploaded_file = st.file_uploader(
        "Upload PDF", type=["pdf"], key="pdf_upload"
    )

    if uploaded_file and not st.session_state.rag_ready:
        with st.spinner("Processing your study material..."):
            import tempfile
            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False, dir=str(PROJECT_ROOT / "rag_uploads")
            ) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            try:
                result = ingest_document(tmp_path)
                st.session_state.rag_ready = True
                st.session_state.rag_filename = result["filename"]
                st.session_state.rag_pages   = result["pages"]
                st.session_state.rag_chunks  = result["chunks"]
                st.success(
                    f"✅ **{result['filename']}** ingested — "
                    f"{result['pages']} pages, {result['chunks']} knowledge chunks"
                )
            except Exception as e:
                st.error(f"Failed to process PDF: {e}")
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    if st.session_state.rag_ready:
        st.success(
            f"📚 Knowledge base ready: **{st.session_state.rag_filename}** "
            f"({st.session_state.rag_pages} pages, {st.session_state.rag_chunks} chunks)"
        )

    st.divider()

    if st.button("🚀 Start Learning Session", type="primary", use_container_width=True):
        if not name.strip():
            st.error("Please enter your name.")
        elif not topic.strip():
            st.error("Please enter a topic to learn.")
        elif not has_openrouter:
            st.error("OPENROUTER_API_KEY is required. Add it to .env")
        else:
            # Save setup
            st.session_state.student_name      = name.strip()
            st.session_state.topic             = topic.strip()
            st.session_state.student_level     = level
            st.session_state.language          = language
            st.session_state.subject_area      = subject_area
            st.session_state.learning_objective= learning_objective
            st.session_state.available_time    = available_time

            # Create student model
            student = StudentModel(name=name.strip(), level=level)
            student.load_from_database(topic.strip())
            st.session_state.student          = student
            st.session_state.mastery_before   = student.get_mastery(topic.strip())

            st.session_state.phase = "lesson"
            st.rerun()


# ════════════════════════════════════════════════════════════
# PHASE 2: LESSON GENERATION
# ════════════════════════════════════════════════════════════

elif st.session_state.phase == "lesson":

    topic         = st.session_state.topic
    level         = st.session_state.student_level
    language      = st.session_state.language
    subject_area  = st.session_state.subject_area
    objective     = st.session_state.learning_objective

    st.markdown(f"## 📖 Generating Your Lesson — *{topic}*")

    if not st.session_state.lesson_text:
        with st.spinner("🤖 TUTIVRA is creating your personalized lesson..."):
            try:
                # Get material context if RAG is ready
                material_context = ""
                if st.session_state.rag_ready:
                    try:
                        retriever = load_knowledge_base()
                        results = retriever.retrieve(topic, top_k=5)
                        if results:
                            material_context = "\n\n".join(
                                f"[Page {r['document']['page']}]\n{r['document']['text']}"
                                for r in results
                            )
                    except Exception:
                        pass

                lesson_text = create_lesson(
                    topic=topic,
                    level=level,
                    language={
                        "en": "English", "hi": "Hindi", "zh": "Chinese",
                        "ja": "Japanese", "ko": "Korean", "fr": "French",
                        "de": "German", "ar": "Arabic",
                    }.get(language, "English"),
                    goal=objective or f"Understand {topic}",
                    material_context=material_context,
                )

                st.session_state.lesson_text = lesson_text
                st.session_state.material_context = material_context

                # Also generate roadmap if material available
                if material_context:
                    try:
                        roadmap = create_learning_roadmap(material_context, topic)
                        st.session_state.learning_roadmap = roadmap
                    except Exception:
                        pass

            except Exception as e:
                st.error(f"Lesson generation failed: {e}")
                st.stop()

    lesson_text = st.session_state.lesson_text

    # Display lesson
    tab1, tab2 = st.tabs(["📖 Lesson Content", "🗺️ Learning Roadmap"])

    with tab1:
        st.markdown(f"""
        <div class="lesson-box">{lesson_text}</div>
        """, unsafe_allow_html=True)

    with tab2:
        roadmap = st.session_state.learning_roadmap
        if roadmap:
            st.markdown(f"**Subject:** {roadmap.get('subject', topic)}")
            concepts = roadmap.get("concepts", [])
            if concepts:
                for c in concepts:
                    st.markdown(
                        f"**{c['order']}.** {c['name']} — *{c['description'][:100]}*"
                    )
                    if c.get("concepts_taught"):
                        st.session_state.concepts_taught = [
                            con["name"] for con in concepts
                        ]
        else:
            st.info("Upload a PDF to see a concept-by-concept roadmap.")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎬 Generate Teaching Scenes", type="primary", use_container_width=True):
            st.session_state.phase = "scenes"
            st.rerun()
    with col2:
        if st.button("❓ Skip to Q&A Practice", use_container_width=True):
            st.session_state.phase = "qa"
            st.rerun()


# ════════════════════════════════════════════════════════════
# PHASE 3: SCENE PLAYER
# ════════════════════════════════════════════════════════════

elif st.session_state.phase == "scenes":

    topic        = st.session_state.topic
    lesson_text  = st.session_state.lesson_text
    level        = st.session_state.student_level
    language     = st.session_state.language
    subject_area = st.session_state.subject_area

    st.markdown(f"## 🎬 Teaching Scenes — *{topic}*")

    if not st.session_state.scenes:
        with st.spinner("🤖 Generating structured teaching scenes..."):
            try:
                scenes = plan_lesson_scenes(
                    topic=topic,
                    lesson_text=lesson_text,
                    student_level=level,
                    language={
                        "en": "English", "hi": "Hindi", "zh": "Chinese",
                        "ja": "Japanese", "fr": "French", "de": "German",
                        "ar": "Arabic",
                    }.get(language, "English"),
                    available_time_minutes=st.session_state.available_time,
                    subject_area=subject_area,
                    learning_objective=st.session_state.learning_objective,
                )
                st.session_state.scenes = scenes
                st.session_state.current_scene_idx = 0
            except Exception as e:
                st.error(f"Scene generation failed: {e}")
                st.stop()

    scenes = st.session_state.scenes
    current_idx = st.session_state.current_scene_idx

    if not scenes:
        st.warning("No scenes generated. Proceeding to Q&A.")
        st.session_state.phase = "qa"
        st.rerun()

    # Scene progress indicator
    total = len(scenes)
    progress_pct = (current_idx) / total if total > 0 else 0
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:16px;">
      <span style="color:#94a3b8; font-size:0.9em;">Scene {current_idx+1} of {total}</span>
      <div class="progress-track" style="flex:1">
        <div class="progress-fill" style="width:{progress_pct*100:.0f}%"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    scene = scenes[current_idx]

    # Scene card
    scene_type_emoji = {
        "introduction": "🌟",
        "explanation": "💡",
        "example": "🔢",
        "demonstration": "🔬",
        "question": "❓",
        "summary": "📋",
    }.get(scene.get("scene_type", ""), "📌")

    st.markdown(f"""
    <div class="scene-card">
      <div class="scene-header">
        <span class="scene-badge">{scene_type_emoji} {scene.get("scene_type","").replace("_"," ").title()}</span>
        <span style="color:#94a3b8; font-size:0.85em;">Concept: <strong style="color:#a78bfa">{scene.get("concept","")}</strong></span>
        <span style="color:#64748b; font-size:0.8em;">~{scene.get("duration_seconds",30)}s</span>
      </div>
      <div class="scene-narration">{scene.get("narration","")}</div>
      <p style="color:#94a3b8; font-size:0.85em; margin:8px 0 0;">
        <strong style="color:#60a5fa">{scene.get("on_screen_text","")}</strong>
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Generate and display visual
    visual_type    = scene.get("visual_type", "none")
    visual_content = scene.get("visual_content", "")

    if visual_type and visual_type != "none" and visual_content:
        with st.expander("📊 Educational Visual", expanded=True):
            visual_html = generate_visual(
                visual_type=visual_type,
                visual_content=visual_content,
                on_screen_text=scene.get("on_screen_text", ""),
                subject_area=subject_area,
            )
            if visual_html:
                components.html(visual_html, height=350, scrolling=True)

    # TTS audio (if Fish Audio configured)
    narration = scene.get("narration", "")
    if has_fish and narration:
        with st.expander("🔊 Narration Audio", expanded=False):
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("▶️ Generate Audio", key=f"tts_{current_idx}"):
                    with st.spinner("Generating audio..."):
                        try:
                            audio_path = generateSpeech(
                                text=narration,
                                language=language,
                            )
                            st.audio(audio_path)
                            # D-ID avatar option
                            if has_did:
                                if st.button("🎭 Generate Avatar Video", key=f"did_{current_idx}"):
                                    with st.spinner("Generating avatar video (may take 30-60s)..."):
                                        result = generateAvatarVideo(audio_path=audio_path)
                                        if result["status"] == "done":
                                            st.video(result["video_url"])
                                        else:
                                            st.warning(f"Avatar video: {result.get('error','Failed')}")
                        except Exception as e:
                            st.warning(f"Audio generation: {e}")
            with col2:
                st.info(
                    "💡 Audio generation uses Fish Audio TTS. "
                    "D-ID avatar video requires DID_API_KEY."
                )
    elif not has_fish:
        st.info("💡 Add FISH_AUDIO_API_KEY to .env to enable voice narration.")

    # Interaction point
    if scene.get("interaction_required") and scene.get("question"):
        st.divider()
        st.markdown(f"""
        <div class="question-box">
          <h3>❓ {scene.get("question","")}</h3>
        </div>
        """, unsafe_allow_html=True)

        q_type = scene.get("question_type", "short_answer")
        choices = scene.get("choices", [])

        if q_type == "mcq" and choices:
            answer = st.radio("Choose your answer:", choices, key=f"mcq_{current_idx}")
        else:
            answer = st.text_area(
                "Your answer:", height=100, key=f"ans_{current_idx}",
                placeholder="Type your answer here..."
            )

        if st.button("✅ Submit Answer", key=f"submit_{current_idx}"):
            if not str(answer).strip():
                st.warning("Please provide an answer.")
            else:
                st.session_state.phase = "qa"
                st.session_state.question_data = {
                    "question": scene.get("question", ""),
                    "expected_answer": "",
                    "concept": scene.get("concept", ""),
                    "difficulty": scene.get("difficulty", "medium"),
                    "question_type": q_type,
                    "_prefilled_answer": str(answer),
                }
                st.rerun()

    # Navigation
    st.divider()
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

    with nav_col1:
        if current_idx > 0:
            if st.button("⬅️ Previous Scene"):
                st.session_state.current_scene_idx -= 1
                st.rerun()

    with nav_col2:
        if current_idx < total - 1:
            if st.button("➡️ Next Scene", type="primary", use_container_width=True):
                st.session_state.current_scene_idx += 1
                st.rerun()
        else:
            if st.button("❓ Start Q&A Practice", type="primary", use_container_width=True):
                st.session_state.phase = "qa"
                st.rerun()

    with nav_col3:
        if st.button("Skip to Q&A ⏩"):
            st.session_state.phase = "qa"
            st.rerun()


# ════════════════════════════════════════════════════════════
# PHASE 4: ADAPTIVE Q&A
# ════════════════════════════════════════════════════════════

elif st.session_state.phase == "qa":

    topic   = st.session_state.topic
    student = st.session_state.student
    level   = st.session_state.student_level

    st.markdown(f"## ❓ Adaptive Q&A — *{topic}*")

    # Initialize learning session
    if st.session_state.learning_session is None:
        st.session_state.learning_session = AdaptiveLearningSession(
            student=student,
            topic=topic,
            concept=st.session_state.concepts_taught[0]
                    if st.session_state.concepts_taught
                    else f"Core concepts of {topic}",
        )

    session = st.session_state.learning_session

    # Progress strip
    q_done = st.session_state.session_questions
    q_correct = st.session_state.session_correct
    mastery = student.get_mastery(topic)
    MAX_QA = 5

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Mastery", f"{mastery:.1f}%")
    with c2: st.metric("Questions", q_done)
    with c3: st.metric("Correct", q_correct)
    with c4: st.metric("Accuracy", f"{q_correct/q_done*100:.0f}%" if q_done else "—")

    # Show last evaluation result
    if st.session_state.last_result:
        result = st.session_state.last_result
        ev = result.get("evaluation", {})

        if ev.get("correct"):
            st.markdown(f"""
            <div class="eval-correct">
              <strong style="color:#34d399">✅ Correct!</strong>
              <p style="color:#6ee7b7; margin:4px 0 0">{ev.get("feedback","")}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="eval-incorrect">
              <strong style="color:#f87171">❌ Needs improvement</strong>
              <p style="color:#fca5a5; margin:4px 0 0">{ev.get("feedback","")}</p>
              {"<p style='color:#fcd34d; font-size:0.85em'>⚠️ Misconception: " + ev.get("misconception","") + "</p>" if ev.get("misconception") else ""}
            </div>
            """, unsafe_allow_html=True)

        adapt = result.get("adaptation", {})
        if adapt:
            st.caption(
                f"📐 Next: {adapt.get('difficulty','?')} difficulty · "
                f"Strategy: {adapt.get('strategy','?').replace('_',' ')}"
            )

    st.divider()

    # Check if session complete
    if q_done >= MAX_QA:
        st.success(f"✅ Q&A complete! Answered {q_done} questions, {q_correct} correct.")
        if st.button("📝 Take Final Assessment", type="primary", use_container_width=True):
            st.session_state.phase = "assessment"
            st.rerun()
        st.stop()

    # Generate question if needed
    if st.session_state.question_data is None:
        with st.spinner("Generating adaptive question..."):
            try:
                mastery_val = student.get_mastery(topic)
                misconceptions = student.misconceptions.get(topic, [])
                adaptation = get_adaptation_decision(
                    mastery=mastery_val,
                    attempts=student.attempts.get(topic, 0),
                    correct_answers=student.correct_answers.get(topic, 0),
                    misconception_detected=bool(misconceptions),
                )
                question_data = generate_question(
                    topic=topic,
                    concept=session.get_current_concept(),
                    student_level=level,
                    mastery=mastery_val,
                    misconceptions=misconceptions,
                    difficulty=adaptation["difficulty"],
                    strategy=adaptation["strategy"],
                    question_type=adaptation["question_type"],
                    material_context=st.session_state.material_context,
                )
                if question_data.get("error"):
                    st.error(f"Question error: {question_data['error']}")
                    st.stop()
                st.session_state.question_data = question_data
                st.session_state.last_result = None
                st.rerun()
            except Exception as e:
                st.error(f"Question generation failed: {e}")
                st.stop()

    # Display question
    qd = st.session_state.question_data
    question = qd.get("question", "")
    difficulty = qd.get("difficulty", "medium")
    q_type = qd.get("question_type", "")

    diff_color = {"easy": "#22c55e", "medium": "#f59e0b", "hard": "#ef4444", "advanced": "#a855f7"}.get(difficulty, "#94a3b8")

    st.markdown(f"""
    <div class="question-box">
      <p style="color:{diff_color}; font-size:0.8em; margin:0 0 8px; text-transform:uppercase; letter-spacing:1px;">
        Question {q_done + 1}/{MAX_QA} · {difficulty} · {q_type.replace('_',' ')}
      </p>
      <h3>{question}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Pre-filled answer (from scene interaction)
    prefilled = qd.get("_prefilled_answer", "")

    with st.form("qa_form", clear_on_submit=False):
        answer = st.text_area(
            "Your answer",
            value=prefilled,
            height=140,
            placeholder="Explain your answer clearly...",
        )
        submitted = st.form_submit_button(
            "Submit Answer ✅",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not answer.strip():
            st.warning("Please provide an answer.")
        else:
            with st.spinner("Evaluating..."):
                try:
                    result = session.process_answer(
                        question=question,
                        expected_answer=qd.get("expected_answer", ""),
                        student_answer=answer.strip(),
                    )
                    ev = result.get("evaluation", {})
                    if not ev.get("system_error"):
                        if ev.get("correct"):
                            st.session_state.session_correct += 1
                        st.session_state.session_questions += 1
                        student.save_to_database(topic)

                    st.session_state.last_result = result
                    st.session_state.question_data = result.get("next_question")
                    st.rerun()
                except Exception as e:
                    st.error(f"Evaluation error: {e}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Skip to Assessment", use_container_width=True):
            st.session_state.phase = "assessment"
            st.rerun()
    with col2:
        if st.button("🔄 New Question", use_container_width=True):
            st.session_state.question_data = None
            st.session_state.last_result = None
            st.rerun()


# ════════════════════════════════════════════════════════════
# PHASE 5: FINAL ASSESSMENT
# ════════════════════════════════════════════════════════════

elif st.session_state.phase == "assessment":

    topic   = st.session_state.topic
    student = st.session_state.student
    level   = st.session_state.student_level

    st.markdown(f"## 📝 Final Assessment — *{topic}*")

    # Generate assessment
    if st.session_state.assessment is None:
        with st.spinner("Generating final assessment..."):
            try:
                misconceptions = student.misconceptions.get(topic, [])
                weak_concepts = [
                    m for m in misconceptions
                ] if misconceptions else []

                assessment = generate_final_assessment(
                    topic=topic,
                    concepts_taught=st.session_state.concepts_taught or [topic],
                    student_level=level,
                    misconceptions=misconceptions,
                    weak_concepts=weak_concepts,
                    material_context=st.session_state.material_context,
                    language={
                        "en": "English", "hi": "Hindi",
                    }.get(st.session_state.language, "English"),
                    n_questions=5,
                )
                st.session_state.assessment = assessment
            except Exception as e:
                st.error(f"Assessment generation failed: {e}")
                st.stop()

    assessment = st.session_state.assessment
    questions = assessment.get("questions", [])

    if not questions:
        st.warning("Could not generate assessment questions.")
        if st.button("📊 Go to Report"):
            st.session_state.phase = "report"
            st.rerun()
        st.stop()

    st.markdown(
        f"**{len(questions)} questions** · "
        f"Total marks: **{assessment.get('total_marks', '?')}** · "
        f"Estimated time: **{assessment.get('time_estimate_minutes', 10)} minutes**"
    )

    st.divider()

    # Display questions + collect answers
    if not st.session_state.assessment_result:
        with st.form("assessment_form"):
            answers = {}
            for q in questions:
                qid = q["id"]
                q_type = q.get("question_type", "short_answer")
                choices = q.get("choices") or []

                st.markdown(f"""
                <div class="question-box" style="margin-bottom:8px">
                  <p style="color:#94a3b8; font-size:0.8em; margin:0;">
                    Q{qid} · {q_type.replace('_',' ').title()} · {q.get('marks',1)} mark(s) · {q.get('difficulty','medium')}
                  </p>
                  <h3 style="margin-top:6px">{q.get("question","")}</h3>
                </div>
                """, unsafe_allow_html=True)

                if q_type == "mcq" and choices:
                    answers[qid] = st.radio(
                        "Select answer:", choices,
                        key=f"assessment_q_{qid}",
                    )
                else:
                    answers[qid] = st.text_area(
                        "Your answer:",
                        height=100,
                        key=f"assessment_q_{qid}",
                        placeholder="Write your answer here...",
                    )

                st.divider()

            submitted = st.form_submit_button(
                "Submit Assessment ✅", type="primary", use_container_width=True
            )

        if submitted:
            # Validate all questions answered
            missing = [q["id"] for q in questions if not str(answers.get(q["id"], "")).strip()]
            if missing:
                st.warning(f"Please answer questions: {missing}")
            else:
                with st.spinner("Evaluating your assessment..."):
                    try:
                        result = evaluate_assessment_answers(
                            questions=questions,
                            student_answers={k: str(v) for k, v in answers.items()},
                            student_level=level,
                            topic=topic,
                        )
                        st.session_state.assessment_result = result
                        st.session_state.assessment_answers = answers
                        st.rerun()
                    except Exception as e:
                        st.error(f"Assessment evaluation failed: {e}")

    else:
        # Show results
        result = st.session_state.assessment_result
        pct = result.get("percentage", 0)
        score = result.get("score", 0)
        max_s = result.get("max_score", 0)

        # Score display
        color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 60 else "#ef4444"
        st.markdown(f"""
        <div class="report-card" style="text-align:center; padding:32px; margin-bottom:24px">
          <div class="report-score" style="color:{color}">{pct:.0f}%</div>
          <p style="color:#94a3b8; margin:8px 0">{score} / {max_s} marks</p>
          <p style="color:#e2e8f0">{result.get("overall_feedback","")}</p>
        </div>
        """, unsafe_allow_html=True)

        # Per-question results
        st.markdown("### Question-by-Question Results")
        for q_result in result.get("question_results", []):
            qid = q_result["id"]
            correct = q_result.get("correct", False)
            q_obj = next((q for q in questions if q["id"] == qid), {})

            icon = "✅" if correct else "❌"
            with st.expander(f"{icon} Question {qid}: {q_obj.get('question','')[:60]}..."):
                st.write(f"**Marks earned:** {q_result.get('marks_earned',0)}")
                st.write(f"**Feedback:** {q_result.get('feedback','')}")
                if q_result.get("misconception"):
                    st.warning(f"Misconception: {q_result['misconception']}")

        st.divider()
        if st.button("📊 View Learning Report", type="primary", use_container_width=True):
            st.session_state.phase = "report"
            st.rerun()


# ════════════════════════════════════════════════════════════
# PHASE 6: LEARNING REPORT
# ════════════════════════════════════════════════════════════

elif st.session_state.phase == "report":

    topic   = st.session_state.topic
    student = st.session_state.student

    st.markdown(f"## 📊 Learning Report — *{topic}*")

    if st.session_state.learning_report is None:
        with st.spinner("Generating your learning report..."):
            try:
                misconceptions = student.misconceptions.get(topic, [])
                report = generate_learning_report(
                    student_name=st.session_state.student_name,
                    topic=topic,
                    session_data={
                        "session_questions": st.session_state.session_questions,
                        "session_correct":   st.session_state.session_correct,
                        "mastery_before":    st.session_state.mastery_before,
                        "mastery_after":     student.get_mastery(topic),
                        "misconceptions":    misconceptions,
                        "concepts_taught":   st.session_state.concepts_taught,
                    },
                    assessment_result=st.session_state.assessment_result,
                )
                st.session_state.learning_report = report
            except Exception as e:
                st.error(f"Report generation failed: {e}")
                st.stop()

    report = st.session_state.learning_report

    # ── Top summary ──────────────────────────────────────────

    status_colors = {
        "excellent":     "#22c55e",
        "good":          "#3b82f6",
        "needs_revision":"#f59e0b",
        "repeat_lesson": "#ef4444",
    }
    status = report.get("status", "needs_revision")
    color  = status_colors.get(status, "#94a3b8")
    score  = report.get("score", 0)

    st.markdown(f"""
    <div class="report-card" style="text-align:center; margin-bottom:28px">
      <div class="report-score">{score:.0f}%</div>
      <p style="color:{color}; font-size:1.1em; font-weight:600; text-transform:capitalize;">
        {status.replace("_"," ")}
      </p>
      <p style="color:#cbd5e1; max-width:600px; margin:12px auto; line-height:1.6">
        {report.get("personalised_message","")}
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats grid ────────────────────────────────────────────

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Mastery Before", f"{report.get('mastery_before',0):.1f}%")
    with c2:
        m_after = report.get('mastery_after', 0)
        m_delta = report.get('mastery_delta', 0)
        st.metric("Mastery After", f"{m_after:.1f}%", delta=f"{m_delta:+.1f}%")
    with c3:
        st.metric("Session Accuracy", f"{report.get('session_accuracy',0):.1f}%")
    with c4:
        if report.get("assessment_percentage") is not None:
            st.metric("Assessment", f"{report['assessment_percentage']:.1f}%")
        else:
            st.metric("Questions", report.get("session_questions", 0))

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Concepts Understood")
        concepts = report.get("concepts_understood", [])
        if concepts:
            for c in concepts:
                st.success(f"✓ {c}")
        else:
            st.info("No specific concepts tracked this session.")

        st.markdown("### ⚠️ Areas to Improve")
        weak = report.get("weak_concepts", [])
        misconcepts = report.get("misconceptions", [])
        if weak:
            for w in weak:
                st.warning(f"• {w}")
        if misconcepts:
            for m in misconcepts:
                st.error(f"✗ Misconception: {m}")
        if not weak and not misconcepts:
            st.success("No significant weak areas identified!")

    with col2:
        st.markdown("### 🗺️ Revision Plan")
        plan = report.get("revision_plan", [])
        if plan:
            for i, step in enumerate(plan, 1):
                st.markdown(f"**{i}.** {step}")

        st.divider()

        st.markdown("### ➡️ Next Steps")
        next_topic = report.get("recommended_next_topic", "")
        next_diff  = report.get("recommended_difficulty", "medium")

        st.markdown(f"**Recommended next topic:** {next_topic}")
        st.markdown(f"**Suggested difficulty:** {next_diff}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Learn Another Topic", type="primary", use_container_width=True):
            for key, val in DEFAULTS.items():
                st.session_state[key] = val
            st.rerun()
    with col2:
        if st.button("📖 Review This Topic", use_container_width=True):
            # Keep student and topic, go back to lesson
            keep_keys = ["student", "student_name", "topic", "student_level",
                         "language", "subject_area", "material_context",
                         "rag_ready", "rag_filename", "rag_pages", "rag_chunks"]
            saved = {k: st.session_state[k] for k in keep_keys}
            for key, val in DEFAULTS.items():
                st.session_state[key] = val
            for k, v in saved.items():
                st.session_state[k] = v
            st.session_state.phase = "lesson"
            st.rerun()


# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════

st.divider()
st.markdown(
    "<p style='text-align:center; color:#475569; font-size:0.8em'>"
    "🎓 TUTIVRA v2 — AI Teacher | "
    "Powered by OpenRouter LLM · Fish Audio TTS · D-ID Avatar"
    "</p>",
    unsafe_allow_html=True,
)
