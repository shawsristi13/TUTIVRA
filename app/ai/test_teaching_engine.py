from app.ai.teaching_engine import create_lesson


def main():

    print("\n========== TUTIVRA TEACHING ENGINE TEST ==========\n")

    lesson = create_lesson(
        topic="Binary Search",
        level="beginner",
        language="English",
        goal="Understand how binary search works and why it requires a sorted array.",
    )

    print("========== GENERATED LESSON ==========\n")
    print(lesson)

    print("\n======================================\n")


if __name__ == "__main__":
    main()