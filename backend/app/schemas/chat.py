from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceSnippet(BaseModel):
    document_id: str
    filename: str
    page: int | None = None
    snippet: str
    score: float


class ChatQueryRequest(BaseModel):
    session_id: str | None = None  # None -> create a new session
    message: str
    document_ids: list[str] | None = None  # optional scoping to specific docs


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    created_at: datetime


class ChatQueryResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceSnippet]
    confidence: float


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    session: ChatSessionRead
    messages: list[ChatMessageRead]
