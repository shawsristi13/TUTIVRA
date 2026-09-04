from app.ai.evaluator import evaluate_answer
from app.ai.question_generator import generate_question

from app.adaptation.difficulty_engine import (
    get_adaptation_decision,
)

from app.student.student_model import StudentModel

from app.learning.learning_roadmap import (
    get_current_concept,
    update_concept_progress,
    get_roadmap_progress,
)


class AdaptiveLearningSession:

    def __init__(
        self,
        student: StudentModel,
        topic: str,
        concept: str,
        language: str = "English",
        learning_roadmap: dict | None = None,
    ):
        """
        Manage an adaptive learning session.

        If a learning roadmap is provided, Tutivra
        automatically selects and progresses through
        concepts in the roadmap.
        """

        self.student = student
        self.topic = topic

        self.concept = (
            concept.strip()
            if concept and concept.strip()
            else f"Core concepts of {topic}"
        )

        self.language = language

        self.learning_roadmap = (
            learning_roadmap
        )

        # ---------------------------------------------
        # SELECT FIRST ROADMAP CONCEPT
        # ---------------------------------------------

        if self.learning_roadmap:

            current_concept = (
                get_current_concept(
                    self.learning_roadmap
                )
            )

            if current_concept:

                self.concept = (
                    current_concept.get(
                        "name",
                        self.concept,
                    )
                )


    # =================================================
    # ROADMAP METHODS
    # =================================================

    def set_learning_roadmap(
        self,
        learning_roadmap: dict,
    ):
        """
        Attach or replace the learning roadmap.
        """

        self.learning_roadmap = (
            learning_roadmap
        )

        self.sync_concept_with_roadmap()


    def sync_concept_with_roadmap(self):
        """
        Update the active concept according to
        the current position in the roadmap.
        """

        if not self.learning_roadmap:

            return self.concept

        current_concept = (
            get_current_concept(
                self.learning_roadmap
            )
        )

        if current_concept:

            concept_name = (
                current_concept.get(
                    "name",
                    "",
                )
            )

            if concept_name:

                self.concept = (
                    concept_name
                )

        return self.concept


    def get_current_concept(self) -> str:
        """
        Return the currently active learning concept.
        """

        self.sync_concept_with_roadmap()

        return self.concept


    def get_current_concept_data(
        self,
    ) -> dict | None:
        """
        Return complete data for the current
        roadmap concept.
        """

        if not self.learning_roadmap:

            return None

        return get_current_concept(
            self.learning_roadmap
        )


    def get_roadmap_progress(
        self,
    ) -> dict:
        """
        Return summarized roadmap progress.
        """

        if not self.learning_roadmap:

            return {
                "total_concepts": 0,
                "completed_concepts": 0,
                "progress_percentage": 0.0,
                "current_concept": None,
            }

        return get_roadmap_progress(
            self.learning_roadmap
        )


    # =================================================
    # CONCEPT CONTROL
    # =================================================

    def set_concept(
        self,
        concept: str,
    ):
        """
        Manually change the currently active concept.
        """

        if concept and concept.strip():

            self.concept = concept.strip()


    # =================================================
    # PROCESS ANSWER
    # =================================================

    def process_answer(
        self,
        question: str,
        expected_answer: str,
        student_answer: str,
    ):
        """
        Evaluate the student's answer, update:

        - Overall student progress
        - Current concept progress
        - Adaptive difficulty

        Then generate the next question according
        to the roadmap.
        """

        # ---------------------------------------------
        # 1. SYNCHRONIZE CURRENT CONCEPT
        # ---------------------------------------------

        self.sync_concept_with_roadmap()

        concept_before_evaluation = (
            self.concept
        )


        # ---------------------------------------------
        # 2. EVALUATE STUDENT ANSWER
        # ---------------------------------------------

        evaluation = evaluate_answer(
            topic=self.topic,

            question=question,

            student_answer=student_answer,

            expected_answer=expected_answer,

            student_level=self.student.level,
        )


        # ---------------------------------------------
        # 3. HANDLE EVALUATOR FAILURE
        # ---------------------------------------------

        if evaluation.get(
            "system_error"
        ) is True:

            return {
                "evaluation": evaluation,

                "student_state": (
                    self.student.get_summary(
                        self.topic
                    )
                ),

                "current_concept": (
                    concept_before_evaluation
                ),

                "roadmap_progress": (
                    self.get_roadmap_progress()
                ),

                "concept_completed": False,

                "next_question": None,

                "adaptation": None,
            }


        # ---------------------------------------------
        # 4. UPDATE OVERALL STUDENT MODEL
        # ---------------------------------------------

        self.student.update_from_evaluation(
            topic=self.topic,
            correct=evaluation.get("correct"),
            misconception=evaluation.get(
                "misconception",
                "",
            ),
            concept=self.concept,
        )


        # ---------------------------------------------
        # 5. UPDATE ROADMAP CONCEPT PROGRESS
        # ---------------------------------------------

        concept_completed = False

        if self.learning_roadmap:

            current_concept_data = (
                self.get_current_concept_data()
            )

            if current_concept_data:

                old_status = (
                    current_concept_data.get(
                        "status",
                        "not_started",
                    )
                )

                update_concept_progress(
                    roadmap=self.learning_roadmap,

                    correct=evaluation.get(
                        "correct"
                    ),

                    misconception=evaluation.get(
                        "misconception",
                        "",
                    ),
                )

                # Check whether the concept was
                # completed after this answer.

                if (
                    old_status != "completed"
                    and current_concept_data.get(
                        "status"
                    )
                    == "completed"
                ):

                    concept_completed = True


        # ---------------------------------------------
        # 6. GET UPDATED STUDENT STATE
        # ---------------------------------------------

        student_state = (
            self.student.get_summary(
                self.topic
            )
        )


        # ---------------------------------------------
        # 7. UPDATE CURRENT CONCEPT
        # ---------------------------------------------

        self.sync_concept_with_roadmap()

        current_concept = (
            self.concept
        )


        # ---------------------------------------------
        # 8. GET CURRENT CONCEPT DATA
        # ---------------------------------------------

        current_concept_data = (
            self.get_current_concept_data()
        )


        # ---------------------------------------------
        # 9. CHECK ROADMAP COMPLETION
        # ---------------------------------------------

        roadmap_progress = (
            self.get_roadmap_progress()
        )

        roadmap_completed = False

        if self.learning_roadmap:

            roadmap_completed = (
                self.learning_roadmap.get(
                    "roadmap_status"
                )
                == "completed"
            )


        # ---------------------------------------------
        # 10. ADAPT QUESTION DIFFICULTY
        # ---------------------------------------------

        if current_concept_data:

            concept_mastery = (
                current_concept_data.get(
                    "mastery",
                    0.0,
                )
            )

            concept_attempts = (
                current_concept_data.get(
                    "attempts",
                    0,
                )
            )

            concept_correct = (
                current_concept_data.get(
                    "correct_answers",
                    0,
                )
            )

        else:

            concept_mastery = (
                student_state[
                    "mastery"
                ]
            )

            concept_attempts = (
                student_state[
                    "attempts"
                ]
            )

            concept_correct = (
                student_state[
                    "correct_answers"
                ]
            )


        adaptation = (
            get_adaptation_decision(
                mastery=concept_mastery,

                attempts=concept_attempts,

                correct_answers=concept_correct,

                misconception_detected=(
                    evaluation.get(
                        "misconception_detected",
                        False,
                    )
                ),
            )
        )


        # ---------------------------------------------
        # 11. HANDLE COMPLETE ROADMAP
        # ---------------------------------------------

        if roadmap_completed:

            return {
                "evaluation": evaluation,

                "student_state": student_state,

                "current_concept": (
                    concept_before_evaluation
                ),

                "roadmap_progress": (
                    roadmap_progress
                ),

                "concept_completed": (
                    concept_completed
                ),

                "roadmap_completed": True,

                "adaptation": adaptation,

                "next_question": None,
            }


        # ---------------------------------------------
        # 12. GET CONCEPT-SPECIFIC MISCONCEPTIONS
        # ---------------------------------------------

        if current_concept_data:

            concept_misconceptions = (
                current_concept_data.get(
                    "misconceptions",
                    [],
                )
            )

        else:

            concept_misconceptions = (
                student_state.get(
                    "misconceptions",
                    [],
                )
            )


        # ---------------------------------------------
        # 13. GENERATE NEXT QUESTION
        # ---------------------------------------------

        next_question = generate_question(
            topic=self.topic,

            concept=current_concept,

            student_level=self.student.level,

            mastery=concept_mastery,

            misconceptions=(
                concept_misconceptions
            ),

            difficulty=adaptation[
                "difficulty"
            ],

            strategy=adaptation[
                "strategy"
            ],

            question_type=adaptation[
                "question_type"
            ],
        )


        # ---------------------------------------------
        # 14. RETURN COMPLETE RESULT
        # ---------------------------------------------

        return {
            "evaluation": evaluation,

            "student_state": student_state,

            "current_concept": (
                current_concept
            ),

            "previous_concept": (
                concept_before_evaluation
            ),

            "roadmap_progress": (
                roadmap_progress
            ),

            "concept_completed": (
                concept_completed
            ),

            "roadmap_completed": False,

            "adaptation": adaptation,

            "next_question": next_question,
        }