from app.learning.learning_roadmap import (
    create_learning_roadmap,
)


def test_learning_roadmap_structure():

    sample_material = """
    Data structures are methods of organizing data.

    Arrays store multiple elements in contiguous
    memory locations.

    Linked lists store data using connected nodes.

    Stacks follow the Last In First Out principle.

    Queues follow the First In First Out principle.

    Trees represent hierarchical data.

    Graphs represent relationships between
    connected objects.
    """

    roadmap = create_learning_roadmap(
        material_context=sample_material,
        topic="Data Structures",
    )

    assert isinstance(
        roadmap,
        dict,
    )

    assert "subject" in roadmap

    assert "concepts" in roadmap

    assert isinstance(
        roadmap["concepts"],
        list,
    )


def test_roadmap_concept_structure():

    sample_material = """
    Arrays and linked lists are important
    data structures.
    """

    roadmap = create_learning_roadmap(
        material_context=sample_material,
        topic="Data Structures",
    )

    concepts = roadmap["concepts"]

    for concept in concepts:

        assert "id" in concept

        assert "name" in concept

        assert "description" in concept

        assert "order" in concept

        assert "mastery" in concept

        assert "attempts" in concept

        assert "correct_answers" in concept

        assert "status" in concept


def test_empty_material_returns_empty_roadmap():

    roadmap = create_learning_roadmap(
        material_context="",
        topic="Data Structures",
    )

    assert isinstance(
        roadmap,
        dict,
    )

    assert "concepts" in roadmap

    assert roadmap["concepts"] == []