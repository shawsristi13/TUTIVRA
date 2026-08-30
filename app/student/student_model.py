from dataclasses import dataclass, field


@dataclass
class StudentModel:
    name: str
    level: str = "beginner"

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

        # If the evaluator failed, do NOT modify
        # the student's learning data.
        if correct is None:
            return

        self.initialize_topic(topic)

        self.attempts[topic] += 1

        if correct:

            # Student answered correctly.
            self.correct_answers[topic] += 1

            # Increase mastery.
            self.mastery[topic] = min(
                100.0,
                self.mastery[topic] + 15.0,
            )

        else:

            # Student answered incorrectly.
            self.mastery[topic] = max(
                0.0,
                self.mastery[topic] - 5.0,
            )

            # Store the misconception.
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