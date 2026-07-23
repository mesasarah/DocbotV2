"""
Extracts entities and relations from a document's text using the local LLM,
then upserts them into the graph tables (deduped per user by name+type).

The LLM is asked to return strict JSON. Local models are not always
perfectly obedient about that, so parsing here is defensive: strip code
fences, bail out cleanly (empty result, logged warning) rather than raising,
so one bad extraction never breaks the document pipeline.
"""
import json
import re

import httpx
from json_repair import repair_json
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.models.entity import ENTITY_TYPES, Entity, EntityDocumentLink, EntityRelation

# Keep the prompt bounded -- local models have limited context, and a huge
# document would blow the budget for little extra extraction value.
MAX_EXTRACTION_CHARS = 8000

EXTRACTION_SYSTEM_PROMPT = (
    "You extract entities and relationships from text for a knowledge graph. "
    "Respond with ONLY valid JSON, no prose, no markdown code fences. "
    'Format: {"entities": [{"name": str, "type": one of '
    f"{list(ENTITY_TYPES)}"
    '}], "relations": [{"source": str, "target": str, "label": str}]}. '
    "Use short canonical names (e.g. 'DRDO' not 'the DRDO organization'). "
    "Keep relation labels short (2-4 words). If nothing meaningful is found, "
    'return {"entities": [], "relations": []}.'
)


class KnowledgeGraphError(Exception):
    pass


class ExtractionParseError(KnowledgeGraphError):
    pass


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_llm_extraction(raw_response: str) -> tuple[list[dict], list[dict]]:
    """Parses the LLM's JSON response into (entities, relations). Raises
    ExtractionParseError on anything unparseable -- callers decide whether
    that's fatal or just logged-and-skipped."""
    cleaned = _strip_code_fences(raw_response)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Local models frequently produce *almost* valid JSON -- a missing
        # comma between array items, or output cut short by a token limit.
        # Try to repair before giving up entirely.
        try:
            repaired = repair_json(cleaned)
            data = json.loads(repaired)
            logger.info("LLM JSON needed repair but was recovered successfully")
        except (json.JSONDecodeError, ValueError) as exc:
            raise ExtractionParseError(f"LLM did not return valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ExtractionParseError("Expected a JSON object at the top level")

    raw_entities = data.get("entities", [])
    raw_relations = data.get("relations", [])

    entities = []
    for e in raw_entities:
        if not isinstance(e, dict) or not e.get("name"):
            continue
        entity_type = e.get("type", "OTHER")
        if entity_type not in ENTITY_TYPES:
            entity_type = "OTHER"
        entities.append({"name": str(e["name"]).strip()[:255], "type": entity_type})

    relations = []
    for r in raw_relations:
        if not isinstance(r, dict) or not r.get("source") or not r.get("target"):
            continue
        relations.append(
            {
                "source": str(r["source"]).strip()[:255],
                "target": str(r["target"]).strip()[:255],
                "label": str(r.get("label", "related to")).strip()[:255],
            }
        )

    return entities, relations


async def call_llm_for_extraction(text: str, model: str | None = None) -> str:
    truncated = text[:MAX_EXTRACTION_CHARS]
    payload = {
        "model": model or settings.OLLAMA_MODEL,
        "system": EXTRACTION_SYSTEM_PROMPT,
        "prompt": f"Extract entities and relations from this text:\n\n{truncated}",
        "stream": False,
        "options": {"temperature": 0.0},
    }

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
    except httpx.ConnectError as exc:
        raise KnowledgeGraphError(
            "Local LLM (Ollama) is not reachable. Make sure Ollama is running."
        ) from exc
    except httpx.TimeoutException as exc:
        raise KnowledgeGraphError(
            f"The local LLM took longer than {settings.LLM_TIMEOUT_SECONDS}s to respond. "
            "This is common on the first request while the model loads into memory, or on "
            "a slower CPU -- try again in a moment."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise KnowledgeGraphError(f"LLM request failed: {exc.response.text}") from exc


def upsert_entities_and_relations(
    db: Session,
    owner_id: str,
    document_id: str,
    entities: list[dict],
    relations: list[dict],
) -> tuple[int, int]:
    """Upserts entities (deduped by owner+name+type, case-insensitive) and
    relations for a document. Returns (entities_upserted, relations_created)."""

    name_type_to_entity: dict[tuple[str, str], Entity] = {}

    existing = db.query(Entity).filter(Entity.owner_id == owner_id).all()
    for e in existing:
        name_type_to_entity[(e.name.lower(), e.type)] = e

    entities_touched = 0
    for e in entities:
        key = (e["name"].lower(), e["type"])
        entity = name_type_to_entity.get(key)
        if entity is None:
            entity = Entity(owner_id=owner_id, name=e["name"], type=e["type"])
            db.add(entity)
            db.flush()  # need entity.id before linking
            name_type_to_entity[key] = entity

        link_exists = (
            db.query(EntityDocumentLink)
            .filter(EntityDocumentLink.entity_id == entity.id, EntityDocumentLink.document_id == document_id)
            .first()
        )
        if link_exists is None:
            db.add(EntityDocumentLink(entity_id=entity.id, document_id=document_id))
        entities_touched += 1

    relations_created = 0
    for r in relations:
        source = _find_by_name_any_type(name_type_to_entity, r["source"])
        target = _find_by_name_any_type(name_type_to_entity, r["target"])
        if source is None or target is None or source.id == target.id:
            continue

        db.add(
            EntityRelation(
                owner_id=owner_id,
                source_entity_id=source.id,
                target_entity_id=target.id,
                document_id=document_id,
                label=r["label"],
            )
        )
        relations_created += 1

    db.commit()
    logger.info(
        "Knowledge graph updated for document {}: {} entities, {} relations",
        document_id,
        entities_touched,
        relations_created,
    )
    return entities_touched, relations_created


def _find_by_name_any_type(index: dict[tuple[str, str], Entity], name: str) -> Entity | None:
    name_lower = name.lower()
    for (n, _t), entity in index.items():
        if n == name_lower:
            return entity
    return None


async def extract_and_store_entities(db: Session, owner_id: str, document_id: str, text: str) -> tuple[int, int]:
    if not text.strip():
        return 0, 0

    raw_response = await call_llm_for_extraction(text)

    try:
        entities, relations = parse_llm_extraction(raw_response)
    except ExtractionParseError as exc:
        logger.warning("Skipping knowledge graph extraction for document {}: {}", document_id, exc)
        return 0, 0

    return upsert_entities_and_relations(db, owner_id, document_id, entities, relations)
