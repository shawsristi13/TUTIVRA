import json
import re

from app.ai.openrouter_client import ask_ai


def evaluate_answer(
    topic: str,
    question: str,
    student_answer: str,
    expected_answer: str,
    student_level: str,
) -> dict:

    prompt = f"""
You are Tutivra, an adaptive AI teacher.

Evaluate a student's answer.

TOPIC:
{topic}

STUDENT LEVEL:
{student_level}

QUESTION:
{question}

EXPECTED ANSWER:
{expected_answer}

STUDENT ANSWER:
{student_answer}

Analyze the answer carefully.

Determine:

1. Whether the answer is correct.
2. The student's apparent understanding level.
3. Whether there is a misconception.
4. What the misconception is, if any.
5. What teaching strategy Tutivra should use next.
6. Whether Tutivra should:
   - continue,
   - give a simpler explanation,
   - give an analogy,
   - give another example,
   - or increase difficulty.

Return ONLY valid JSON using exactly this structure:

{{
    "correct": true,
    "understanding_level": "beginner",
    "misconception_detected": false,
    "misconception": "",
    "recommended_strategy": "continue",
    "feedback": "Short feedback for the student."
}}

Rules:
- "correct" must be true or false.
- "misconception_detected" must be true or false.
- Keep feedback encouraging but precise.
- Do not reveal the expected answer unnecessarily.
- Do not add markdown outside the JSON.
"""

    response = ask_ai(prompt)

    # Remove accidental whitespace
    response = response.strip()

    # First attempt: response is already valid JSON
    try:
        result = json.loads(response)
        result["system_error"] = False
        return result

    except json.JSONDecodeError:
        pass

    # Second attempt:
    # Sometimes the model returns:
    #
    # ```json
    # { ... }
    # ```
    #
    # Extract the JSON object from the response.
    match = re.search(
        r"\{.*\}",
        response,
        re.DOTALL,
    )

    if match:
        try:
            result = json.loads(match.group())
            result["system_error"] = False
            return result

        except json.JSONDecodeError:
            pass

    # The AI evaluation failed.
    # IMPORTANT:
    # This is a system error, NOT a student misconception.
    return {
        "correct": None,
        "understanding_level": student_level,
        "misconception_detected": False,
        "misconception": "",
        "recommended_strategy": "retry_evaluation",
        "feedback": (
            "Tutivra could not reliably evaluate this answer. "
            "Please try answering again."
        ),
        "system_error": True,
    }