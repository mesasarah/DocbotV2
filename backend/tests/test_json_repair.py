"""
Regression tests for a real bug: local LLMs (llama3 in production use)
sometimes emit near-valid JSON -- a missing comma between array items, or
output truncated by a token limit. Strict json.loads() rejected all of it
outright. These test the json_repair fallback recovers what it can.
"""
from app.services.ai_features_service import _parse_json_response
from app.services.knowledge_graph_service import parse_llm_extraction


def test_extraction_recovers_missing_comma_between_objects():
    # This is the exact shape of malformed output seen in production.
    broken = (
        '{"entities": [{"name": "Sarah", "type": "PERSON"} '
        '{"name": "DRDO", "type": "ORGANIZATION"}], "relations": []}'
    )
    entities, relations = parse_llm_extraction(broken)
    assert len(entities) == 2
    assert entities[0]["name"] == "Sarah"
    assert entities[1]["name"] == "DRDO"


def test_extraction_recovers_truncated_output():
    # Simulates the model running out of tokens mid-generation.
    truncated = '{"entities": [{"name": "Sarah", "type": "PERSON"}, {"name": "DRDO", "type": "ORG'
    entities, _relations = parse_llm_extraction(truncated)
    assert len(entities) >= 1
    assert entities[0]["name"] == "Sarah"


def test_summary_parsing_recovers_missing_comma():
    broken = (
        '{"executive_summary": "A short summary." '
        '"bullet_points": ["point one"], "key_insights": []}'
    )
    data = _parse_json_response(broken, "summary")
    assert data["executive_summary"] == "A short summary."
    assert data["bullet_points"] == ["point one"]
