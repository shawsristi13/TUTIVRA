from app.ai.concept_extractor import extract_concepts


def create_learning_roadmap(
    material_context: str,
    topic: str = "",
) -> dict:
    """
    Create a structured learning roadmap from
    study material.

    Each concept receives independent learning
    progress that can later be used to control
    Tutivra's adaptive learning flow.
    """

    result = extract_concepts(
        material_context=material_context,
        topic=topic,
    )

    if not isinstance(
        result,
        dict,
    ):
        result = {}

    subject = result.get(
        "subject",
        topic or "Unknown Subject",
    )

    concepts = result.get(
        "concepts",
        [],
    )

    if not isinstance(
        concepts,
        list,
    ):
        concepts = []

    roadmap = []

    for index, concept in enumerate(
        concepts,
        start=1,
    ):

        # ---------------------------------------------
        # HANDLE INVALID CONCEPT DATA
        # ---------------------------------------------

        if isinstance(
            concept,
            dict,
        ):

            name = str(
                concept.get(
                    "name",
                    concept.get(
                        "concept",
                        "",
                    ),
                )
            ).strip()

            description = str(
                concept.get(
                    "description",
                    "",
                )
            ).strip()

        else:

            name = str(
                concept
            ).strip()

            description = ""

        # ---------------------------------------------
        # SKIP EMPTY CONCEPTS
        # ---------------------------------------------

        if not name:
            continue

        # ---------------------------------------------
        # CREATE CONCEPT
        # ---------------------------------------------

        roadmap.append(
            {
                "id": (
                    f"concept_{index}"
                ),

                "name": name,

                "description": description,

                "order": index,

                # Learning progress
                "mastery": 0.0,

                "attempts": 0,

                "correct_answers": 0,

                # Learning state
                "status": "not_started",

                # Future teaching support
                "lesson_completed": False,

                "question_history": [],

                "misconceptions": [],
            }
        )

    # ---------------------------------------------
    # RETURN COMPLETE ROADMAP
    # ---------------------------------------------

    return {
        "subject": subject,

        "concepts": roadmap,

        "current_concept_index": 0,

        "completed_concepts": 0,

        "roadmap_status": (
            "ready"
            if roadmap
            else "empty"
        ),
    }


def get_current_concept(
    roadmap: dict,
) -> dict | None:
    """
    Return the concept that the student should
    currently learn.
    """

    if not isinstance(
        roadmap,
        dict,
    ):
        return None

    concepts = roadmap.get(
        "concepts",
        [],
    )

    if not concepts:
        return None

    current_index = roadmap.get(
        "current_concept_index",
        0,
    )

    # ---------------------------------------------
    # FIND NEXT INCOMPLETE CONCEPT
    # ---------------------------------------------

    while current_index < len(
        concepts
    ):

        concept = concepts[
            current_index
        ]

        if (
            concept.get(
                "status"
            )
            != "completed"
        ):

            roadmap[
                "current_concept_index"
            ] = current_index

            return concept

        current_index += 1

    # ---------------------------------------------
    # ALL CONCEPTS COMPLETED
    # ---------------------------------------------

    roadmap[
        "roadmap_status"
    ] = "completed"

    return None


def update_concept_progress(
    roadmap: dict,
    correct: bool | None,
    misconception: str = "",
    mastery_threshold: float = 80.0,
    minimum_attempts: int = 2,
) -> dict:
    """
    Update progress for the current roadmap concept.

    A concept is marked as completed only when:

    - Mastery reaches the required threshold
    - The student has attempted enough questions
    """

    current_concept = get_current_concept(
        roadmap
    )

    if current_concept is None:

        return roadmap

    # ---------------------------------------------
    # UPDATE ATTEMPTS
    # ---------------------------------------------

    current_concept[
        "attempts"
    ] += 1

    # ---------------------------------------------
    # UPDATE CORRECT ANSWERS
    # ---------------------------------------------

    if correct is True:

        current_concept[
            "correct_answers"
        ] += 1

    # ---------------------------------------------
    # UPDATE MASTERY
    # ---------------------------------------------

    attempts = current_concept[
        "attempts"
    ]

    correct_answers = current_concept[
        "correct_answers"
    ]

    if attempts > 0:

        mastery = (
            correct_answers
            / attempts
        ) * 100

    else:

        mastery = 0.0

    current_concept[
        "mastery"
    ] = round(
        mastery,
        1,
    )

    # ---------------------------------------------
    # UPDATE MISCONCEPTIONS
    # ---------------------------------------------

    if misconception:

        misconceptions = (
            current_concept.get(
                "misconceptions",
                [],
            )
        )

        if misconception not in misconceptions:

            misconceptions.append(
                misconception
            )

        current_concept[
            "misconceptions"
        ] = misconceptions

    # ---------------------------------------------
    # DETERMINE STATUS
    # ---------------------------------------------

    if (
        attempts >= minimum_attempts
        and mastery >= mastery_threshold
    ):

        current_concept[
            "status"
        ] = "completed"

        roadmap[
            "completed_concepts"
        ] += 1

        roadmap[
            "current_concept_index"
        ] += 1

    else:

        current_concept[
            "status"
        ] = "in_progress"

    # ---------------------------------------------
    # CHECK ROADMAP COMPLETION
    # ---------------------------------------------

    concepts = roadmap.get(
        "concepts",
        [],
    )

    if concepts and all(
        concept.get(
            "status"
        )
        == "completed"
        for concept in concepts
    ):

        roadmap[
            "roadmap_status"
        ] = "completed"

    return roadmap


def get_roadmap_progress(
    roadmap: dict,
) -> dict:
    """
    Return summarized roadmap progress for the UI.
    """

    if not isinstance(
        roadmap,
        dict,
    ):

        return {
            "total_concepts": 0,
            "completed_concepts": 0,
            "progress_percentage": 0.0,
            "current_concept": None,
        }

    concepts = roadmap.get(
        "concepts",
        [],
    )

    total_concepts = len(
        concepts
    )

    completed_concepts = sum(
        1
        for concept in concepts
        if concept.get(
            "status"
        )
        == "completed"
    )

    progress_percentage = (
        (
            completed_concepts
            / total_concepts
        )
        * 100
        if total_concepts > 0
        else 0.0
    )

    current_concept = (
        get_current_concept(
            roadmap
        )
    )

    return {
        "total_concepts": total_concepts,

        "completed_concepts": (
            completed_concepts
        ),

        "progress_percentage": round(
            progress_percentage,
            1,
        ),

        "current_concept": (
            current_concept
        ),
    }