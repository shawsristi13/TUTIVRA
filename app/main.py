from app.student.student_model import StudentModel
from app.learning.learning_session import LearningSession


def main():

    print("\n========== TUTIVRA ==========\n")

    # Create student
    student = StudentModel(
        name="Student",
        level="beginner",
    )

    topic = "Binary Search"

    # Create learning session
    session = LearningSession(
        student=student,
        topic=topic,
    )

    question = "Why does binary search require a sorted list?"

    expected_answer = (
        "Because binary search uses the sorted order "
        "to decide which half of the list can be discarded."
    )

    concept = "Why binary search requires a sorted list"

    print("Question:")
    print(question)

    student_answer = input("\nYour answer: ")

    print("\nProcessing answer...\n")

    result = session.process_answer(
        question=question,
        expected_answer=expected_answer,
        student_answer=student_answer,
        concept=concept,
    )

    evaluation = result["evaluation"]
    student_state = result["student_state"]
    adaptive_response = result["adaptive_response"]

    print("========== EVALUATION ==========\n")

    for key, value in evaluation.items():
        print(f"{key}: {value}")

    print("\n========== STUDENT MODEL ==========\n")

    print(f"Student: {student_state['student']}")
    print(f"Topic: {student_state['topic']}")
    print(f"Mastery: {student_state['mastery']}%")
    print(f"Attempts: {student_state['attempts']}")
    print(f"Correct answers: {student_state['correct_answers']}")

    print("\nMisconceptions:")

    if student_state["misconceptions"]:
        for misconception in student_state["misconceptions"]:
            print(f"- {misconception}")
    else:
        print("- None")

    if adaptive_response:

        print("\n========== TUTIVRA ADAPTS ==========\n")
        print(adaptive_response)

    else:

        print("\nTutivra believes you are ready to continue.")

    print("\n====================================\n")


if __name__ == "__main__":
    main()