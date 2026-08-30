from app.database.database import (
    initialize_database,
    get_or_create_student,
    load_topic_progress,
    save_topic_progress,
)
from app.student.student_model import StudentModel


def main():

    print("\n========== MULTI-TOPIC TEST ==========\n")

    # Initialize database
    initialize_database()

    # Get/create student
    student_data = get_or_create_student(
        name="MultiTopicTestStudent",
        level="beginner",
    )

    student_id = student_data[0]

    # Create StudentModel
    student = StudentModel(
        name="MultiTopicTestStudent",
        level="beginner",
    )

    # -------------------------------
    # TOPIC 1: Binary Search
    # -------------------------------

    binary_search = "Binary Search"

    student.update_from_evaluation(
        topic=binary_search,
        correct=True,
    )

    student.update_from_evaluation(
        topic=binary_search,
        correct=True,
    )

    save_topic_progress(
        student_id=student_id,
        topic=binary_search,
        mastery=student.get_mastery(binary_search),
        attempts=student.attempts[binary_search],
        correct_answers=student.correct_answers[binary_search],
        misconceptions=student.misconceptions[binary_search],
    )

    # -------------------------------
    # TOPIC 2: Linked List
    # -------------------------------

    linked_list = "Linked List"

    student.update_from_evaluation(
        topic=linked_list,
        correct=True,
    )

    save_topic_progress(
        student_id=student_id,
        topic=linked_list,
        mastery=student.get_mastery(linked_list),
        attempts=student.attempts[linked_list],
        correct_answers=student.correct_answers[linked_list],
        misconceptions=student.misconceptions[linked_list],
    )

    # -------------------------------
    # LOAD BOTH TOPICS
    # -------------------------------

    binary_progress = load_topic_progress(
        student_id=student_id,
        topic=binary_search,
    )

    linked_progress = load_topic_progress(
        student_id=student_id,
        topic=linked_list,
    )

    print("Student:")
    print(student_data)

    print("\nBinary Search progress:")
    print(binary_progress)

    print("\nLinked List progress:")
    print(linked_progress)

    print("\n======================================\n")


if __name__ == "__main__":
    main()