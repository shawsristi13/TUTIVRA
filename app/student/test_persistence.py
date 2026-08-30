from app.student.student_model import StudentModel


def main():

    print("\n========== PERSISTENCE TEST ==========\n")

    topic = "Binary Search"

    # -------------------------------
    # FIRST SESSION
    # -------------------------------

    student = StudentModel(
        name="PersistenceTestStudent",
        level="beginner",
    )

    student.load_from_database(topic)

    print("Initial state:")
    print(student.get_summary(topic))

    # Simulate a correct answer.
    student.update_from_evaluation(
        topic=topic,
        correct=True,
    )

    student.save_to_database(topic)

    print("\nAfter correct answer:")
    print(student.get_summary(topic))

    # -------------------------------
    # SECOND SESSION
    # -------------------------------

    new_student = StudentModel(
        name="PersistenceTestStudent",
        level="beginner",
    )

    new_student.load_from_database(topic)

    print("\nAfter creating a new StudentModel:")
    print(new_student.get_summary(topic))

    print("\n======================================\n")


if __name__ == "__main__":
    main()