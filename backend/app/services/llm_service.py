"""
Thin client around a locally-running Ollama server. No external API calls --
everything hits OLLAMA_BASE_URL, which defaults to localhost.
"""
import httpx

from app.core.config import settings
from app.core.logging_config import logger

SYSTEM_PROMPT = (
    "You are DOCBOT, an offline document assistant. Answer the user's question "
    "using ONLY the provided context excerpts from their uploaded documents. "
    "If the answer is not contained in the context, say clearly that the "
    "documents don't contain enough information to answer -- do not make "
    "anything up. Keep answers concise and cite which document/page each "
    "fact comes from when possible."
)


class LLMError(Exception):
    pass


def build_rag_prompt(question: str, context_chunks: list[str]) -> str:
    context_block = "\n\n---\n\n".join(
        f"[Excerpt {i + 1}]\n{chunk}" for i, chunk in enumerate(context_chunks)
    )
    return (
        f"Context excerpts from the user's documents:\n\n{context_block}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above."
    )


async def generate_answer(question: str, context_chunks: list[str], model: str | None = None) -> str:
    prompt = build_rag_prompt(question, context_chunks)
    payload = {
        "model": model or settings.OLLAMA_MODEL,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": settings.LLM_TEMPERATURE},
    }

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
    except httpx.ConnectError as exc:
        logger.error("Could not connect to Ollama at {}: {}", settings.OLLAMA_BASE_URL, exc)
        raise LLMError(
            "Local LLM (Ollama) is not reachable. Make sure Ollama is running "
            f"and the model '{settings.OLLAMA_MODEL}' is pulled."
        ) from exc
    except httpx.TimeoutException as exc:
        logger.error("Ollama timed out after {}s: {}", settings.LLM_TIMEOUT_SECONDS, exc)
        raise LLMError(
            f"The local LLM took longer than {settings.LLM_TIMEOUT_SECONDS}s to respond. "
            "This is common on the first request while the model loads into memory, or on "
            "a slower CPU -- try again in a moment."
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.error("Ollama returned an error: {}", exc)
        raise LLMError(f"LLM request failed: {exc.response.text}") from exc


async def list_available_models() -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except httpx.HTTPError as exc:
        logger.warning("Could not list Ollama models: {}", exc)
        return []
