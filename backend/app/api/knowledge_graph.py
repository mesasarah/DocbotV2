from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.entity import Entity, EntityDocumentLink, EntityRelation
from app.models.user import User
from app.schemas.knowledge_graph import ExtractEntitiesResponse, GraphEdge, GraphNode, GraphResponse
from app.services.knowledge_graph_service import KnowledgeGraphError, extract_and_store_entities
from app.services.vector_store import get_document_full_text

router = APIRouter(prefix="/api/v1/knowledge-graph", tags=["knowledge-graph"])


@router.post("/documents/{document_id}/extract", response_model=ExtractEntitiesResponse)
async def extract_entities_for_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExtractEntitiesResponse:
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.owner_id == current_user.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != "indexed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be fully indexed before extracting entities.",
        )

    text = get_document_full_text(current_user.id, document_id)

    try:
        entities_found, relations_found = await extract_and_store_entities(
            db, current_user.id, document_id, text
        )
    except KnowledgeGraphError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return ExtractEntitiesResponse(
        document_id=document_id, entities_found=entities_found, relations_found=relations_found
    )


@router.get("", response_model=GraphResponse)
def get_graph(
    document_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GraphResponse:
    entities_query = db.query(Entity).filter(Entity.owner_id == current_user.id)
    if document_id:
        entities_query = entities_query.join(EntityDocumentLink).filter(
            EntityDocumentLink.document_id == document_id
        )
    entities = entities_query.all()
    entity_ids = {e.id for e in entities}

    nodes = [
        GraphNode(id=e.id, name=e.name, type=e.type, document_count=len(e.document_links))
        for e in entities
    ]

    relations_query = db.query(EntityRelation).filter(EntityRelation.owner_id == current_user.id)
    if document_id:
        relations_query = relations_query.filter(EntityRelation.document_id == document_id)
    relations = relations_query.all()

    edges = [
        GraphEdge(
            id=r.id,
            source=r.source_entity_id,
            target=r.target_entity_id,
            label=r.label,
            document_id=r.document_id,
        )
        for r in relations
        if r.source_entity_id in entity_ids and r.target_entity_id in entity_ids
    ]

    return GraphResponse(nodes=nodes, edges=edges)
