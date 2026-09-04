"""
TUTIVRA — Final Assessment Generator

After a teaching session, generates a comprehensive assessment with:
  - MCQ questions
  - Conceptual questions
  - Short answer questions
  - Problem-solving questions (subject-appropriate)

Uses the student's misconceptions and weak areas from the session
to target the assessment appropriately.
"""

import json
import re
from typing import Any

from app.ai.openrouter_client import ask_ai


SYSTEM_PROMPT = """You are Tutivra, an adaptive AI teacher conducting a final assessment.
Generate assessment questions that accurately test the student's understanding.
Always return valid JSON. Do not add any text outside the JSON."""


def generate_final_assessment(
    topic: str,
    concepts_taught: list[str],
    student_level: str,
    misconceptions: list[str],
    weak_concepts: list[str],
    material_context: str = "",
    language: str = "English",
    n_questions: int = 5,
) -> dict:
    """
    Generate a final assessment for the completed lesson/session.

    Returns:
        {
          "topic": str,
          "questions": [
            {
              "id":              int,
              "question_type":   "mcq" | "short_answer" | "conceptual" | "problem_solving",
              "question":        str,
              "choices":         list[str] | None,   # MCQ only
              "expected_answer": str,
              "concept_tested":  str,
              "difficulty":      "easy" | "medium" | "hard",
              "marks":           int,
            }
          ],
          "total_marks": int,
          "time_estimate_minutes": int,
        }
    """

    misconception_text = "\n".join(f"- {m}" for m in misconceptions) or "None recorded"
    weak_text = "\n".join(f"- {w}" for w in weak_concepts) or "None identified"
    concept_text = "\n".join(f"- {c}" for c in concepts_taught) or topic

    material_section = ""
    if material_context.strip():
        material_section = f"""
STUDY MATERIAL CONTEXT:
{material_context[:2000]}

Base questions on this material where possible.
"""

    prompt = f"""
Generate a final assessment for a student who just completed a lesson.

TOPIC: {topic}
STUDENT LEVEL: {student_level}
LANGUAGE: {language}
NUMBER OF QUESTIONS: {n_questions}

CONCEPTS TAUGHT:
{concept_text}

STUDENT MISCONCEPTIONS:
{misconception_text}

WEAK AREAS:
{weak_text}

{material_section}

Generate exactly {n_questions} assessment questions.

QUESTION TYPE DISTRIBUTION:
- 2 MCQ questions (4 choices each)
- 1 conceptual question (explain in own words)
- 1 short answer question
- 1 problem-solving question (if topic allows)

For EACH question, include questions that target the student's weak areas
and misconceptions where possible.

Return ONLY a valid JSON object:

{{
  "topic": "{topic}",
  "questions": [
    {{
      "id": 1,
      "question_type": "mcq",
      "question": "The actual question text",
      "choices": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
      "expected_answer": "B. Option 2 — because...",
      "concept_tested": "the concept this tests",
      "difficulty": "medium",
      "marks": 2
    }},
    {{
      "id": 2,
      "question_type": "short_answer",
      "question": "The actual question text",
      "choices": null,
      "expected_answer": "Key points the answer should include",
      "concept_tested": "the concept this tests",
      "difficulty": "medium",
      "marks": 3
    }}
  ],
  "total_marks": 15,
  "time_estimate_minutes": 10
}}

Rules:
- All questions must be educationally valid and answerable from the lesson
- MCQ choices must be plausible (wrong ones should be believable distractors)
- expected_answer for MCQ must include the letter AND a brief explanation
- difficulty must match {student_level} capability
- For problem_solving type, omit choices (set null)
- Do NOT return any text before or after the JSON
"""

    try:
        response = ask_ai(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.5,
        )
        return _parse_assessment(response, topic)

    except Exception as e:
        return _fallback_assessment(topic, concepts_taught, n_questions)


