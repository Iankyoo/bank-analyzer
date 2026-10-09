import io
import logging
from datetime import date
from decimal import Decimal

import pdfplumber
from sqlalchemy import select

from bank_analyzer.core.database import SessionLocal
from bank_analyzer.core.enums import Status, TransactionType
from bank_analyzer.models.statement import Statement
from bank_analyzer.models.transaction import Transaction
from bank_analyzer.services.analytics import calculate_metrics
from bank_analyzer.services.categorizer import (
    categorize_transactions,
    extract_transactions,
)
from bank_analyzer.services.insight import generate_insight
from bank_analyzer.services.storage import read_file

logger = logging.getLogger(__name__)


def read_pdf(file_path: str) -> io.BytesIO:
    return io.BytesIO(read_file(file_path))


def extract_text_from_pdf(file_obj: io.BytesIO) -> str:
    with pdfplumber.open(file_obj) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text


def generate_statement_insight(transactions: list[Transaction]) -> str | None:
    # o insight é complementar: se o Gemini falhar aqui, o extrato continua
    # válido com todas as métricas, só sem o texto
    try:
        return generate_insight(calculate_metrics(transactions))
    except Exception:
        logger.exception("Falha ao gerar insight; extrato salvo sem insight")
        return None


async def process_statement(statement_id: str, file_path: str) -> None:
    async with SessionLocal() as session:
        statement = None
        try:
            result = await session.execute(
                select(Statement).where(Statement.id == statement_id)
            )
            statement = result.scalar_one_or_none()
            if not statement:
                return

            statement.status = Status.PROCESSING
            await session.commit()

            file_obj = read_pdf(file_path)
            text = extract_text_from_pdf(file_obj)
            transactions = extract_transactions(text)
            await categorize_transactions(session, statement.user_id, transactions)

            new_transactions = [
                Transaction(
                    statement_id=statement.id,
                    date=date.fromisoformat(t["date"]),
                    description=t["description"],
                    amount=Decimal(str(t["amount"])),
                    transaction_type=TransactionType(t["transaction_type"]),
                    category=t["category"],
                )
                for t in transactions
            ]
            session.add_all(new_transactions)

            statement.ai_insight = generate_statement_insight(new_transactions)
            statement.status = Status.COMPLETED
            await session.commit()

        except Exception as e:
            logger.error(f"Error processing statement {statement_id}: {e}")
            await session.rollback()
            if statement is not None:
                statement.status = Status.ERROR
                await session.commit()
