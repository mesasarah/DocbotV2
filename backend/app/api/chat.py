import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.logging_config import logger
from app.db.session import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.query_log import QueryLog
from app.models.user import User
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageRead,
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSessionRead,
    SourceSnippet,
)
from app.services.llm_service import LLMError, generate_answer
from app.services.vector_store import semantic_search

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/query", response_model=ChatQueryResponse)
async def query(
    payload: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatQueryResponse:
    # Resolve or create the chat session
    if payload.session_id:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == payload.session_id, ChatSession.owner_id == current_user.id)
            .first()
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    else:
        session = ChatSession(owner_id=current_user.id, title=payload.message[:60])
        db.add(session)
        db.commit()
        db.refresh(session)

    # Retrieve relevant chunks
    retrieved = semantic_search(
        owner_id=current_user.id,
        query=payload.message,
        document_ids=payload.document_ids,
    )

    if not retrieved:
        answer_text = (
            "I couldn't find any relevant information in your uploaded documents "
            "to answer that. Try uploading a document first, or rephrase your question."
        )
        sources: list[SourceSnippet] = []
        confidence = 0.0
    else:
        context_texts = [r.text for r in retrieved]
        try:
            answer_text = await generate_answer(payload.message, context_texts)
        except LLMError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

        sources = [
            SourceSnippet(
                document_id=r.document_id,
                filename=r.filename,
                page=r.page_number,
                snippet=r.text[:300],
                score=r.score,
            )
            for r in retrieved
        ]
        confidence = round(sum(r.score for r in retrieved) / len(retrieved), 4)

    # Persist both turns
    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.message, sources_json="[]")
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer_text,
        sources_json=json.dumps([s.model_dump() for s in sources]),
    )
    db.add_all([user_msg, assistant_msg])

    db.add(
        QueryLog(
            owner_id=current_user.id,
            query_text=payload.message[:2000],
            result_count=len(sources),
            confidence=confidence,
        )
    )

    db.commit()

    logger.info("Chat query answered for user {} (session {})", current_user.email, session.id)

    return ChatQueryResponse(session_id=session.id, answer=answer_text, sources=sources, confidence=confidence)


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatSessionRead]:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.owner_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [ChatSessionRead.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.owner_id == current_user.id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    return ChatHistoryResponse(
        session=ChatSessionRead.model_validate(session),
        messages=[ChatMessageRead.model_validate(m) for m in session.messages],
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.owner_id == current_user.id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    db.delete(session)
    db.commit()
