from app.student.student_model import StudentModel
from app.adaptation.difficulty_engine import get_adaptation_decision
from app.ai.question_generator import generate_question
from app.ai.evaluator import evaluate_answer


def main():

    print("\n========== TUTIVRA ADAPTIVE SESSION ==========\n")

    # -------------------------------------------------
    # 1. Create student
    # -------------------------------------------------

    student = StudentModel(
        name="AdaptiveTestStudent",
        level="beginner",
    )

    topic = "Binary Search"

    student.initialize_topic(topic)

    # -------------------------------------------------
    # 2. Get current student state
    # -------------------------------------------------

    mastery = student.get_mastery(topic)
    attempts = student.attempts[topic]
    correct_answers = student.correct_answers[topic]
    misconceptions = student.misconceptions[topic]

    print("Current Student State:")
    print(f"Mastery: {mastery}%")
    print(f"Attempts: {attempts}")
    print(f"Correct Answers: {correct_answers}")

    # -------------------------------------------------
    # 3. Decide difficulty
    # -------------------------------------------------

    decision = get_adaptation_decision(
        mastery=mastery,
        attempts=attempts,
        correct_answers=correct_answers,
        misconception_detected=False,
    )

    print("\n========== ADAPTATION DECISION ==========\n")

    print(f"Difficulty: {decision['difficulty']}")
    print(f"Strategy: {decision['strategy']}")
    print(f"Question Type: {decision['question_type']}")

    # -------------------------------------------------
    # 4. Generate adaptive question
    # -------------------------------------------------

    question_data = generate_question(
        topic=topic,
        concept="Why binary search requires a sorted list",
        student_level=student.level,
        mastery=mastery,
        misconceptions=misconceptions,
        difficulty=decision["difficulty"],
        strategy=decision["strategy"],
        question_type=decision["question_type"],
    )

    question = question_data["question"]
    expected_answer = question_data["expected_answer"]
    concept = question_data["concept"]

    print("\n========== GENERATED QUESTION ==========\n")

    print(question)

    # -------------------------------------------------
    # 5. Get student answer
    # -------------------------------------------------

    student_answer = input("\nYour answer: ")

    print("\nProcessing answer...\n")

    # -------------------------------------------------
    # 6. Evaluate answer using AI
    # -------------------------------------------------

    evaluation = evaluate_answer(
        topic=topic,
        question=question,
        student_answer=student_answer,
        expected_answer=expected_answer,
        student_level=student.level,
    )

    print("========== EVALUATION ==========\n")

    for key, value in evaluation.items():
        print(f"{key}: {value}")

    # -------------------------------------------------
    # 7. Update Student Model
    # -------------------------------------------------

    correct = evaluation.get("correct")

    # Important:
    # None means evaluator/system failure.
    # Do not count it as a wrong answer.

    student.update_from_evaluation(
        topic=topic,
        correct=correct,
        misconception=evaluation.get(
            "misconception",
            "",
        ),
    )

    # -------------------------------------------------
    # 8. Show updated student state
    # -------------------------------------------------

    student_state = student.get_summary(topic)

    print("\n========== UPDATED STUDENT MODEL ==========\n")

    print(f"Student: {student_state['student']}")
    print(f"Topic: {student_state['topic']}")
    print(f"Mastery: {student_state['mastery']}%")
    print(f"Attempts: {student_state['attempts']}")
    print(f"Correct Answers: {student_state['correct_answers']}")

    print("\nMisconceptions:")

    if student_state["misconceptions"]:
        for misconception in student_state["misconceptions"]:
            print(f"- {misconception}")
    else:
        print("- None")

    # -------------------------------------------------
    # 9. Decide what Tutivra should do next
    # -------------------------------------------------

    misconception_detected = evaluation.get(
        "misconception_detected",
        False,
    )

    next_decision = get_adaptation_decision(
        mastery=student_state["mastery"],
        attempts=student_state["attempts"],
        correct_answers=student_state["correct_answers"],
        misconception_detected=misconception_detected,
    )

    print("\n========== NEXT ADAPTATION ==========\n")

    print(f"Difficulty: {next_decision['difficulty']}")
    print(f"Strategy: {next_decision['strategy']}")
    print(f"Question Type: {next_decision['question_type']}")
    print(f"Reason: {next_decision['reason']}")

    print("\n============================================\n")


if __name__ == "__main__":
    main()