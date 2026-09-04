"""
TUTIVRA — Scene Planner

Converts a lesson topic + RAG context into a structured scene-by-scene
teaching plan. Each scene is a well-defined unit of teaching content
with narration, visual type, interaction points, etc.

Output schema (list of SceneDict):
  scene_id        : str  — unique ID, e.g. "scene_1"
  concept         : str  — concept being taught in this scene
  scene_type      : str  — "introduction" | "explanation" | "example"
                           | "demonstration" | "question" | "summary"
  narration       : str  — what the AI teacher says out loud
  visual_type     : str  — "equation" | "diagram" | "code" | "graph"
                           | "timeline" | "table" | "bullet_list"
                           | "comparison" | "flowchart" | "none"
  visual_content  : str  — content for the visual (LaTeX / code / text)
  on_screen_text  : str  — key point or subtitle shown on screen
  duration_seconds: int  — estimated narration duration
  interaction_required: bool — whether to pause for student input
  question        : str  — question to ask (if interaction_required)
  question_type   : str  — "mcq" | "short_answer" | "conceptual" | ""
  choices         : list — MCQ options (if question_type == "mcq")
  difficulty      : str  — "easy" | "medium" | "hard"
  language        : str  — language this scene is delivered in
"""

import json
import re
from typing import Any

from app.ai.openrouter_client import ask_ai


# ── Type alias ──────────────────────────────────────────────
SceneDict = dict[str, Any]


SYSTEM_PROMPT = """You are a professional educational curriculum designer
working with an AI teacher called Tutivra.
Your job is to break a lesson into scenes — discrete teaching moments —
each with narration text, a visual, and optionally an interactive question.
You always return valid JSON. You never add explanations outside the JSON."""


