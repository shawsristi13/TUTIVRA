// ============================================================
// TUTIVRA — Centralized API Client
// All fetch calls to the FastAPI backend live here.
// ============================================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ─── Health ──────────────────────────────────────────────────
export const getHealth = () => apiFetch<Record<string, unknown>>("/health");
export const getProviders = () => apiFetch<Record<string, unknown>>("/video/providers");

// ─── Student ─────────────────────────────────────────────────
export const setupStudent = (name: string, level: string, topic: string) =>
  apiFetch<Record<string, unknown>>("/student/setup", {
    method: "POST",
    body: JSON.stringify({ name, level, topic }),
  });

export const getProgress = (name: string, topic: string) =>
  apiFetch<Record<string, unknown>>(`/student/${encodeURIComponent(name)}/progress/${encodeURIComponent(topic)}`);

// ─── RAG / Content ───────────────────────────────────────────
export const uploadPdf = async (file: File) => {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/rag/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Upload failed: ${res.status}`);
  }
  return res.json();
};

export const generateRoadmap = (materialContext: string, topic: string) =>
  apiFetch<Record<string, unknown>>("/rag/roadmap", {
    method: "POST",
    body: JSON.stringify({ material_context: materialContext, topic }),
  });

// ─── Lesson ──────────────────────────────────────────────────
export interface LessonRequest {
  topic: string;
  student_level: string;
  language: string;
  goal: string;
  material_context: string;
  available_time_minutes: number;
  subject_area: string;
}
export const createLesson = (req: LessonRequest) =>
  apiFetch<{ topic: string; lesson: string }>("/lesson/create", {
    method: "POST",
    body: JSON.stringify(req),
  });

// ─── Scenes ──────────────────────────────────────────────────
export interface Scene {
  scene_id: string;
  concept: string;
  scene_type: string;
  narration: string;
  visual_type: string;
  visual_content: string;
  on_screen_text: string;
  duration_seconds: number;
  interaction_required: boolean;
  question: string;
  question_type: string;
  choices: string[];
  difficulty: string;
  language: string;
}
export const planScenes = (
  topic: string,
  lesson_text: string,
  student_level: string,
  language: string,
  available_time_minutes: number,
  subject_area: string,
  learning_objective: string
) =>
  apiFetch<{ topic: string; scenes: Scene[]; total_scenes: number }>("/video/plan-scenes", {
    method: "POST",
    body: JSON.stringify({ topic, lesson_text, student_level, language, available_time_minutes, subject_area, learning_objective }),
  });

// ─── Visuals ─────────────────────────────────────────────────
export const generateVisual = (
  visual_type: string,
  visual_content: string,
  on_screen_text = "",
  subject_area = ""
) =>
  apiFetch<{ html: string }>("/video/generate-visual", {
    method: "POST",
    body: JSON.stringify({ visual_type, visual_content, on_screen_text, subject_area }),
  });

// ─── TTS ─────────────────────────────────────────────────────
export const generateTts = (text: string, language = "en") =>
  apiFetch<{ audio_path: string; audio_url: string }>("/video/tts", {
    method: "POST",
    body: JSON.stringify({ text, language }),
  });

// ─── Avatar ──────────────────────────────────────────────────
export const generateAvatar = (audioPath?: string, scriptText?: string) =>
  apiFetch<{ status: string; video_url?: string; talk_id?: string; error?: string }>("/video/avatar", {
    method: "POST",
    body: JSON.stringify({ audio_path: audioPath, script_text: scriptText }),
  });

// ─── Adaptive Q&A ────────────────────────────────────────────
export const adaptiveAnswer = (
  student_name: string,
  topic: string,
  concept: string,
  question: string,
  expected_answer: string,
  student_answer: string
) =>
  apiFetch<Record<string, unknown>>("/answer/adaptive", {
    method: "POST",
    body: JSON.stringify({ student_name, topic, concept, question, expected_answer, student_answer }),
  });

export const reexplain = (
  topic: string,
  concept: string,
  misconception: string,
  student_level: string,
  language: string,
  material_context = ""
) =>
  apiFetch<{
    reexplanation: string;
    analogy: string;
    visual_suggestion: string;
    visual_content: string;
    check_question: string;
  }>("/answer/reexplain", {
    method: "POST",
    body: JSON.stringify({ topic, concept, misconception, student_level, language, material_context }),
  });

// ─── Assessment ──────────────────────────────────────────────
export const generateAssessment = (
  topic: string,
  concepts_taught: string[],
  student_level: string,
  misconceptions: string[],
  weak_concepts: string[],
  material_context: string,
  language: string,
  n_questions = 5
) =>
  apiFetch<{ questions: Record<string, unknown>[] }>("/assessment/generate", {
    method: "POST",
    body: JSON.stringify({ topic, concepts_taught, student_level, misconceptions, weak_concepts, material_context, language, n_questions }),
  });

export const evaluateAssessment = (
  questions: Record<string, unknown>[],
  student_answers: Record<string, string>,
  student_level: string,
  topic: string
) =>
  apiFetch<Record<string, unknown>>("/assessment/evaluate", {
    method: "POST",
    body: JSON.stringify({ questions, student_answers, student_level, topic }),
  });

// ─── Report ──────────────────────────────────────────────────
export const generateReport = (
  student_name: string,
  topic: string,
  session_data: Record<string, unknown>,
  assessment_result?: Record<string, unknown>
) =>
  apiFetch<Record<string, unknown>>("/report/generate", {
    method: "POST",
    body: JSON.stringify({ student_name, topic, session_data, assessment_result }),
  });
