import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging_config import logger
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentListResponse, DocumentRead
from app.services.document_pipeline import process_document
from app.services.vector_store import delete_document_chunks
from app.utils.file_validation import enforce_size_limit, generate_stored_filename, validate_upload

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _run_pipeline_in_background(bind, document_id: str, force_ocr: bool = False) -> None:
    """Background tasks run after the request's own session has closed, so
    this needs a fresh session -- but it must be bound to the *same engine*
    the request used (`bind`, taken from the request-scoped session),
    rather than a hardcoded global. That keeps this correctly isolated in
    tests (which override get_db with a per-test engine) without any extra
    test-only branching here.
    """
    SessionFactory = sessionmaker(bind=bind)
    db = SessionFactory()
    try:
        process_document(db, document_id, force_ocr=force_ocr)
    finally:
        db.close()


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    ext = validate_upload(file)

    contents = await file.read()
    enforce_size_limit(len(contents))

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_name = generate_stored_filename(file.filename or "upload")
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)

    with open(stored_path, "wb") as f:
        f.write(contents)

    document = Document(
        owner_id=current_user.id,
        filename=stored_name,
        original_filename=file.filename or stored_name,
        file_path=stored_path,
        file_type=ext,
        file_size_bytes=len(contents),
        status="pending",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    logger.info("Document uploaded: {} by user {}", document.original_filename, current_user.email)

    background_tasks.add_task(_run_pipeline_in_background, db.get_bind(), document.id)

    return DocumentRead.model_validate(document)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    documents = (
        db.query(Document)
        .filter(Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return DocumentListResponse(total=len(documents), documents=[DocumentRead.model_validate(d) for d in documents])


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.owner_id == current_user.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentRead.model_validate(document)


@router.post("/{document_id}/retry", response_model=DocumentRead)
def retry_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    force_ocr: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.owner_id == current_user.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document.status = "pending"
    document.error_message = ""
    db.commit()

    background_tasks.add_task(_run_pipeline_in_background, db.get_bind(), document.id, force_ocr)
    return DocumentRead.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.owner_id == current_user.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    delete_document_chunks(current_user.id, document.id)

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()
    logger.info("Document deleted: {} by user {}", document.original_filename, current_user.email)
