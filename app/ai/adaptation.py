from app.ai.openrouter_client import ask_ai


def generate_adaptive_response(
    topic: str,
    concept: str,
    student_answer: str,
    evaluation: dict,
    student_level: str,
    language: str,
) -> str:

    misconception = evaluation.get("misconception", "")
    strategy = evaluation.get("recommended_strategy", "")
    feedback = evaluation.get("feedback", "")

    prompt = f"""
You are Tutivra, an adaptive AI teacher.

Your job is to respond to a student AFTER their answer has been evaluated.

TOPIC:
{topic}

CONCEPT:
{concept}

STUDENT LEVEL:
{student_level}

LANGUAGE:
{language}

STUDENT ANSWER:
{student_answer}

EVALUATION:
{feedback}

MISCONCEPTION:
{misconception}

RECOMMENDED TEACHING STRATEGY:
{strategy}

Adapt your teaching based on the evaluation.

Rules:

1. Do NOT simply repeat the previous explanation.
2. Directly address the student's misconception.
3. Use the recommended teaching strategy.
4. If an analogy is recommended, create a simple analogy.
5. If the student is confused, simplify the concept.
6. Give one small example.
7. End with ONE new question that checks whether the student now understands.
8. Keep the explanation appropriate for the student's level.
9. Respond in the requested language.

Return the response in this structure:

FEEDBACK:
<short feedback>

RE-EXPLANATION:
<adaptive explanation>

EXAMPLE:
<simple example>

CHECK QUESTION:
<one question>
"""

    return ask_ai(prompt)