"""
TUTIVRA — Learning Report Generator

After a session + final assessment, generates a structured learning report
that the student and teacher can use to understand progress.

Report contains:
  - Session summary (questions, accuracy, mastery delta)
  - Concepts understood vs weak
  - Misconceptions detected
  - Recommended next topic
  - Suggested difficulty for next session
  - AI-written personalised learning recommendation
"""

from app.ai.openrouter_client import ask_ai


def generate_learning_report(
    student_name: str,
    topic: str,
    session_data: dict,
    assessment_result: dict | None = None,
    student_model_summary: dict | None = None,
) -> dict:
    """
    Generate a comprehensive learning report after a session.

    Args:
        student_name:        Student's name.
        topic:               Topic studied.
        session_data:        Dict with session stats (questions, correct, mastery, etc.)
        assessment_result:   Result from evaluate_assessment_answers() or None.
        student_model_summary: StudentModel.get_summary() result or None.

    Returns:
        {
          "student":               str,
          "topic":                 str,
          "score":                 float,   # 0–100
          "mastery_before":        float,
          "mastery_after":         float,
          "mastery_delta":         float,
          "session_questions":     int,
          "session_correct":       int,
          "session_accuracy":      float,   # 0–100
          "assessment_score":      float | None,
          "assessment_percentage": float | None,
          "concepts_understood":   list[str],
          "weak_concepts":         list[str],
          "misconceptions":        list[str],
          "recommended_next_topic":str,
          "recommended_difficulty":str,
          "personalised_message":  str,
          "revision_plan":         list[str],
          "status":                "excellent" | "good" | "needs_revision" | "repeat_lesson",
        }
    """

    # ── Extract session stats ────────────────────────────────

    questions      = session_data.get("session_questions", 0)
    correct        = session_data.get("session_correct", 0)
    mastery_before = session_data.get("mastery_before", 0.0)
    mastery_after  = session_data.get("mastery_after", 0.0)
    misconceptions = session_data.get("misconceptions", [])
    concepts_taught= session_data.get("concepts_taught", [topic])

    accuracy = (correct / questions * 100) if questions > 0 else 0.0
    mastery_delta = mastery_after - mastery_before

    # ── Extract assessment stats ─────────────────────────────

    assessment_score = None
    assessment_pct   = None
    concepts_understood = []
    weak_concepts = []

    if assessment_result:
        assessment_score = assessment_result.get("score")
        assessment_pct   = assessment_result.get("percentage")
        concepts_understood = assessment_result.get("concepts_understood", [])
        weak_concepts   = assessment_result.get("weak_concepts", [])

    # ── Compute overall score ────────────────────────────────

    if assessment_pct is not None:
        overall_score = (accuracy * 0.4 + assessment_pct * 0.6)
    else:
        overall_score = accuracy

    # ── Determine status ─────────────────────────────────────

    if overall_score >= 80:
        status = "excellent"
    elif overall_score >= 60:
        status = "good"
    elif overall_score >= 40:
        status = "needs_revision"
    else:
        status = "repeat_lesson"

    # ── Recommended difficulty ────────────────────────────────

    if overall_score >= 80:
        recommended_difficulty = "hard"
    elif overall_score >= 60:
        recommended_difficulty = "medium"
    else:
        recommended_difficulty = "easy"

    # ── Generate personalised AI message ────────────────────

    personalised_message = _generate_personalised_message(
        student_name=student_name,
        topic=topic,
        overall_score=overall_score,
        mastery_delta=mastery_delta,
        misconceptions=misconceptions,
        weak_concepts=weak_concepts,
        status=status,
    )

    # ── Revision plan ────────────────────────────────────────

    revision_plan = _build_revision_plan(
        weak_concepts=weak_concepts,
        misconceptions=misconceptions,
        topic=topic,
        status=status,
    )

    # ── Recommended next topic ────────────────────────────────

    recommended_next = _recommend_next_topic(
        topic=topic,
        status=status,
        concepts_taught=concepts_taught,
    )

    return {
        "student":               student_name,
        "topic":                 topic,
        "score":                 round(overall_score, 1),
        "mastery_before":        round(mastery_before, 1),
        "mastery_after":         round(mastery_after, 1),
        "mastery_delta":         round(mastery_delta, 1),
        "session_questions":     questions,
        "session_correct":       correct,
        "session_accuracy":      round(accuracy, 1),
        "assessment_score":      assessment_score,
        "assessment_percentage": assessment_pct,
        "concepts_understood":   concepts_understood,
        "weak_concepts":         weak_concepts,
        "misconceptions":        misconceptions,
        "recommended_next_topic":recommended_next,
        "recommended_difficulty":recommended_difficulty,
        "personalised_message":  personalised_message,
        "revision_plan":         revision_plan,
        "status":                status,
    }


