from app.student.student_model import StudentModel
from app.learning.learning_session import LearningSession
from app.adaptation.difficulty_engine import get_adaptation_decision
from app.ai.question_generator import generate_question


def main():

    print("\n========== TUTIVRA FULL ADAPTIVE LOOP ==========\n")

    # -------------------------------------------------
    # 1. Create student
    # -------------------------------------------------

    student = StudentModel(
        name="FullLoopTestStudent",
        level="beginner",
    )

    topic = "Binary Search"
    concept = "Why binary search requires a sorted list"

    # -------------------------------------------------
    # 2. Create learning session
    # -------------------------------------------------

    session = LearningSession(
        student=student,
        topic=topic,
    )

    # -------------------------------------------------
    # 3. Run a small 3-question adaptive session
    # -------------------------------------------------

    for question_number in range(1, 4):

        print(
            f"\n========== QUESTION {question_number} ==========\n"
        )

        # Get current student state
        student_state = student.get_summary(topic)

        mastery = student_state["mastery"]
        attempts = student_state["attempts"]
        correct_answers = student_state["correct_answers"]
        misconceptions = student_state["misconceptions"]

        print(f"Current Mastery: {mastery}%")
        print(f"Attempts: {attempts}")
        print(f"Correct Answers: {correct_answers}")

        # -------------------------------------------------
        # 4. Decide difficulty
        # -------------------------------------------------

        misconception_detected = len(misconceptions) > 0

        decision = get_adaptation_decision(
            mastery=mastery,
            attempts=attempts,
            correct_answers=correct_answers,
            misconception_detected=misconception_detected,
        )

        print("\n========== ADAPTATION DECISION ==========\n")

        print(f"Difficulty: {decision['difficulty']}")
        print(f"Strategy: {decision['strategy']}")
        print(f"Question Type: {decision['question_type']}")
        print(f"Reason: {decision['reason']}")

        # -------------------------------------------------
        # 5. Generate question using current state
        # -------------------------------------------------

        question_data = generate_question(
            topic=topic,
            concept=concept,
            student_level=student.level,
            mastery=mastery,
            misconceptions=misconceptions,
            difficulty=decision["difficulty"],
            strategy=decision["strategy"],
            question_type=decision["question_type"],
        )

        if question_data.get("error"):
            print("\nQuestion generation failed.")
            print(question_data["error"])
            break

        question = question_data["question"]
        expected_answer = question_data["expected_answer"]

        print("\n========== GENERATED QUESTION ==========\n")
        print(question)

        # -------------------------------------------------
        # 6. Get student's answer
        # -------------------------------------------------

        student_answer = input("\nYour answer: ")

        # -------------------------------------------------
        # 7. Evaluate + update + save
        # -------------------------------------------------

        print("\nProcessing answer...\n")

        result = session.process_answer(
            question=question,
            expected_answer=expected_answer,
            student_answer=student_answer,
            concept=concept,
        )

        evaluation = result["evaluation"]
        updated_state = result["student_state"]

        # -------------------------------------------------
        # 8. Display evaluation
        # -------------------------------------------------

        print("\n========== EVALUATION ==========\n")

        print(f"Correct: {evaluation.get('correct')}")
        print(
            f"Understanding Level: "
            f"{evaluation.get('understanding_level')}"
        )
        print(
            f"Misconception Detected: "
            f"{evaluation.get('misconception_detected')}"
        )
        print(
            f"Feedback: "
            f"{evaluation.get('feedback')}"
        )

        if evaluation.get("system_error"):
            print("\nSystem error occurred.")
            print("Student progress was NOT modified.")
            break

        # -------------------------------------------------
        # 9. Display updated student model
        # -------------------------------------------------

        print("\n========== UPDATED STUDENT MODEL ==========\n")

        print(f"Mastery: {updated_state['mastery']}%")
        print(f"Attempts: {updated_state['attempts']}")
        print(
            f"Correct Answers: "
            f"{updated_state['correct_answers']}"
        )

        print("\nMisconceptions:")

        if updated_state["misconceptions"]:

            for misconception in updated_state["misconceptions"]:
                print(f"- {misconception}")

        else:
            print("- None")

    # -------------------------------------------------
    # 10. Final session summary
    # -------------------------------------------------

    final_state = student.get_summary(topic)

    print("\n\n========== SESSION COMPLETE ==========\n")

    print(f"Student: {final_state['student']}")
    print(f"Topic: {final_state['topic']}")
    print(f"Final Mastery: {final_state['mastery']}%")
    print(f"Total Attempts: {final_state['attempts']}")
    print(
        f"Total Correct: "
        f"{final_state['correct_answers']}"
    )

    print("\n=======================================\n")


if __name__ == "__main__":
    main()