def plan_lesson_scenes(
    topic: str,
    lesson_text: str,
    student_level: str = "beginner",
    language: str = "English",
    available_time_minutes: int = 10,
    subject_area: str = "",
    learning_objective: str = "",
) -> list[SceneDict]:
    """
    Convert a lesson into a structured list of teaching scenes.

    Args:
        topic:                  Main topic to teach.
        lesson_text:            Lesson content (from teaching_engine or RAG).
        student_level:          Student's level (beginner/intermediate/advanced).
        language:               Language to teach in.
        available_time_minutes: Total session time budget.
        subject_area:           Optional subject (math, physics, history, etc.).
        learning_objective:     What the student should achieve.

    Returns:
        List of SceneDict objects representing each teaching scene.
    """

    # Estimate number of scenes from time budget
    # ~2 min per scene is a good baseline
    max_scenes = max(3, min(available_time_minutes // 2, 8))

    prompt = f"""
Create a scene-by-scene teaching plan for the following lesson.

TOPIC: {topic}
SUBJECT AREA: {subject_area or "General"}
STUDENT LEVEL: {student_level}
LANGUAGE: {language}
AVAILABLE TIME: {available_time_minutes} minutes
LEARNING OBJECTIVE: {learning_objective or f"Understand {topic}"}
MAXIMUM SCENES: {max_scenes}

LESSON CONTENT:
{lesson_text[:3000]}

Create {max_scenes} scenes that teach this topic progressively.

Each scene MUST follow this exact structure:

{{
  "scene_id": "scene_1",
  "concept": "concept name",
  "scene_type": "introduction",
  "narration": "What the AI teacher says out loud (2-4 sentences)",
  "visual_type": "bullet_list",
  "visual_content": "content for the visual",
  "on_screen_text": "Short key point shown on screen",
  "duration_seconds": 30,
  "interaction_required": false,
  "question": "",
  "question_type": "",
  "choices": [],
  "difficulty": "easy",
  "language": "{language}"
}}

Rules:
- scene_type must be one of: introduction, explanation, example, demonstration, question, summary
- visual_type must be one of: equation, diagram, code, graph, timeline, table, bullet_list, comparison, flowchart, none
- At least ONE scene must have interaction_required = true with a real question
- The LAST scene must be a summary scene with interaction_required = true
- narration should be natural spoken text (the AI teacher talks)
- visual_content should be the actual content to display (LaTeX for equations, real code for code, etc.)
- duration_seconds should be realistic (20-60 seconds per scene)
- difficulty must be appropriate for {student_level}
- For question scenes: question_type must be "mcq", "short_answer", or "conceptual"
- For MCQ: choices must have exactly 4 strings ["A. ...", "B. ...", "C. ...", "D. ..."]

Return ONLY a valid JSON array of scene objects.
Do NOT include any text before or after the JSON array.
"""

    response = ask_ai(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.4,  # Low temperature for structured output
    )

    return _parse_scenes(response, topic, language, student_level)


def _parse_scenes(
    response: str,
    topic: str,
    language: str,
    student_level: str,
) -> list[SceneDict]:
    """Parse and validate LLM response into a list of SceneDicts."""

    response = response.strip()

    # Remove markdown code fences if present
    response = re.sub(r"^```(?:json)?\s*", "", response, flags=re.IGNORECASE)
    response = re.sub(r"\s*```$", "", response)
    response = response.strip()

    # Try to parse as JSON array
    scenes_raw = None

    try:
        scenes_raw = json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON array from surrounding text
        match = re.search(r"\[[\s\S]*\]", response)
        if match:
            try:
                scenes_raw = json.loads(match.group())
            except json.JSONDecodeError:
                pass

    if not isinstance(scenes_raw, list):
        # Return a minimal fallback scene plan
        return _fallback_scenes(topic, language, student_level)

    scenes = []
    for i, raw in enumerate(scenes_raw):
        if not isinstance(raw, dict):
            continue
        scene = _validate_scene(raw, i + 1, language, student_level)
        scenes.append(scene)

    if not scenes:
        return _fallback_scenes(topic, language, student_level)

    return scenes


def _validate_scene(
    raw: dict,
    index: int,
    language: str,
    student_level: str,
) -> SceneDict:
    """Normalise and fill defaults for a scene dict."""

    VALID_SCENE_TYPES = {
        "introduction", "explanation", "example",
        "demonstration", "question", "summary",
    }
    VALID_VISUAL_TYPES = {
        "equation", "diagram", "code", "graph",
        "timeline", "table", "bullet_list",
        "comparison", "flowchart", "none",
    }
    VALID_DIFFICULTIES = {"easy", "medium", "hard"}
    VALID_QUESTION_TYPES = {"mcq", "short_answer", "conceptual", ""}

    scene_type = str(raw.get("scene_type", "explanation")).lower()
    if scene_type not in VALID_SCENE_TYPES:
        scene_type = "explanation"

    visual_type = str(raw.get("visual_type", "none")).lower()
    if visual_type not in VALID_VISUAL_TYPES:
        visual_type = "none"

    difficulty = str(raw.get("difficulty", student_level)).lower()
    if difficulty not in VALID_DIFFICULTIES:
        difficulty = "medium"

    question_type = str(raw.get("question_type", "")).lower()
    if question_type not in VALID_QUESTION_TYPES:
        question_type = "short_answer"

    interaction = bool(raw.get("interaction_required", False))
    question = str(raw.get("question", ""))
    if interaction and not question:
        question_type = ""
        interaction = False

    choices = raw.get("choices", [])
    if not isinstance(choices, list):
        choices = []

    duration = raw.get("duration_seconds", 30)
    try:
        duration = int(duration)
        duration = max(15, min(120, duration))
    except (TypeError, ValueError):
        duration = 30

    return {
        "scene_id": str(raw.get("scene_id", f"scene_{index}")),
        "concept": str(raw.get("concept", "")),
        "scene_type": scene_type,
        "narration": str(raw.get("narration", "")),
        "visual_type": visual_type,
        "visual_content": str(raw.get("visual_content", "")),
        "on_screen_text": str(raw.get("on_screen_text", "")),
        "duration_seconds": duration,
        "interaction_required": interaction,
        "question": question,
        "question_type": question_type,
        "choices": choices[:4] if choices else [],
        "difficulty": difficulty,
        "language": str(raw.get("language", language)),
    }


def _fallback_scenes(
    topic: str,
    language: str,
    student_level: str,
) -> list[SceneDict]:
    """Minimal 3-scene plan when LLM output cannot be parsed."""

    return [
        {
            "scene_id": "scene_1",
            "concept": topic,
            "scene_type": "introduction",
            "narration": (
                f"Welcome! Today we're going to learn about {topic}. "
                "Let's start with the basics."
            ),
            "visual_type": "bullet_list",
            "visual_content": f"Topic: {topic}\nLevel: {student_level}",
            "on_screen_text": f"Introduction to {topic}",
            "duration_seconds": 30,
            "interaction_required": False,
            "question": "",
            "question_type": "",
            "choices": [],
            "difficulty": "easy",
            "language": language,
        },
        {
            "scene_id": "scene_2",
            "concept": topic,
            "scene_type": "explanation",
            "narration": (
                f"Let me explain the key concepts of {topic}. "
                "Pay attention to the visual on screen."
            ),
            "visual_type": "none",
            "visual_content": "",
            "on_screen_text": f"Key Concepts: {topic}",
            "duration_seconds": 45,
            "interaction_required": False,
            "question": "",
            "question_type": "",
            "choices": [],
            "difficulty": "medium",
            "language": language,
        },
        {
            "scene_id": "scene_3",
            "concept": topic,
            "scene_type": "summary",
            "narration": (
                f"Let's check your understanding of {topic}. "
                "Please answer the following question."
            ),
            "visual_type": "none",
            "visual_content": "",
            "on_screen_text": f"Check Your Understanding",
            "duration_seconds": 30,
            "interaction_required": True,
            "question": f"Summarise what you have learnt about {topic} in your own words.",
            "question_type": "short_answer",
            "choices": [],
            "difficulty": "medium",
            "language": language,
        },
    ]
