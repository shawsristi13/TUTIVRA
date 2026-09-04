"""
TUTIVRA — FastAPI Backend
=========================
REST API server that exposes all TUTIVRA modules as JSON endpoints.

Security: All external API keys (OpenRouter, Fish Audio, D-ID) are
read from environment variables and NEVER exposed to the frontend.

Run:
    uvicorn app.api.main:app --reload --port 8000
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


# ── Import TUTIVRA modules ───────────────────────────────────
from app.student.student_model import StudentModel
from app.learning.adaptive_session import AdaptiveLearningSession
from app.learning.learning_roadmap import create_learning_roadmap
from app.ai.teaching_engine import create_lesson
from app.ai.question_generator import generate_question
from app.ai.evaluator import evaluate_answer
from app.adaptation.difficulty_engine import get_adaptation_decision
from app.rag.rag_service import ingest_document, ask_from_material, load_knowledge_base
from app.video.scene_planner import plan_lesson_scenes
from app.video.visual_generator import generate_visual
from app.video.tts_provider import generateSpeech, get_provider_info
from app.video.avatar_provider import generateAvatarVideo, get_avatar_provider_info
from app.video.lesson_video_pipeline import run_lesson_pipeline
from app.ai.assessment_generator import generate_final_assessment, evaluate_assessment_answers
from app.ai.report_generator import generate_learning_report


# ════════════════════════════════════════════════════════════
# APP SETUP
# ════════════════════════════════════════════════════════════

app = FastAPI(
    title="TUTIVRA API",
    description="AI Teacher — Backend API",
    version="2.0.0",
)

# Allow Streamlit + any local frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated audio files
UPLOADS_DIR = PROJECT_ROOT / "rag_uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(UPLOADS_DIR)), name="audio")


# ════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ════════════════════════════════════════════════════════════

class StudentSetupRequest(BaseModel):
    name: str
    level: str = "beginner"
    topic: str

class LessonRequest(BaseModel):
    topic: str
    student_level: str = "beginner"
    language: str = "English"
    goal: str = ""
    material_context: str = ""
    available_time_minutes: int = 10
    subject_area: str = ""

class ScenePlanRequest(BaseModel):
    topic: str
    lesson_text: str
    student_level: str = "beginner"
    language: str = "en"
    available_time_minutes: int = 10
    subject_area: str = ""
    learning_objective: str = ""

class VideoPipelineRequest(BaseModel):
    topic: str
    lesson_text: str
    student_level: str = "beginner"
    language: str = "en"
    available_time_minutes: int = 10
    subject_area: str = ""
    generate_audio: bool = True
    generate_avatar: bool = True

class QuestionRequest(BaseModel):
    topic: str
    concept: str
    student_level: str
    mastery: float = 0.0
    misconceptions: List[str] = []
    difficulty: str = "medium"
    strategy: str = "continue"
    question_type: str = "conceptual"
    material_context: str = ""

class AnswerRequest(BaseModel):
    topic: str
    question: str
    expected_answer: str
    student_answer: str
    student_level: str = "beginner"

class AdaptiveAnswerRequest(BaseModel):
    student_name: str
    topic: str
    concept: str
    question: str
    expected_answer: str
    student_answer: str

class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 3

class RoadmapRequest(BaseModel):
    material_context: str
    topic: str = ""

class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    voice_id: Optional[str] = None

class AvatarRequest(BaseModel):
    audio_url: Optional[str] = None
    script_text: Optional[str] = None
    avatar_id: Optional[str] = None

class AssessmentRequest(BaseModel):
    topic: str
    concepts_taught: List[str] = []
    student_level: str = "beginner"
    misconceptions: List[str] = []
    weak_concepts: List[str] = []
    material_context: str = ""
    language: str = "English"
    n_questions: int = 5

class AssessmentEvalRequest(BaseModel):
    questions: List[dict]
    student_answers: dict
    student_level: str = "beginner"
    topic: str

class LearningReportRequest(BaseModel):
    student_name: str
    topic: str
    session_data: dict
    assessment_result: Optional[dict] = None


# ════════════════════════════════════════════════════════════
# HEALTH
# ════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "fish_audio_configured": bool(os.getenv("FISH_AUDIO_API_KEY")),
        "did_configured": bool(os.getenv("DID_API_KEY")),
    }


# ════════════════════════════════════════════════════════════
# STUDENT
# ════════════════════════════════════════════════════════════

@app.post("/student/setup")
def setup_student(req: StudentSetupRequest):
    """Create or load a student profile."""
    try:
        student = StudentModel(name=req.name.strip(), level=req.level)
        student.load_from_database(req.topic)
        return student.get_summary(req.topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/student/{name}/progress/{topic}")
def get_progress(name: str, topic: str):
    """Get student progress for a topic."""
    try:
        student = StudentModel(name=name)
        student.load_from_database(topic)
        return student.get_summary(topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════
# RAG / DOCUMENT
# ════════════════════════════════════════════════════════════

@app.post("/rag/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and ingest a PDF into the knowledge base."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_path = UPLOADS_DIR / f"upload_{uuid.uuid4().hex}.pdf"
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        result = ingest_document(str(temp_path))
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.post("/rag/query")
def rag_query(req: RAGQueryRequest):
    """Ask a question against the uploaded study material."""
    try:
        answer = ask_from_material(req.question, top_k=req.top_k)
        return {"question": req.question, "answer": answer}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/roadmap")
def generate_roadmap(req: RoadmapRequest):
    """Generate a learning roadmap from material context."""
    try:
        roadmap = create_learning_roadmap(req.material_context, req.topic)
        return roadmap
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════
# LESSON
# ════════════════════════════════════════════════════════════

@app.post("/lesson/create")
def create_lesson_endpoint(req: LessonRequest):
    """Generate a personalized lesson."""
    try:
        lesson = create_lesson(
            topic=req.topic,
            level=req.student_level,
            language=req.language,
            goal=req.goal,
            material_context=req.material_context,
        )
        return {"topic": req.topic, "lesson": lesson}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════
# VIDEO PIPELINE
# ════════════════════════════════════════════════════════════

@app.post("/video/plan-scenes")
def plan_scenes(req: ScenePlanRequest):
    """Convert lesson text into a structured scene plan."""
    try:
        scenes = plan_lesson_scenes(
            topic=req.topic,
            lesson_text=req.lesson_text,
            student_level=req.student_level,
            language=req.language,
            available_time_minutes=req.available_time_minutes,
            subject_area=req.subject_area,
            learning_objective=req.learning_objective,
        )
        return {"topic": req.topic, "scenes": scenes, "total_scenes": len(scenes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/video/generate-visual")
def generate_visual_endpoint(
    visual_type: str = Body(...),
    visual_content: str = Body(...),
    on_screen_text: str = Body(""),
    subject_area: str = Body(""),
):
    """Generate HTML visual for a scene."""
    try:
        html = generate_visual(
            visual_type=visual_type,
            visual_content=visual_content,
            on_screen_text=on_screen_text,
            subject_area=subject_area,
        )
        return {"html": html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/video/tts")
def tts_endpoint(req: TTSRequest):
    """
    Generate speech audio from text (Fish Audio).
    Returns path to audio file (served via /audio/ endpoint).
    """
    try:
        audio_path = generateSpeech(
            text=req.text,
            language=req.language,
            voice_id=req.voice_id,
        )
        # Convert to a relative URL served by /audio/
        rel_path = Path(audio_path).relative_to(UPLOADS_DIR)
        return {
            "audio_path": str(audio_path),
            "audio_url": f"/audio/{rel_path}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/video/avatar")
def avatar_endpoint(req: AvatarRequest):
    """
    Generate avatar video (D-ID).
    Provide audio_url or script_text.
    """
    try:
        result = generateAvatarVideo(
            audio_url=req.audio_url,
            script_text=req.script_text,
            avatar_id=req.avatar_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/video/pipeline")
def video_pipeline_endpoint(req: VideoPipelineRequest):
    """
    Run the full lesson video pipeline:
    Lesson → Scene Plan → Visuals → Fish Audio → D-ID → Scene Bundles
    """
    try:
        result = run_lesson_pipeline(
            topic=req.topic,
            lesson_text=req.lesson_text,
            student_level=req.student_level,
            language=req.language,
            available_time_minutes=req.available_time_minutes,
            subject_area=req.subject_area,
            generate_audio=req.generate_audio,
            generate_avatar=req.generate_avatar,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/video/providers")
def provider_info():
    """Return info about configured TTS and avatar providers."""
    return {
        "tts": get_provider_info(),
        "avatar": get_avatar_provider_info(),
    }


# ════════════════════════════════════════════════════════════
# ADAPTIVE Q&A
# ════════════════════════════════════════════════════════════

@app.post("/question/generate")
def generate_question_endpoint(req: QuestionRequest):
    """Generate an adaptive question."""
    try:
        question = generate_question(
            topic=req.topic,
            concept=req.concept,
            student_level=req.student_level,
            mastery=req.mastery,
            misconceptions=req.misconceptions,
            difficulty=req.difficulty,
            strategy=req.strategy,
            question_type=req.question_type,
            material_context=req.material_context,
        )
        if question.get("error"):
            raise HTTPException(status_code=500, detail=question["error"])
        return question
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/answer/evaluate")
def evaluate_answer_endpoint(req: AnswerRequest):
    """Evaluate a student's answer."""
    try:
        result = evaluate_answer(
            topic=req.topic,
            question=req.question,
            student_answer=req.student_answer,
            expected_answer=req.expected_answer,
            student_level=req.student_level,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/answer/adaptive")
def adaptive_answer_endpoint(req: AdaptiveAnswerRequest):
    """
    Process an answer in a full adaptive session:
    Evaluate → Update Student → Get Adaptation → Generate Next Question
    """
    try:
        student = StudentModel(name=req.student_name)
        student.load_from_database(req.topic)

        session = AdaptiveLearningSession(
            student=student,
            topic=req.topic,
            concept=req.concept,
        )

        result = session.process_answer(
            question=req.question,
            expected_answer=req.expected_answer,
            student_answer=req.student_answer,
        )

        # Save updated progress
        student.save_to_database(req.topic)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════
# ASSESSMENT
# ════════════════════════════════════════════════════════════

@app.post("/assessment/generate")
def assessment_generate(req: AssessmentRequest):
    """Generate a final assessment for a completed lesson."""
    try:
        assessment = generate_final_assessment(
            topic=req.topic,
            concepts_taught=req.concepts_taught,
            student_level=req.student_level,
            misconceptions=req.misconceptions,
            weak_concepts=req.weak_concepts,
            material_context=req.material_context,
            language=req.language,
            n_questions=req.n_questions,
        )
        return assessment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assessment/evaluate")
def assessment_evaluate(req: AssessmentEvalRequest):
    """Evaluate all student answers in a final assessment."""
    try:
        result = evaluate_assessment_answers(
            questions=req.questions,
            student_answers={int(k): v for k, v in req.student_answers.items()},
            student_level=req.student_level,
            topic=req.topic,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report/generate")
def report_generate(req: LearningReportRequest):
    """Generate a comprehensive learning report."""
    try:
        report = generate_learning_report(
            student_name=req.student_name,
            topic=req.topic,
            session_data=req.session_data,
            assessment_result=req.assessment_result,
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
