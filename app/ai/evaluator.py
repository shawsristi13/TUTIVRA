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

Evaluate the student's answer academically.

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

Return ONLY ONE valid JSON object.

The JSON MUST use exactly these fields:

{{
  "correct": true,
  "understanding_level": "beginner",
  "misconception_detected": false,
  "misconception": "",
  "recommended_strategy": "continue",
  "feedback": "Short feedback for the student."
}}

Rules:

- correct must be either true or false.
- misconception_detected must be either true or false.
- understanding_level must be one of:
  "beginner", "intermediate", "advanced".
- recommended_strategy must be one of:
  "continue",
  "simpler_explanation",
  "give_an_example",
  "give_another_example",
  "increase_difficulty".
- If the student's answer is substantially correct, set correct to true.
- Minor wording differences must NOT make an answer incorrect.
- Evaluate the meaning of the answer, not exact wording.
- If correct is false and there is a clear conceptual misunderstanding, identify it.
- Keep feedback concise.
- Do not include markdown.
- Do not include ```json.
- Do not include any text before or after the JSON.
"""


    try:
        response = ask_ai(prompt)

    except Exception as error:

        return {
            "correct": None,
            "understanding_level": student_level,
            "misconception_detected": False,
            "misconception": "",
            "recommended_strategy": "retry_evaluation",
            "feedback": (
                "Tutivra could not connect to the AI evaluator. "
                "Please try again."
            ),
            "system_error": True,
            "error": str(error),
        }

    if not response:
        return {
            "correct": None,
            "understanding_level": student_level,
            "misconception_detected": False,
            "misconception": "",
            "recommended_strategy": "retry_evaluation",
            "feedback": "The AI evaluator returned an empty response.",
            "system_error": True,
        }

    response = response.strip()

    # Remove markdown code fences if the model accidentally adds them.
    response = re.sub(
        r"^```(?:json)?\s*",
        "",
        response,
        flags=re.IGNORECASE,
    )

    response = re.sub(
        r"\s*```$",
        "",
        response,
    )

    response = response.strip()

    # First attempt: complete response is JSON.
    try:

        result = json.loads(response)

        if not isinstance(result, dict):
            raise ValueError("AI response is not a JSON object.")

        return validate_evaluation(
            result=result,
            student_level=student_level,
        )

    except (json.JSONDecodeError, ValueError):
        pass

    # Second attempt: extract JSON object from surrounding text.
    match = re.search(
        r"\{[\s\S]*\}",
        response,
    )

    if match:

        try:

            result = json.loads(match.group())

            if not isinstance(result, dict):
                raise ValueError(
                    "Extracted response is not a JSON object."
                )

            return validate_evaluation(
                result=result,
                student_level=student_level,
            )

        except (json.JSONDecodeError, ValueError):
            pass

    # AI returned something we cannot safely interpret.
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
        "raw_response": response,
    }


def validate_evaluation(
    result: dict,
    student_level: str,
) -> dict:

    required_fields = [
        "correct",
        "understanding_level",
        "misconception_detected",
        "misconception",
        "recommended_strategy",
        "feedback",
    ]

    for field in required_fields:

        if field not in result:
            raise ValueError(
                f"Missing evaluator field: {field}"
            )

    # Validate critical boolean fields.
    if not isinstance(result["correct"], bool):
        raise ValueError(
            "Evaluator returned invalid 'correct' value."
        )

    if not isinstance(
        result["misconception_detected"],
        bool,
    ):
        raise ValueError(
            "Evaluator returned invalid "
            "'misconception_detected' value."
        )

    # Normalize optional values.
    result["misconception"] = str(
        result.get("misconception", "")
    )

    result["feedback"] = str(
        result.get("feedback", "")
    )

    result["system_error"] = False

    return result