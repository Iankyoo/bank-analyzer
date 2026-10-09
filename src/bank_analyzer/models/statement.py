from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bank_analyzer.core.base import Base
from bank_analyzer.core.enums import Status

if TYPE_CHECKING:
    from bank_analyzer.models.user import User


class Statement(Base):
    __tablename__ = "statements"
    # o mesmo PDF não entra duas vezes para o mesmo usuário (idempotência do upload)
    __table_args__ = (
        UniqueConstraint("user_id", "file_hash", name="uq_statements_user_file_hash"),
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default_factory=uuid.uuid4, primary_key=True, init=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str]
    file_path: Mapped[str]
    uploaded_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())
    status: Mapped[Status]
    file_hash: Mapped[str]
    user: Mapped["User"] = relationship(init=False)
