import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

# Entity types we ask the LLM to classify into -- kept small and closed so
# the frontend can assign a consistent color/icon per type.
ENTITY_TYPES = ("PERSON", "ORGANIZATION", "LOCATION", "TECHNOLOGY", "DATE", "OTHER")


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (UniqueConstraint("owner_id", "name", "type", name="uq_entity_owner_name_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="OTHER")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    document_links = relationship(
        "EntityDocumentLink", back_populates="entity", cascade="all, delete-orphan"
    )


class EntityDocumentLink(Base):
    """Which documents an entity was mentioned in -- lets the graph be scoped/filtered per document."""

    __tablename__ = "entity_document_links"
    __table_args__ = (UniqueConstraint("entity_id", "document_id", name="uq_entity_document"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)

    entity = relationship("Entity", back_populates="document_links")


class EntityRelation(Base):
    """A directed, labeled edge between two entities, sourced from a specific document."""

    __tablename__ = "entity_relations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    source_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), default="related to")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
