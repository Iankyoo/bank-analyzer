from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from bank_analyzer.core.base import Base
from bank_analyzer.core.enums import Category

EMBEDDING_DIMENSIONS = 768


class TransactionEmbedding(Base):
    __tablename__ = "transaction_embeddings"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default_factory=uuid.uuid4, init=False, primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str] = mapped_column(String(200))
    category: Mapped[Category]
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
