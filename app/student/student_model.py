from dataclasses import dataclass, field

from app.database.database import (
    get_or_create_student,
    load_topic_progress,
    save_topic_progress,
)


@dataclass
class StudentModel:
    name: str
    level: str = "beginner"

    # Database student ID
    student_id: int | None = None

    # Overall learning information
    mastery: dict = field(default_factory=dict)

    # Known misconceptions
    misconceptions: dict = field(default_factory=dict)

    # Learning history
    attempts: dict = field(default_factory=dict)
    correct_answers: dict = field(default_factory=dict)

    def initialize_topic(self, topic: str):
        """Create an initial record for a topic."""

        if topic not in self.mastery:
            self.mastery[topic] = 0.0

        if topic not in self.misconceptions:
            self.misconceptions[topic] = []

        if topic not in self.attempts:
            self.attempts[topic] = 0

        if topic not in self.correct_answers:
            self.correct_answers[topic] = 0

    def load_from_database(self, topic: str):
        """
        Load the student's saved progress for a topic.

        If no progress exists yet, initialize the topic
        with default values.
        """

        # Get existing student or create one.
        student = get_or_create_student(
            name=self.name,
            level=self.level,
        )

        self.student_id = student[0]

        # Keep the database version of the student's level.
        self.level = student[2]

        # Load topic progress.
        progress = load_topic_progress(
            student_id=self.student_id,
            topic=topic,
        )

        # No saved progress yet.
        if progress is None:
            self.initialize_topic(topic)
            return

        mastery, attempts, correct_answers, misconceptions = progress

        self.mastery[topic] = mastery
        self.attempts[topic] = attempts
        self.correct_answers[topic] = correct_answers

        # Convert database text back into a list.
        if misconceptions:
            self.misconceptions[topic] = [
                item.strip()
                for item in misconceptions.split("\n")
                if item.strip()
            ]
        else:
            self.misconceptions[topic] = []

    def save_to_database(self, topic: str):
        """Save the current topic progress to SQLite."""

        # Make sure student exists in database.
        if self.student_id is None:

            student = get_or_create_student(
                name=self.name,
                level=self.level,
            )

            self.student_id = student[0]

        self.initialize_topic(topic)

        save_topic_progress(
            student_id=self.student_id,
            topic=topic,
            mastery=self.mastery[topic],
            attempts=self.attempts[topic],
            correct_answers=self.correct_answers[topic],
            misconceptions=self.misconceptions[topic],
        )

    def update_from_evaluation(
        self,
        topic: str,
        correct: bool | None,
        misconception: str = "",
    ):
        """
        Update the student model after an evaluated answer.

        correct=True  -> student answered correctly
        correct=False -> student answered incorrectly
        correct=None  -> evaluation/system failure
        """

        # If the evaluator failed, don't modify learning data.
        if correct is None:
            return

        self.initialize_topic(topic)

        self.attempts[topic] += 1

        if correct:

            self.correct_answers[topic] += 1

            self.mastery[topic] = min(
                100.0,
                self.mastery[topic] + 15.0,
            )

        else:

            self.mastery[topic] = max(
                0.0,
                self.mastery[topic] - 5.0,
            )

            if misconception:

                if misconception not in self.misconceptions[topic]:

                    self.misconceptions[topic].append(
                        misconception
                    )

    def get_mastery(self, topic: str) -> float:
        """Return mastery percentage for a topic."""

        self.initialize_topic(topic)

        return self.mastery[topic]

    def get_summary(self, topic: str) -> dict:
        """Return the student's current state for a topic."""

        self.initialize_topic(topic)

        return {
            "student": self.name,
            "level": self.level,
            "topic": topic,
            "mastery": self.mastery[topic],
            "attempts": self.attempts[topic],
            "correct_answers": self.correct_answers[topic],
            "misconceptions": self.misconceptions[topic],
        }