from app.ai.openrouter_client import ask_ai


def create_lesson(
    topic: str,
    level: str,
    language: str,
    goal: str,
    material_context: str = "",
    available_time_minutes: int = 10,
    subject_area: str = "",
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

    # Time budget instruction
    if available_time_minutes <= 5:
        time_instruction = (
            f"The student has only {available_time_minutes} minutes. "
            "Cover only the single most important concept. Be very concise."
        )
    elif available_time_minutes <= 15:
        time_instruction = (
            f"The student has {available_time_minutes} minutes. "
            "Cover 2-3 key concepts with one example each. Keep it focused."
        )
    elif available_time_minutes <= 30:
        time_instruction = (
            f"The student has {available_time_minutes} minutes. "
            "Cover all main concepts with examples, analogies, and a practice question."
        )
    else:
        time_instruction = (
            f"The student has {available_time_minutes} minutes. "
            "Cover the topic deeply: explain all concepts, provide multiple examples, "
            "use analogies, include demonstrations and a thorough checkpoint."
        )

    # Subject-aware visual instruction
    subject_hint = ""
    if subject_area:
        subject_map = {
            "math": "Use mathematical notation, equations, and step-by-step solutions where appropriate.",
            "mathematics": "Use mathematical notation, equations, and step-by-step solutions where appropriate.",
            "physics": "Include formulas, diagrams, and physical processes with real-world demonstrations.",
            "chemistry": "Use chemical equations, molecular structures, and reaction processes.",
            "biology": "Describe biological structures, processes, and labeled diagrams.",
            "history": "Use timelines, key dates, events, and cause-effect relationships.",
            "programming": "Include real code examples with execution flow and output.",
            "computer science": "Include code examples, algorithms, and architecture diagrams.",
            "geography": "Reference maps, regions, and spatial relationships.",
            "economics": "Use graphs, charts, supply/demand curves, and real examples.",
        }
        sa = subject_area.lower()
        for key, hint in subject_map.items():
            if key in sa:
                subject_hint = f"\nSUBJECT-SPECIFIC GUIDANCE: {hint}"
                break
        if not subject_hint:
            subject_hint = f"\nSUBJECT AREA: {subject_area}. Use appropriate subject-specific explanations and examples."

    prompt = f"""
You are Tutivra, an adaptive AI teacher.

Your job is to create a personalized lesson
for one student.

Student information:

- Topic: {topic}
- Current level: {level}
- Preferred language: {language}
- Learning goal: {goal}
- Subject area: {subject_area or "General"}

TIME CONSTRAINT: {time_instruction}
{subject_hint}

{material_section}

Create a structured and easy-to-understand lesson.
Write the ENTIRE lesson in {language}.

The lesson should contain:

## Learning Objective

Clearly explain what the student should understand by the end of this lesson.

## Concepts to Learn

List the concepts in a logical learning order.

## Explanation

Explain the concepts simply and progressively, appropriate for a {level} student.

## Real-World Analogy

Use one useful real-world analogy that makes the concept intuitive.

## Example

Provide one clear example when appropriate.

## Practice Question

Give one question for the student to solve on their own.

## Checkpoint Question

Ask one short question to verify understanding before moving on.

Important:

- Start from the student's current level.
- Do not unnecessarily introduce advanced concepts.
- Focus on conceptual understanding.
- Use clear, {language} language throughout.
- Respect the time constraint — do not make the lesson longer than needed.
- The lesson should help an adaptive tutor understand what to teach next.
"""

    return ask_ai(prompt)