import json
import re

from app.ai.openrouter_client import ask_ai


def _extract_json(response: str) -> dict:
    """
    Extract JSON from an AI response.

    Handles:
    - Pure JSON
    - JSON inside ```json ... ```
    - Extra text surrounding JSON
    """

    response = response.strip()

    # Case 1: response is already valid JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Case 2: JSON inside markdown code block
    code_block = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        response,
        re.DOTALL | re.IGNORECASE,
    )

    if code_block:
        return json.loads(code_block.group(1))

    # Case 3: Find the first JSON object in the response
    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1 and end > start:
        return json.loads(response[start:end + 1])

    raise json.JSONDecodeError(
        "No valid JSON object found in AI response",
        response,
        0,
    )


def generate_question(
    topic: str,
    concept: str,
    student_level: str,
    mastery: float,
    misconceptions: list,
    difficulty: str,
    strategy: str,
    question_type: str,
) -> dict:

    misconception_text = (
        "\n".join(misconceptions)
        if misconceptions
        else "None"
    )

    prompt = f"""
You are Tutivra, an adaptive AI teacher.

Generate ONE educational question for the student.

TOPIC:
{topic}

CONCEPT:
{concept}

STUDENT LEVEL:
{student_level}

CURRENT MASTERY:
{mastery}%

KNOWN MISCONCEPTIONS:
{misconception_text}

DIFFICULTY:
{difficulty}

TEACHING STRATEGY:
{strategy}

QUESTION TYPE:
{question_type}

Your question must:
- Match the student's current difficulty.
- Address the given concept.
- Consider known misconceptions.
- Be appropriate for the student's level.
- Test understanding rather than memorization.
- Avoid repeating the exact same question wording.
- Be clear and unambiguous.

IMPORTANT:
Return ONLY a JSON object.
Do NOT use markdown.
Do NOT use ```json.
Do NOT add explanations before or after the JSON.

Use exactly this structure:

{{
    "question": "The generated question",
    "expected_answer": "A concise description of what a correct answer should contain",
    "concept": "{concept}",
    "difficulty": "{difficulty}",
    "question_type": "{question_type}"
}}
"""

    response = ask_ai(prompt)

    try:

        result = _extract_json(response)

        required_fields = [
            "question",
            "expected_answer",
            "concept",
            "difficulty",
            "question_type",
        ]

        for field in required_fields:
            if field not in result:
                raise ValueError(
                    f"Missing field: {field}"
                )

        # Make sure important fields are not empty.
        for field in required_fields:
            if not str(result[field]).strip():
                raise ValueError(
                    f"Empty field: {field}"
                )

        return result

    except (json.JSONDecodeError, ValueError) as error:

        return {
            "question": "",
            "expected_answer": "",
            "concept": concept,
            "difficulty": difficulty,
            "question_type": question_type,
            "error": f"Question generation failed: {error}",
            "raw_response": response,
        }