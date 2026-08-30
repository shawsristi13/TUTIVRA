from dataclasses import dataclass


@dataclass
class AdaptationDecision:
    difficulty: str
    strategy: str
    question_type: str
    reason: str


class DifficultyEngine:

    def decide(
        self,
        mastery: float,
        attempts: int,
        correct_answers: int,
        misconception_detected: bool = False,
    ) -> AdaptationDecision:

        # -------------------------------------------------
        # 1. Handle misconceptions first
        # -------------------------------------------------

        if misconception_detected:

            return AdaptationDecision(
                difficulty="easy",
                strategy="simpler_explanation",
                question_type="conceptual",
                reason=(
                    "A misconception was detected, so Tutivra "
                    "should reinforce the basic concept before "
                    "increasing difficulty."
                ),
            )

        # -------------------------------------------------
        # 2. Beginner / low mastery
        # -------------------------------------------------

        if mastery < 30:

            return AdaptationDecision(
                difficulty="easy",
                strategy="give_an_example",
                question_type="conceptual",
                reason=(
                    "The student's mastery is below 30%, "
                    "so Tutivra should strengthen the fundamentals."
                ),
            )

        # -------------------------------------------------
        # 3. Developing understanding
        # -------------------------------------------------

        if mastery < 60:

            return AdaptationDecision(
                difficulty="medium",
                strategy="continue",
                question_type="application",
                reason=(
                    "The student has basic understanding and "
                    "can move to moderate application questions."
                ),
            )

        # -------------------------------------------------
        # 4. Strong understanding
        # -------------------------------------------------

        if mastery < 80:

            return AdaptationDecision(
                difficulty="hard",
                strategy="increase_difficulty",
                question_type="problem_solving",
                reason=(
                    "The student's mastery is strong enough "
                    "for more challenging problems."
                ),
            )

        # -------------------------------------------------
        # 5. High mastery
        # -------------------------------------------------

        return AdaptationDecision(
            difficulty="advanced",
            strategy="increase_difficulty",
            question_type="coding_or_real_world",
            reason=(
                "The student demonstrates high mastery, "
                "so Tutivra should provide advanced "
                "application or coding tasks."
            ),
        )


def get_adaptation_decision(
    mastery: float,
    attempts: int,
    correct_answers: int,
    misconception_detected: bool = False,
) -> dict:

    engine = DifficultyEngine()

    decision = engine.decide(
        mastery=mastery,
        attempts=attempts,
        correct_answers=correct_answers,
        misconception_detected=misconception_detected,
    )

    return {
        "difficulty": decision.difficulty,
        "strategy": decision.strategy,
        "question_type": decision.question_type,
        "reason": decision.reason,
    }