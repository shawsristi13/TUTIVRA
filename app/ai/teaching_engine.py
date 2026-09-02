from app.ai.openrouter_client import ask_ai


def create_lesson(
    topic: str,
    level: str,
    language: str,
    goal: str,
    material_context: str = "",
) -> str:
    """
    Create a personalized lesson.

    If uploaded study material is available,
    the lesson is grounded primarily in that material.
    """

    if material_context.strip():

        material_section = f"""
STUDY MATERIAL CONTEXT:
{material_context}

IMPORTANT:
- Base the lesson primarily on the uploaded study material.
- Do not contradict the provided material.
- Explain the concepts using the student's current level.
"""

    else:

        material_section = """
No uploaded study material is available.

Use reliable educational knowledge to create the lesson.
"""

    prompt = f"""
You are Tutivra, an adaptive AI teacher.

Your job is to create a personalized lesson
for one student.

Student information:

- Topic: {topic}
- Current level: {level}
- Preferred language: {language}
- Learning goal: {goal}

{material_section}

Create a structured and easy-to-understand lesson.

The lesson should contain:

## Learning Objective

Clearly explain what the student should understand.

## Concepts to Learn

List the concepts in a logical learning order.

## Explanation

Explain the concepts simply and progressively.

## Real-World Analogy

Use one useful real-world analogy.

## Example

Provide one clear example when appropriate.

## Practice Question

Give one question for the student to solve.

## Checkpoint Question

Ask one short question to verify understanding.

Important:

- Start from the student's current level.
- Do not unnecessarily introduce advanced concepts.
- Focus on conceptual understanding.
- Make the lesson interactive.
- Use clear language.
- Do not make the lesson unnecessarily long.
- The lesson should help an adaptive tutor understand
  what to teach next.
"""

    return ask_ai(prompt)