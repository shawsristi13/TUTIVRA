from app.ai.question_generator import generate_question


def main():

    print("\n========== ADAPTIVE QUESTION TEST ==========\n")

    result = generate_question(
        topic="Binary Search",
        concept="Why binary search requires a sorted list",
        student_level="beginner",
        mastery=15.0,
        misconceptions=[
            "Confuses binary search with linear search."
        ],
        difficulty="easy",
        strategy="simpler_explanation",
        question_type="conceptual",
    )

    print("Generated question:\n")

    for key, value in result.items():
        print(f"{key}: {value}")

    print("\n============================================\n")


if __name__ == "__main__":
    main()