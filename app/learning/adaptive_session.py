from app.ai.evaluator import evaluate_answer
from app.ai.question_generator import generate_question
from app.adaptation.difficulty_engine import get_adaptation_decision
from app.student.student_model import StudentModel


class AdaptiveLearningSession:

    def __init__(
        self,
        student: StudentModel,
        topic: str,
        concept: str,
        language: str = "English",
    ):
        self.student = student
        self.topic = topic
        self.concept = concept
        self.language = language

    def process_answer(
        self,
        question: str,
        expected_answer: str,
        student_answer: str,
    ):

        # ---------------------------------------------
        # 1. Evaluate student's answer
        # ---------------------------------------------

        evaluation = evaluate_answer(
            topic=self.topic,
            question=question,
            student_answer=student_answer,
            expected_answer=expected_answer,
            student_level=self.student.level,
        )

        # ---------------------------------------------
        # 2. Handle evaluator/system failure
        # ---------------------------------------------

        if evaluation.get("system_error") is True:

            return {
                "evaluation": evaluation,
                "student_state": self.student.get_summary(self.topic),
                "next_question": None,
                "adaptation": None,
            }

        # ---------------------------------------------
        # 3. Update Student Model
        # ---------------------------------------------

        self.student.update_from_evaluation(
            topic=self.topic,
            correct=evaluation.get("correct"),
            misconception=evaluation.get(
                "misconception",
                "",
            ),
        )

        # ---------------------------------------------
        # 4. Get updated student state
        # ---------------------------------------------

        student_state = self.student.get_summary(
            self.topic
        )

        # ---------------------------------------------
        # 5. Decide next difficulty
        # ---------------------------------------------

        adaptation = get_adaptation_decision(
            mastery=student_state["mastery"],
            attempts=student_state["attempts"],
            correct_answers=student_state["correct_answers"],
            misconception_detected=evaluation.get(
                "misconception_detected",
                False,
            ),
        )

        # ---------------------------------------------
        # 6. Generate next adaptive question
        # ---------------------------------------------

        next_question = generate_question(
            topic=self.topic,
            concept=self.concept,
            student_level=self.student.level,
            mastery=student_state["mastery"],
            misconceptions=student_state[
                "misconceptions"
            ],
            difficulty=adaptation["difficulty"],
            strategy=adaptation["strategy"],
            question_type=adaptation["question_type"],
        )

        # ---------------------------------------------
        # 7. Return complete adaptive result
        # ---------------------------------------------

        return {
            "evaluation": evaluation,
            "student_state": student_state,
            "adaptation": adaptation,
            "next_question": next_question,
        }