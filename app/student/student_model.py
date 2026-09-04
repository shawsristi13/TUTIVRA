from dataclasses import dataclass, field

from app.database.database import (
    get_or_create_student,
    load_topic_progress,
    save_topic_progress,
    load_concept_progress,
    load_all_concept_progress,
    save_concept_progress,
)


@dataclass
class StudentModel:

    name: str

    level: str = "beginner"

    # Database student ID
    student_id: int | None = None


    # ======================================================
    # TOPIC-LEVEL LEARNING INFORMATION
    # ======================================================

    mastery: dict = field(
        default_factory=dict
    )

    misconceptions: dict = field(
        default_factory=dict
    )

    attempts: dict = field(
        default_factory=dict
    )

    correct_answers: dict = field(
        default_factory=dict
    )


    # ======================================================
    # CONCEPT-LEVEL LEARNING INFORMATION
    #
    # Structure:
    #
    # {
    #     "Binary Search": {
    #
    #         "Sorted Arrays": {
    #
    #             "mastery": 0.0,
    #             "attempts": 0,
    #             "correct_answers": 0,
    #             "misconceptions": [],
    #             "status": "not_started"
    #
    #         }
    #     }
    # }
    # ======================================================

    concept_progress: dict = field(
        default_factory=dict
    )


    # ======================================================
    # TOPIC INITIALIZATION
    # ======================================================

    def initialize_topic(
        self,
        topic: str,
    ):
        """
        Create initial tracking data
        for a topic.
        """

        if topic not in self.mastery:

            self.mastery[topic] = 0.0


        if topic not in self.misconceptions:

            self.misconceptions[topic] = []


        if topic not in self.attempts:

            self.attempts[topic] = 0


        if topic not in self.correct_answers:

            self.correct_answers[topic] = 0


        if topic not in self.concept_progress:

            self.concept_progress[topic] = {}


    # ======================================================
    # CONCEPT INITIALIZATION
    # ======================================================

    def initialize_concept(
        self,
        topic: str,
        concept: str,
    ):
        """
        Create initial tracking data
        for a learning concept.
        """

        self.initialize_topic(
            topic
        )


        if (
            concept
            not in self.concept_progress[topic]
        ):

            self.concept_progress[
                topic
            ][concept] = {

                "mastery": 0.0,

                "attempts": 0,

                "correct_answers": 0,

                "misconceptions": [],

                "status": "not_started",
            }


    # ======================================================
    # DATABASE LOADING
    # ======================================================

    def load_from_database(
        self,
        topic: str,
    ):
        """
        Load saved topic-level and
        concept-level progress.
        """

        # --------------------------------------------------
        # GET OR CREATE STUDENT
        # --------------------------------------------------

        student = get_or_create_student(
            name=self.name,
            level=self.level,
        )

        self.student_id = student[0]

        self.level = student[2]


        # --------------------------------------------------
        # LOAD TOPIC PROGRESS
        # --------------------------------------------------

        progress = load_topic_progress(
            student_id=self.student_id,
            topic=topic,
        )


        if progress is None:

            self.initialize_topic(
                topic
            )

        else:

            (
                mastery,
                attempts,
                correct_answers,
                misconceptions,
            ) = progress


            self.mastery[topic] = mastery

            self.attempts[topic] = attempts

            self.correct_answers[
                topic
            ] = correct_answers


            if misconceptions:

                self.misconceptions[
                    topic
                ] = [

                    item.strip()

                    for item in misconceptions.split(
                        "\n"
                    )

                    if item.strip()

                ]

            else:

                self.misconceptions[
                    topic
                ] = []


        # --------------------------------------------------
        # INITIALIZE CONCEPT STORAGE
        # --------------------------------------------------

        self.initialize_topic(
            topic
        )


        # --------------------------------------------------
        # LOAD ALL SAVED CONCEPTS
        # --------------------------------------------------

        saved_concepts = (
            load_all_concept_progress(
                student_id=self.student_id,
                topic=topic,
            )
        )


        for row in saved_concepts:

            (
                concept,
                mastery,
                attempts,
                correct_answers,
                misconceptions,
                status,
            ) = row


            if misconceptions:

                misconception_list = [

                    item.strip()

                    for item in misconceptions.split(
                        "\n"
                    )

                    if item.strip()

                ]

            else:

                misconception_list = []


            self.concept_progress[
                topic
            ][concept] = {

                "mastery": mastery,

                "attempts": attempts,

                "correct_answers": correct_answers,

                "misconceptions": (
                    misconception_list
                ),

                "status": status,
            }


    # ======================================================
    # SAVE TOPIC PROGRESS
    # ======================================================

    def save_to_database(
        self,
        topic: str,
    ):
        """
        Save overall topic progress
        and all concept progress.
        """

        # --------------------------------------------------
        # ENSURE STUDENT EXISTS
        # --------------------------------------------------

        if self.student_id is None:

            student = get_or_create_student(
                name=self.name,
                level=self.level,
            )

            self.student_id = student[0]


        self.initialize_topic(
            topic
        )


        # --------------------------------------------------
        # SAVE TOPIC PROGRESS
        # --------------------------------------------------

        save_topic_progress(
            student_id=self.student_id,

            topic=topic,

            mastery=self.mastery[
                topic
            ],

            attempts=self.attempts[
                topic
            ],

            correct_answers=(
                self.correct_answers[
                    topic
                ]
            ),

            misconceptions=(
                self.misconceptions[
                    topic
                ]
            ),
        )


        # --------------------------------------------------
        # SAVE ALL CONCEPT PROGRESS
        # --------------------------------------------------

        for (
            concept,
            progress,
        ) in self.concept_progress[
            topic
        ].items():

            save_concept_progress(

                student_id=self.student_id,

                topic=topic,

                concept=concept,

                mastery=progress[
                    "mastery"
                ],

                attempts=progress[
                    "attempts"
                ],

                correct_answers=progress[
                    "correct_answers"
                ],

                misconceptions=progress[
                    "misconceptions"
                ],

                status=progress[
                    "status"
                ],
            )


    # ======================================================
    # UPDATE CONCEPT PROGRESS
    # ======================================================

    def update_concept_from_evaluation(
        self,
        topic: str,
        concept: str,
        correct: bool | None,
        misconception: str = "",
    ):
        """
        Update learning progress
        for one specific concept.
        """

        if correct is None:

            return


        self.initialize_concept(
            topic,
            concept,
        )


        progress = self.concept_progress[
            topic
        ][concept]


        # --------------------------------------------------
        # UPDATE ATTEMPTS
        # --------------------------------------------------

        progress["attempts"] += 1


        # --------------------------------------------------
        # CORRECT ANSWER
        # --------------------------------------------------

        if correct:

            progress[
                "correct_answers"
            ] += 1


            progress[
                "mastery"
            ] = min(

                100.0,

                progress[
                    "mastery"
                ] + 15.0,
            )


        # --------------------------------------------------
        # INCORRECT ANSWER
        # --------------------------------------------------

        else:

            progress[
                "mastery"
            ] = max(

                0.0,

                progress[
                    "mastery"
                ] - 5.0,
            )


            if misconception:

                if (
                    misconception
                    not in progress[
                        "misconceptions"
                    ]
                ):

                    progress[
                        "misconceptions"
                    ].append(
                        misconception
                    )


        # --------------------------------------------------
        # UPDATE STATUS
        # --------------------------------------------------

        mastery = progress[
            "mastery"
        ]

        attempts = progress[
            "attempts"
        ]


        if attempts == 0:

            progress[
                "status"
            ] = "not_started"


        elif mastery >= 80:

            progress[
                "status"
            ] = "completed"


        elif mastery >= 40:

            progress[
                "status"
            ] = "in_progress"


        else:

            progress[
                "status"
            ] = "needs_practice"


    # ======================================================
    # UPDATE FROM EVALUATION
    # ======================================================

    def update_from_evaluation(
        self,
        topic: str,
        correct: bool | None,
        misconception: str = "",
        concept: str | None = None,
    ):
        """
        Update topic progress and,
        when provided, concept progress.
        """

        if correct is None:

            return


        self.initialize_topic(
            topic
        )


        # --------------------------------------------------
        # UPDATE TOPIC ATTEMPTS
        # --------------------------------------------------

        self.attempts[
            topic
        ] += 1


        # --------------------------------------------------
        # CORRECT ANSWER
        # --------------------------------------------------

        if correct:

            self.correct_answers[
                topic
            ] += 1


            self.mastery[
                topic
            ] = min(

                100.0,

                self.mastery[
                    topic
                ] + 15.0,
            )


        # --------------------------------------------------
        # INCORRECT ANSWER
        # --------------------------------------------------

        else:

            self.mastery[
                topic
            ] = max(

                0.0,

                self.mastery[
                    topic
                ] - 5.0,
            )


            if misconception:

                if (
                    misconception
                    not in self.misconceptions[
                        topic
                    ]
                ):

                    self.misconceptions[
                        topic
                    ].append(
                        misconception
                    )


        # --------------------------------------------------
        # UPDATE CONCEPT
        # --------------------------------------------------

        if concept:

            self.update_concept_from_evaluation(

                topic=topic,

                concept=concept,

                correct=correct,

                misconception=misconception,
            )


        # --------------------------------------------------
        # SAVE EVERYTHING
        # --------------------------------------------------

        self.save_to_database(
            topic
        )


    # ======================================================
    # GET CONCEPT SUMMARY
    # ======================================================

    def get_concept_summary(
        self,
        topic: str,
        concept: str,
    ) -> dict:
        """
        Return progress for
        one specific concept.
        """

        self.initialize_concept(
            topic,
            concept,
        )


        progress = self.concept_progress[
            topic
        ][concept]


        return {

            "student": self.name,

            "level": self.level,

            "topic": topic,

            "concept": concept,

            "mastery": progress[
                "mastery"
            ],

            "attempts": progress[
                "attempts"
            ],

            "correct_answers": progress[
                "correct_answers"
            ],

            "misconceptions": progress[
                "misconceptions"
            ],

            "status": progress[
                "status"
            ],
        }


    # ======================================================
    # GET ALL CONCEPT PROGRESS
    # ======================================================

    def get_all_concept_progress(
        self,
        topic: str,
    ) -> dict:
        """
        Return progress for all concepts
        in a topic.
        """

        self.initialize_topic(
            topic
        )

        return self.concept_progress[
            topic
        ]


    # ======================================================
    # TOPIC MASTERY
    # ======================================================

    def get_mastery(
        self,
        topic: str,
    ) -> float:
        """
        Return overall topic mastery.
        """

        self.initialize_topic(
            topic
        )

        return self.mastery[
            topic
        ]


    # ======================================================
    # TOPIC SUMMARY
    # ======================================================

    def get_summary(
        self,
        topic: str,
    ) -> dict:
        """
        Return complete topic-level
        learning progress.
        """

        self.initialize_topic(
            topic
        )


        return {

            "student": self.name,

            "level": self.level,

            "topic": topic,

            "mastery": self.mastery[
                topic
            ],

            "attempts": self.attempts[
                topic
            ],

            "correct_answers": (
                self.correct_answers[
                    topic
                ]
            ),

            "misconceptions": (
                self.misconceptions[
                    topic
                ]
            ),

            "concept_progress": (
                self.concept_progress[
                    topic
                ]
            ),
        }