from app.ai.openrouter_client import ask_ai


def create_lesson(topic: str, level: str, language: str, goal: str) -> str:
    prompt = f"""
You are Tutivra, an adaptive AI teacher.

Your job is to create a personalized lesson for one student.

Student information:
- Topic: {topic}
- Current level: {level}
- Preferred language: {language}
- Learning goal: {goal}

Create a short lesson plan.

The lesson should contain:
1. Learning objective
2. Concepts to teach in order
3. A simple explanation strategy
4. One real-world analogy
5. One practice question
6. One checkpoint question

Important:
- Start from the student's current level.
- Do not unnecessarily introduce advanced concepts.
- Make the lesson interactive.
- The teacher should be able to adapt later based on the student's answers.

Return the lesson plan in clear sections.
"""

    return ask_ai(prompt)