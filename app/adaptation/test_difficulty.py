from app.adaptation.difficulty_engine import (
    get_adaptation_decision
)


def test_decisions():

    test_cases = [
        {
            "mastery": 10,
            "attempts": 1,
            "correct_answers": 0,
            "misconception_detected": True,
        },
        {
            "mastery": 25,
            "attempts": 2,
            "correct_answers": 1,
            "misconception_detected": False,
        },
        {
            "mastery": 45,
            "attempts": 4,
            "correct_answers": 3,
            "misconception_detected": False,
        },
        {
            "mastery": 70,
            "attempts": 6,
            "correct_answers": 5,
            "misconception_detected": False,
        },
        {
            "mastery": 90,
            "attempts": 10,
            "correct_answers": 9,
            "misconception_detected": False,
        },
    ]

    for case in test_cases:

        result = get_adaptation_decision(**case)

        print("\n-----------------------------")
        print("Mastery:", case["mastery"])
        print("Misconception:",
              case["misconception_detected"])

        print("Difficulty:",
              result["difficulty"])

        print("Strategy:",
              result["strategy"])

        print("Question type:",
              result["question_type"])

        print("Reason:",
              result["reason"])


if __name__ == "__main__":
    test_decisions()