def evaluate_assessment_answers(
    questions: list[dict],
    student_answers: dict[int, str],
    student_level: str,
    topic: str,
) -> dict:
    """
    Evaluate all student answers in the final assessment.

    Args:
        questions:       List of question dicts from generate_final_assessment.
        student_answers: {question_id: student_answer_text}
        student_level:   Student's level.
        topic:           Topic being assessed.

    Returns:
        {
          "score": int,
          "max_score": int,
          "percentage": float,
          "question_results": [
            {
              "id":          int,
              "correct":     bool,
              "marks_earned": int,
              "feedback":    str,
              "misconception": str,
            }
          ],
          "overall_feedback": str,
          "concepts_understood": list[str],
          "weak_concepts": list[str],
          "recommended_next": str,
        }
    """

    question_results = []
    total_score = 0
    max_score = sum(q.get("marks", 1) for q in questions)

    for question in questions:
        qid = question["id"]
        student_answer = student_answers.get(qid, "").strip()
        marks = question.get("marks", 1)

        if not student_answer:
            question_results.append({
                "id": qid,
                "correct": False,
                "marks_earned": 0,
                "feedback": "No answer provided.",
                "misconception": "",
            })
            continue

        # MCQ: can evaluate without AI
        if question["question_type"] == "mcq":
            result = _evaluate_mcq(question, student_answer, marks)
        else:
            # Use AI evaluation for open-ended
            result = _evaluate_open(question, student_answer, student_level, topic, marks)

        total_score += result["marks_earned"]
        question_results.append(result)

    percentage = (total_score / max_score * 100) if max_score > 0 else 0.0

    # Identify weak concepts
    weak_concepts = [
        r_dict["id"]
        for r_dict in question_results
        if not r_dict["correct"]
    ]

    weak_concept_names = []
    for r_dict in question_results:
        if not r_dict["correct"]:
            q = next((q for q in questions if q["id"] == r_dict["id"]), None)
            if q:
                weak_concept_names.append(q.get("concept_tested", ""))

    strong_concept_names = []
    for r_dict in question_results:
        if r_dict["correct"]:
            q = next((q for q in questions if q["id"] == r_dict["id"]), None)
            if q:
                strong_concept_names.append(q.get("concept_tested", ""))

    if percentage >= 80:
        recommended_next = f"You're ready to advance! Consider studying the next topic after {topic}."
    elif percentage >= 60:
        recommended_next = f"Good effort. Review {', '.join(weak_concept_names[:2] or [topic])} and try again."
    else:
        recommended_next = f"Please revise {topic} from the beginning with focus on the basics."

    if percentage >= 80:
        overall_feedback = "Excellent work! You have a strong understanding of this topic."
    elif percentage >= 60:
        overall_feedback = "Good progress! A few concepts need more practice."
    elif percentage >= 40:
        overall_feedback = "Fair understanding. Focus on revising the weak areas identified."
    else:
        overall_feedback = "This topic needs more study. Don't worry — review and try again."

    return {
        "score": total_score,
        "max_score": max_score,
        "percentage": round(percentage, 1),
        "question_results": question_results,
        "overall_feedback": overall_feedback,
        "concepts_understood": list(set(strong_concept_names)),
        "weak_concepts": list(set(weak_concept_names)),
        "recommended_next": recommended_next,
    }


# ── Internal helpers ──────────────────────────────────────────

def _evaluate_mcq(question: dict, student_answer: str, marks: int) -> dict:
    """Evaluate MCQ without LLM."""
    expected = question.get("expected_answer", "")
    # Extract letter from expected answer (e.g., "B. Option — because...")
    expected_letter = expected[0].upper() if expected else ""
    student_letter = student_answer.strip()[0].upper() if student_answer.strip() else ""

    correct = student_letter == expected_letter if expected_letter else False
    return {
        "id": question["id"],
        "correct": correct,
        "marks_earned": marks if correct else 0,
        "feedback": (
            "Correct!" if correct
            else f"The correct answer is {expected_letter}. {expected[2:] if len(expected) > 2 else ''}"
        ),
        "misconception": "" if correct else question.get("concept_tested", ""),
    }


def _evaluate_open(
    question: dict,
    student_answer: str,
    student_level: str,
    topic: str,
    marks: int,
) -> dict:
    """Evaluate open-ended question via LLM."""

    from app.ai.evaluator import evaluate_answer

    eval_result = evaluate_answer(
        topic=topic,
        question=question["question"],
        student_answer=student_answer,
        expected_answer=question.get("expected_answer", ""),
        student_level=student_level,
    )

    if eval_result.get("system_error"):
        return {
            "id": question["id"],
            "correct": False,
            "marks_earned": marks // 2,  # Partial credit on error
            "feedback": "Could not evaluate automatically. Manual review needed.",
            "misconception": "",
        }

    correct = eval_result.get("correct", False)
    understanding = eval_result.get("understanding_level", "")

    # Partial marks for partial understanding
    if correct:
        marks_earned = marks
    elif understanding == "intermediate":
        marks_earned = marks // 2
    else:
        marks_earned = 0

    return {
        "id": question["id"],
        "correct": correct,
        "marks_earned": marks_earned,
        "feedback": eval_result.get("feedback", ""),
        "misconception": eval_result.get("misconception", ""),
    }


def _parse_assessment(response: str, topic: str) -> dict:
    """Parse LLM assessment response."""

    response = response.strip()
    response = re.sub(r"^```(?:json)?\s*", "", response, flags=re.IGNORECASE)
    response = re.sub(r"\s*```$", "", response)
    response = response.strip()

    try:
        data = json.loads(response)
        if isinstance(data, dict) and "questions" in data:
            return data
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in surrounding text
    match = re.search(r"\{[\s\S]*\}", response)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, dict) and "questions" in data:
                return data
        except json.JSONDecodeError:
            pass

    return _fallback_assessment(topic, [], 5)


def _fallback_assessment(
    topic: str,
    concepts: list[str],
    n_questions: int,
) -> dict:
    """Minimal assessment when LLM fails."""
    return {
        "topic": topic,
        "questions": [
            {
                "id": 1,
                "question_type": "short_answer",
                "question": f"Explain the main concept of {topic} in your own words.",
                "choices": None,
                "expected_answer": f"A clear explanation of {topic}'s core idea.",
                "concept_tested": topic,
                "difficulty": "medium",
                "marks": 5,
            }
        ],
        "total_marks": 5,
        "time_estimate_minutes": 5,
    }
