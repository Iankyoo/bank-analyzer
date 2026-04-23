from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bank_analyzer.core.base import Base
from bank_analyzer.core.enums import Category, TransactionType

if TYPE_CHECKING:
    from bank_analyzer.models.statement import Statement


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default_factory=uuid.uuid4, init=False, primary_key=True
    )
    statement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("statements.id"))
    date: Mapped[date]
    description: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    transaction_type: Mapped[TransactionType]
    category: Mapped[Category]
    statement: Mapped["Statement"] = relationship(init=False)
