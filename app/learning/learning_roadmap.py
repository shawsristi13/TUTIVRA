from app.ai.concept_extractor import extract_concepts


def create_learning_roadmap(
    material_context: str,
    topic: str = "",
) -> dict:
    """
    Create a structured learning roadmap from
    study material.

    Each concept receives an initial mastery value
    of 0.0. Later, Tutivra will update mastery
    separately for each concept.
    """

    result = extract_concepts(
        material_context=material_context,
        topic=topic,
    )

    subject = result.get(
        "subject",
        topic or "Unknown Subject",
    )

    concepts = result.get(
        "concepts",
        [],
    )

    if not isinstance(concepts, list):
        concepts = []

    roadmap = []

    for index, concept in enumerate(
        concepts,
        start=1,
    ):

        if not isinstance(concept, dict):
            continue

        name = str(
            concept.get(
                "name",
                "",
            )
        ).strip()

        description = str(
            concept.get(
                "description",
                "",
            )
        ).strip()

        if not name:
            continue

        roadmap.append(
            {
                "id": f"concept_{index}",
                "name": name,
                "description": description,
                "order": index,
                "mastery": 0.0,
                "attempts": 0,
                "correct_answers": 0,
                "status": "not_started",
            }
        )

    return {
        "subject": subject,
        "concepts": roadmap,
    }