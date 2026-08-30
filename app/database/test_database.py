from app.database.database import (
    initialize_database,
    get_or_create_student,
    load_topic_progress,
    save_topic_progress,
)


def main():

    print("\n========== DATABASE TEST ==========\n")

    # Create tables
    initialize_database()

    print("Database initialized successfully.")

    # Create/get student
    student = get_or_create_student(
        name="Student",
        level="beginner",
    )

    print("\nStudent:")
    print(student)

    student_id = student[0]

    # Save progress
    save_topic_progress(
        student_id=student_id,
        topic="Binary Search",
        mastery=15.0,
        attempts=1,
        correct_answers=1,
        misconceptions=[],
    )

    print("\nProgress saved.")

    # Load progress
    progress = load_topic_progress(
        student_id=student_id,
        topic="Binary Search",
    )

    print("\nLoaded progress:")
    print(progress)

    print("\n===================================\n")


if __name__ == "__main__":
    main()