"""
Regression tests for a real bug: httpx.ReadTimeout (Ollama taking too long)
was not being caught anywhere, so a slow LLM response crashed as a raw,
unhandled 500 instead of a clean error. Covers all three call sites that
talk to Ollama.
"""
import httpx
import pytest

from app.services.ai_features_service import AIFeatureError, summarize_text
from app.services.knowledge_graph_service import KnowledgeGraphError, call_llm_for_extraction
from app.services.llm_service import LLMError, generate_answer


@pytest.mark.asyncio
async def test_chat_generate_answer_handles_timeout(monkeypatch):
    async def raise_timeout(*args, **kwargs):
        raise httpx.ReadTimeout("simulated slow LLM")

    monkeypatch.setattr(httpx.AsyncClient, "post", raise_timeout)

    with pytest.raises(LLMError, match="took longer than"):
        await generate_answer("question", ["some context"])


@pytest.mark.asyncio
async def test_summarize_handles_timeout(monkeypatch):
    async def raise_timeout(*args, **kwargs):
        raise httpx.ReadTimeout("simulated slow LLM")

    monkeypatch.setattr(httpx.AsyncClient, "post", raise_timeout)

    with pytest.raises(AIFeatureError, match="took longer than"):
        await summarize_text("some document text")


@pytest.mark.asyncio
async def test_knowledge_graph_extraction_handles_timeout(monkeypatch):
    async def raise_timeout(*args, **kwargs):
        raise httpx.ReadTimeout("simulated slow LLM")

    monkeypatch.setattr(httpx.AsyncClient, "post", raise_timeout)

    with pytest.raises(KnowledgeGraphError, match="took longer than"):
        await call_llm_for_extraction("some document text")
