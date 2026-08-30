from app.ai.evaluator import evaluate_answer
from app.ai.adaptation import generate_adaptive_response
from app.student.student_model import StudentModel
from app.adaptation.difficulty_engine import get_adaptation_decision


class LearningSession:

    def __init__(self, student: StudentModel, topic: str):
        self.student = student
        self.topic = topic

    def process_answer(
        self,
        question: str,
        expected_answer: str,
        student_answer: str,
        concept: str,
        language: str = "English",
    ):

        # ---------------------------------------------
        # 1. Evaluate the student's answer
        # ---------------------------------------------

        evaluation = evaluate_answer(
            topic=self.topic,
            question=question,
            student_answer=student_answer,
            expected_answer=expected_answer,
            student_level=self.student.level,
        )

        # ---------------------------------------------
        # 2. Update the Student Model
        # ---------------------------------------------

        self.student.update_from_evaluation(
            topic=self.topic,
            correct=evaluation.get("correct"),
            misconception=evaluation.get("misconception", ""),
        )

        # ---------------------------------------------
        # 3. Get updated student state
        # ---------------------------------------------

        student_state = self.student.get_summary(self.topic)

        # ---------------------------------------------
        # 4. Check whether evaluation failed
        # ---------------------------------------------

        if evaluation.get("system_error"):

            return {
                "evaluation": evaluation,
                "student_state": student_state,
                "adaptation": None,
                "adaptive_response": None,
            }

        # ---------------------------------------------
        # 5. Decide the next difficulty
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
        # 6. Generate adaptive teaching response
        # ---------------------------------------------

        if evaluation.get("correct"):

            adaptive_response = None

        else:

            adaptive_response = generate_adaptive_response(
                topic=self.topic,
                concept=concept,
                student_answer=student_answer,
                evaluation=evaluation,
                student_level=self.student.level,
                language=language,
            )

        # ---------------------------------------------
        # 7. Return complete learning decision
        # ---------------------------------------------

        return {
            "evaluation": evaluation,
            "student_state": student_state,
            "adaptation": adaptation,
            "adaptive_response": adaptive_response,
        }