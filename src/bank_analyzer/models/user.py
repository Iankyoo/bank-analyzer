import uuid
from datetime import datetime

from sqlalchemy import UUID, func
from sqlalchemy.orm import Mapped, mapped_column

from bank_analyzer.core.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default_factory=uuid.uuid4,
        unique=True,
        init=False,
        primary_key=True,
    )
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())
