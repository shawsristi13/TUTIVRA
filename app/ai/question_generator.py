import json

from app.ai.openrouter_client import ask_ai


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
    """
    Generate an adaptive question based on the student's
    current learning state.
    """

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

Return ONLY valid JSON using exactly this structure:

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
        result = json.loads(response)

        # Basic validation
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