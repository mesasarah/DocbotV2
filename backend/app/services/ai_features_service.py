"""
Higher-level document intelligence features built on top of the same local
LLM used for chat: summarization and quiz generation. Both are single-shot
prompts against a (possibly truncated) document text -- no separate model
needed.
"""
import json
import re

import httpx
from json_repair import repair_json

from app.core.config import settings
from app.core.logging_config import logger

MAX_SUMMARY_INPUT_CHARS = 12000
MAX_QUIZ_INPUT_CHARS = 8000

SUMMARY_SYSTEM_PROMPT = (
    "You summarize documents. Respond with ONLY valid JSON, no prose, no "
    'markdown fences. Format: {"executive_summary": str (2-4 sentences), '
    '"bullet_points": [str, ...] (5-8 key points), "key_insights": [str, ...] '
    "(1-3 non-obvious takeaways)}."
)

QUIZ_SYSTEM_PROMPT = (
    "You write quiz questions to test understanding of a document. Respond "
    'with ONLY valid JSON, no prose, no markdown fences. Format: {"questions": '
    '[{"question": str, "options": [str, str, str, str], "correct_index": int, '
    '"explanation": str}]}. correct_index is 0-based into options. Base every '
    "question strictly on the provided text."
)


class AIFeatureError(Exception):
    pass


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": settings.OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "options": {"temperature": 0.3},
    }
    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
    except httpx.ConnectError as exc:
        raise AIFeatureError(
            "Local LLM (Ollama) is not reachable. Make sure Ollama is running."
        ) from exc
    except httpx.TimeoutException as exc:
        raise AIFeatureError(
            f"The local LLM took longer than {settings.LLM_TIMEOUT_SECONDS}s to respond. "
            "This is common on the first request while the model loads into memory, or on "
            "a slower CPU -- try again in a moment."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise AIFeatureError(f"LLM request failed: {exc.response.text}") from exc


def _parse_json_response(raw: str, feature_name: str) -> dict:
    cleaned = _strip_code_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            data = json.loads(repair_json(cleaned))
            logger.info("{} response needed JSON repair but was recovered", feature_name)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("{} response was not valid JSON: {}", feature_name, exc)
            raise AIFeatureError(
                f"The model's {feature_name} response couldn't be parsed. Try again."
            ) from exc
    if not isinstance(data, dict):
        raise AIFeatureError(f"Unexpected {feature_name} response shape.")
    return data


async def summarize_text(text: str) -> dict:
    if not text.strip():
        raise AIFeatureError("Document has no extracted text to summarize.")

    raw = await _call_ollama(SUMMARY_SYSTEM_PROMPT, text[:MAX_SUMMARY_INPUT_CHARS])
    data = _parse_json_response(raw, "summary")

    return {
        "executive_summary": str(data.get("executive_summary", "")).strip(),
        "bullet_points": [str(b).strip() for b in data.get("bullet_points", []) if str(b).strip()],
        "key_insights": [str(k).strip() for k in data.get("key_insights", []) if str(k).strip()],
    }


async def generate_quiz(text: str, num_questions: int = 5) -> list[dict]:
    if not text.strip():
        raise AIFeatureError("Document has no extracted text to quiz on.")

    prompt = f"Generate {num_questions} multiple-choice questions from this text:\n\n{text[:MAX_QUIZ_INPUT_CHARS]}"
    raw = await _call_ollama(QUIZ_SYSTEM_PROMPT, prompt)
    data = _parse_json_response(raw, "quiz")

    questions = []
    for q in data.get("questions", []):
        if not isinstance(q, dict):
            continue
        options = q.get("options", [])
        correct_index = q.get("correct_index", 0)
        if not isinstance(options, list) or len(options) < 2:
            continue
        if not isinstance(correct_index, int) or not (0 <= correct_index < len(options)):
            correct_index = 0
        questions.append(
            {
                "question": str(q.get("question", "")).strip(),
                "options": [str(o).strip() for o in options],
                "correct_index": correct_index,
                "explanation": str(q.get("explanation", "")).strip(),
            }
        )

    if not questions:
        raise AIFeatureError("The model didn't return any usable quiz questions. Try again.")

    return questions
