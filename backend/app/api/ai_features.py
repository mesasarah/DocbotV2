from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.ai_features import QuizResponse, SummaryResponse
from app.services.ai_features_service import AIFeatureError, generate_quiz, summarize_text
from app.services.vector_store import get_document_full_text

router = APIRouter(prefix="/api/v1/documents", tags=["ai-features"])


def _get_owned_indexed_document(db: Session, document_id: str, owner_id: str) -> Document:
    document = db.query(Document).filter(Document.id == document_id, Document.owner_id == owner_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != "indexed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be fully indexed before using this feature.",
        )
    return document


@router.post("/{document_id}/summarize", response_model=SummaryResponse)
async def summarize_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SummaryResponse:
    _get_owned_indexed_document(db, document_id, current_user.id)
    text = get_document_full_text(current_user.id, document_id)

    try:
        result = await summarize_text(text)
    except AIFeatureError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return SummaryResponse(document_id=document_id, **result)


@router.post("/{document_id}/quiz", response_model=QuizResponse)
async def quiz_document(
    document_id: str,
    num_questions: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizResponse:
    if not (1 <= num_questions <= 15):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="num_questions must be between 1 and 15")

    _get_owned_indexed_document(db, document_id, current_user.id)
    text = get_document_full_text(current_user.id, document_id)

    try:
        questions = await generate_quiz(text, num_questions)
    except AIFeatureError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return QuizResponse(document_id=document_id, questions=questions)
