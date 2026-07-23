import pytest

from app.services.ai_features_service import (
    AIFeatureError,
    _parse_json_response,
    _strip_code_fences,
)


def test_strip_code_fences_removes_json_fence():
    raw = '```json\n{"a": 1}\n```'
    assert _strip_code_fences(raw) == '{"a": 1}'


def test_strip_code_fences_removes_plain_fence():
    raw = '```\n{"a": 1}\n```'
    assert _strip_code_fences(raw) == '{"a": 1}'


def test_strip_code_fences_noop_when_no_fence():
    raw = '{"a": 1}'
    assert _strip_code_fences(raw) == '{"a": 1}'


def test_parse_json_response_success():
    result = _parse_json_response('{"executive_summary": "test"}', "summary")
    assert result == {"executive_summary": "test"}


def test_parse_json_response_invalid_raises():
    with pytest.raises(AIFeatureError):
        _parse_json_response("not json", "summary")


def test_parse_json_response_non_object_raises():
    with pytest.raises(AIFeatureError):
        _parse_json_response("[1, 2, 3]", "summary")


class TestGenerateQuiz:
    """Exercises the real generate_quiz function with the LLM call mocked out,
    so the actual filtering/validation logic runs end-to-end."""

    @pytest.mark.asyncio
    async def test_valid_questions_pass_through(self, monkeypatch):
        import app.services.ai_features_service as svc

        async def fake_call(system_prompt, user_prompt):
            return (
                '{"questions": [{"question": "What is DOCBOT?", '
                '"options": ["A RAG assistant", "A game", "A car", "A movie"], '
                '"correct_index": 0, "explanation": "It answers from documents."}]}'
            )

        monkeypatch.setattr(svc, "_call_ollama", fake_call)
        questions = await svc.generate_quiz("DOCBOT is an offline RAG assistant.", num_questions=1)
        assert len(questions) == 1
        assert questions[0]["correct_index"] == 0

    @pytest.mark.asyncio
    async def test_malformed_question_is_filtered_out(self, monkeypatch):
        import app.services.ai_features_service as svc

        async def fake_call(system_prompt, user_prompt):
            return (
                '{"questions": ['
                '{"question": "Bad one", "options": ["only one"], "correct_index": 0}, '
                '{"question": "Good one", "options": ["a", "b"], "correct_index": 1}'
                "]}"
            )

        monkeypatch.setattr(svc, "_call_ollama", fake_call)
        questions = await svc.generate_quiz("some text", num_questions=2)
        assert len(questions) == 1
        assert questions[0]["question"] == "Good one"

    @pytest.mark.asyncio
    async def test_out_of_range_correct_index_defaults_to_zero(self, monkeypatch):
        import app.services.ai_features_service as svc

        async def fake_call(system_prompt, user_prompt):
            return '{"questions": [{"question": "Q?", "options": ["a", "b"], "correct_index": 99}]}'

        monkeypatch.setattr(svc, "_call_ollama", fake_call)
        questions = await svc.generate_quiz("some text", num_questions=1)
        assert questions[0]["correct_index"] == 0

    @pytest.mark.asyncio
    async def test_no_usable_questions_raises(self, monkeypatch):
        import app.services.ai_features_service as svc

        async def fake_call(system_prompt, user_prompt):
            return '{"questions": []}'

        monkeypatch.setattr(svc, "_call_ollama", fake_call)
        with pytest.raises(AIFeatureError):
            await svc.generate_quiz("some text", num_questions=1)

    @pytest.mark.asyncio
    async def test_empty_document_text_raises_before_calling_llm(self, monkeypatch):
        import app.services.ai_features_service as svc

        called = False

        async def fake_call(system_prompt, user_prompt):
            nonlocal called
            called = True
            return "{}"

        monkeypatch.setattr(svc, "_call_ollama", fake_call)
        with pytest.raises(AIFeatureError):
            await svc.generate_quiz("   ", num_questions=1)
        assert called is False


class TestSummarizeText:
    @pytest.mark.asyncio
    async def test_summary_fields_extracted(self, monkeypatch):
        import app.services.ai_features_service as svc

        async def fake_call(system_prompt, user_prompt):
            return (
                '{"executive_summary": "A short summary.", '
                '"bullet_points": ["point one", "point two"], '
                '"key_insights": ["insight one"]}'
            )

        monkeypatch.setattr(svc, "_call_ollama", fake_call)
        result = await svc.summarize_text("Some document text.")
        assert result["executive_summary"] == "A short summary."
        assert result["bullet_points"] == ["point one", "point two"]
        assert result["key_insights"] == ["insight one"]

    @pytest.mark.asyncio
    async def test_empty_text_raises(self):
        import app.services.ai_features_service as svc

        with pytest.raises(AIFeatureError):
            await svc.summarize_text("")