# ── Internal helpers ──────────────────────────────────────────

def _generate_personalised_message(
    student_name: str,
    topic: str,
    overall_score: float,
    mastery_delta: float,
    misconceptions: list[str],
    weak_concepts: list[str],
    status: str,
) -> str:
    """Generate a short personalised learning message via LLM."""

    misconception_text = ", ".join(misconceptions[:3]) or "none"
    weak_text = ", ".join(weak_concepts[:3]) or "none"

    prompt = f"""
You are Tutivra, an encouraging AI teacher.
Write a SHORT (3-4 sentences) personalised message to {student_name} about their
learning session on "{topic}".

Performance stats:
- Overall score: {overall_score:.0f}%
- Mastery change: {mastery_delta:+.1f}%
- Status: {status}
- Misconceptions found: {misconception_text}
- Weak areas: {weak_text}

Tone: warm, encouraging, constructive. Acknowledge both strengths and areas to improve.
If score < 50%, be gentle but honest. If score >= 80%, be celebratory.
Do NOT mention internal system terms (RAG, FAISS, embeddings, etc.)
Write in second person ("You...").
Return ONLY the message text, no prefixes or labels.
"""

    try:
        return ask_ai(prompt=prompt, temperature=0.7)
    except Exception:
        # Fallback
        if status == "excellent":
            return (
                f"Outstanding work on {topic}, {student_name}! "
                f"Your score of {overall_score:.0f}% shows excellent understanding. "
                "Keep up this great momentum!"
            )
        elif status == "good":
            return (
                f"Good job on {topic}, {student_name}! "
                f"You scored {overall_score:.0f}%, which shows solid progress. "
                "Review the areas marked for improvement and you'll be ready for the next topic."
            )
        else:
            return (
                f"You've made a start on {topic}, {student_name}. "
                f"Your score is {overall_score:.0f}% this time. "
                "Don't worry — review the lesson and try again. You'll get there!"
            )


def _build_revision_plan(
    weak_concepts: list[str],
    misconceptions: list[str],
    topic: str,
    status: str,
) -> list[str]:
    """Build a practical revision plan."""

    plan = []

    if status == "excellent":
        plan.append(f"Review {topic} summary notes once more to consolidate.")
        plan.append("Move on to the next topic in your learning roadmap.")
        return plan

    if status == "repeat_lesson":
        plan.append(f"Re-watch the full {topic} teaching session from the beginning.")
        plan.append("Focus especially on the introduction and core concepts.")

    if weak_concepts:
        plan.append(
            f"Revise these specific concepts: {', '.join(weak_concepts[:3])}"
        )

    if misconceptions:
        plan.append(
            f"Correct these misconceptions: {', '.join(misconceptions[:2])}"
        )

    if status in ("needs_revision", "repeat_lesson"):
        plan.append("Complete 5 more practice questions on this topic before moving on.")

    plan.append("Ask Tutivra for an extra explanation on any concept you found difficult.")

    return plan


def _recommend_next_topic(
    topic: str,
    status: str,
    concepts_taught: list[str],
) -> str:
    """Simple rule-based next topic recommendation."""

    if status in ("needs_revision", "repeat_lesson"):
        return f"Revise {topic} (session not yet mastered)"

    # Generic suggestion based on topic keywords
    topic_lower = topic.lower()

    if "introduction" in topic_lower or "basics" in topic_lower or "fundamentals" in topic_lower:
        return f"Intermediate {topic.replace('Introduction to', '').replace('Basics of', '').strip()}"

    if "beginner" in topic_lower:
        return f"Intermediate {topic.replace('Beginner', '').strip()}"

    return f"Advanced {topic} / Next chapter"
