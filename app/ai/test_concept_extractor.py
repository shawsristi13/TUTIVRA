from app.ai.concept_extractor import (
    extract_concepts,
)


def test_extract_concepts_structure():

    sample_material = """
    Data structures are methods of organizing data.

    Arrays store elements in contiguous memory locations.
    Linked lists store elements using nodes and pointers.

    Stacks follow the Last In First Out principle.
    Queues follow the First In First Out principle.

    Trees represent hierarchical relationships.
    Graphs represent relationships between connected nodes.
    """

    result = extract_concepts(
        material_context=sample_material,
        topic="Data Structures",
    )

    assert isinstance(result, dict)

    assert "subject" in result

    assert "concepts" in result

    assert isinstance(
        result["concepts"],
        list,
    )


def test_concept_extractor_empty_material():

    result = extract_concepts(
        material_context="",
        topic="Data Structures",
    )

    assert isinstance(result, dict)

    assert result["concepts"] == []