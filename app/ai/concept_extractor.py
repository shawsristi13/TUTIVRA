import json
import re

from app.ai.openrouter_client import ask_ai


def _extract_json(response: str) -> dict:
    """
    Extract a JSON object from the AI response.
    """

    response = response.strip()

    # Case 1: Pure JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Case 2: JSON inside a markdown block
    code_block = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        response,
        re.DOTALL | re.IGNORECASE,
    )

    if code_block:
        return json.loads(code_block.group(1))

    # Case 3: JSON surrounded by extra text
    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1 and end > start:
        return json.loads(
            response[start:end + 1]
        )

    raise json.JSONDecodeError(
        "No valid JSON object found in AI response",
        response,
        0,
    )


def extract_concepts(
    material_context: str,
    topic: str = "",
) -> dict:
    """
    Extract the main subject and important
    learning concepts from study material.

    The material_context should contain
    retrieved chunks or representative text
    from the uploaded document.
    """

    if not material_context.strip():

        return {
            "subject": topic or "Unknown Subject",
            "concepts": [],
            "error": "No study material was provided.",
        }

    prompt = f"""
You are an educational curriculum analysis system.

Analyze the provided study material and identify
the important concepts that a student should learn.

TOPIC PROVIDED BY STUDENT:
{topic if topic else "Not specified"}

STUDY MATERIAL:
{material_context}

Your task:

1. Identify the overall subject.
2. Identify the major concepts.
3. Arrange concepts in a logical learning order.
4. Include only concepts that are actually supported
   by the provided material.
5. Do not invent unrelated topics.
6. Avoid duplicate concepts.
7. Prefer broad concepts that can later contain
   smaller subtopics.

Return ONLY valid JSON.

Do not use markdown.
Do not add explanations.

Use exactly this structure:

{{
    "subject": "Name of the overall subject",
    "concepts": [
        {{
            "name": "Concept name",
            "description": "Short description of what the student should learn",
            "order": 1
        }}
    ]
}}

Important:

- Return between 3 and 12 concepts when the material
  contains enough information.
- Arrange the concepts from foundational to advanced.
- Keep descriptions concise.
"""

    response = ask_ai(prompt)

    try:

        result = _extract_json(response)

        subject = result.get(
            "subject",
            topic or "Unknown Subject",
        )

        concepts = result.get(
            "concepts",
            [],
        )

        if not isinstance(concepts, list):
            raise ValueError(
                "Concepts must be a list."
            )

        cleaned_concepts = []

        for index, concept in enumerate(
            concepts,
            start=1,
        ):

            if not isinstance(concept, dict):
                continue

            name = str(
                concept.get("name", "")
            ).strip()

            description = str(
                concept.get(
                    "description",
                    "",
                )
            ).strip()

            if not name:
                continue

            cleaned_concepts.append(
                {
                    "name": name,
                    "description": description,
                    "order": index,
                }
            )

        return {
            "subject": subject,
            "concepts": cleaned_concepts,
        }

    except (
        json.JSONDecodeError,
        ValueError,
    ) as error:

        return {
            "subject": topic or "Unknown Subject",
            "concepts": [],
            "error": (
                f"Concept extraction failed: {error}"
            ),
            "raw_response": response,
        }