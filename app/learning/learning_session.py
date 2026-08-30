from app.ai.evaluator import evaluate_answer
from app.ai.adaptation import generate_adaptive_response
from app.student.student_model import StudentModel


class LearningSession:

    def __init__(self, student: StudentModel, topic: str):
        self.student = student
        self.topic = topic

        # Load previous progress when the session starts.
        self.student.load_from_database(self.topic)

    def process_answer(
        self,
        question: str,
        expected_answer: str,
        student_answer: str,
        concept: str,
        language: str = "English",
    ):

        # 1. Evaluate the student's answer
        evaluation = evaluate_answer(
            topic=self.topic,
            question=question,
            student_answer=student_answer,
            expected_answer=expected_answer,
            student_level=self.student.level,
        )

        # 2. Determine whether the evaluation itself failed.
        if evaluation.get("system_error") is True:

            correct = None

        else:

            correct = evaluation.get("correct")

            if not isinstance(correct, bool):
                correct = None

        # 3. Update the Student Model
        self.student.update_from_evaluation(
            topic=self.topic,
            correct=correct,
            misconception=evaluation.get(
                "misconception",
                "",
            ),
        )

        # 4. Save updated progress only if evaluation succeeded.
        if correct is not None:
            self.student.save_to_database(self.topic)

        # 5. Get updated student state
        student_state = self.student.get_summary(self.topic)

        # 6. Decide what to do next
        if correct is True:

            adaptive_response = None

        elif correct is False:

            adaptive_response = generate_adaptive_response(
                topic=self.topic,
                concept=concept,
                student_answer=student_answer,
                evaluation=evaluation,
                student_level=self.student.level,
                language=language,
            )

        else:

            adaptive_response = None

        return {
            "evaluation": evaluation,
            "student_state": student_state,
            "adaptive_response": adaptive_response,
        }