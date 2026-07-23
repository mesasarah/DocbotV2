import pytest

from app.services.knowledge_graph_service import (
    ExtractionParseError,
    parse_llm_extraction,
    upsert_entities_and_relations,
)


def test_parse_valid_json():
    raw = '{"entities": [{"name": "DRDO", "type": "ORGANIZATION"}], "relations": []}'
    entities, relations = parse_llm_extraction(raw)
    assert entities == [{"name": "DRDO", "type": "ORGANIZATION"}]
    assert relations == []


def test_parse_strips_markdown_code_fences():
    raw = '```json\n{"entities": [], "relations": []}\n```'
    entities, relations = parse_llm_extraction(raw)
    assert entities == []
    assert relations == []


def test_parse_invalid_type_falls_back_to_other():
    raw = '{"entities": [{"name": "Thing", "type": "NOT_A_REAL_TYPE"}], "relations": []}'
    entities, _ = parse_llm_extraction(raw)
    assert entities[0]["type"] == "OTHER"


def test_parse_skips_entities_without_name():
    raw = '{"entities": [{"type": "PERSON"}, {"name": "Sarah", "type": "PERSON"}], "relations": []}'
    entities, _ = parse_llm_extraction(raw)
    assert len(entities) == 1
    assert entities[0]["name"] == "Sarah"


def test_parse_garbage_raises():
    with pytest.raises(ExtractionParseError):
        parse_llm_extraction("this is not json at all")


def test_parse_non_object_top_level_raises():
    with pytest.raises(ExtractionParseError):
        parse_llm_extraction("[1, 2, 3]")


def test_parse_relations_require_source_and_target():
    raw = (
        '{"entities": [], "relations": ['
        '{"source": "A", "target": "B", "label": "works with"}, '
        '{"source": "C"}'
        "]}"
    )
    _, relations = parse_llm_extraction(raw)
    assert len(relations) == 1
    assert relations[0]["label"] == "works with"


def test_upsert_dedupes_by_owner_name_type(db_session):
    entities = [{"name": "DRDO", "type": "ORGANIZATION"}, {"name": "drdo", "type": "ORGANIZATION"}]
    touched, _ = upsert_entities_and_relations(db_session, "owner-1", "doc-1", entities, [])
    # Both refer to the same entity case-insensitively -- should collapse to one row touched twice.
    assert touched == 2

    from app.models.entity import Entity

    rows = db_session.query(Entity).filter(Entity.owner_id == "owner-1").all()
    assert len(rows) == 1


def test_upsert_creates_relation_between_known_entities(db_session):
    entities = [
        {"name": "Sarah", "type": "PERSON"},
        {"name": "DOCBOT", "type": "TECHNOLOGY"},
    ]
    relations = [{"source": "Sarah", "target": "DOCBOT", "label": "built"}]

    entities_touched, relations_created = upsert_entities_and_relations(
        db_session, "owner-2", "doc-1", entities, relations
    )
    assert entities_touched == 2
    assert relations_created == 1

    from app.models.entity import EntityRelation

    rel = db_session.query(EntityRelation).filter(EntityRelation.owner_id == "owner-2").first()
    assert rel.label == "built"


def test_upsert_skips_relation_with_unknown_entity(db_session):
    entities = [{"name": "Sarah", "type": "PERSON"}]
    relations = [{"source": "Sarah", "target": "Nonexistent", "label": "knows"}]

    _, relations_created = upsert_entities_and_relations(db_session, "owner-3", "doc-1", entities, relations)
    assert relations_created == 0


def test_upsert_skips_self_referencing_relation(db_session):
    entities = [{"name": "Sarah", "type": "PERSON"}]
    relations = [{"source": "Sarah", "target": "Sarah", "label": "self"}]

    _, relations_created = upsert_entities_and_relations(db_session, "owner-4", "doc-1", entities, relations)
    assert relations_created == 0
