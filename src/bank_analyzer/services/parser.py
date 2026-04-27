import io
import logging

import pdfplumber
from sqlalchemy import select

from bank_analyzer.core.config import settings
from bank_analyzer.core.database import SessionLocal
from bank_analyzer.core.enums import Category, Status, TransactionType
from bank_analyzer.models.statement import Statement
from bank_analyzer.models.transaction import Transaction
from bank_analyzer.services.categorizer import parse_transactions
from bank_analyzer.services.storage import s3_client

logger = logging.getLogger(__name__)


def download_pdf_from_s3(s3_key: str) -> io.BytesIO:
    file_obj = io.BytesIO()
    s3_client.download_fileobj(settings.AWS_BUCKET_NAME, s3_key, file_obj)
    file_obj.seek(0)
    return file_obj


def extract_text_from_pdf(file_obj: io.BytesIO) -> str:
    with pdfplumber.open(file_obj) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text


async def process_statement(statement_id: str, s3_key: str) -> None:
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(Statement).where(Statement.id == statement_id)
            )
            statement = result.scalar_one_or_none()
            if not statement:
                return

            statement.status = Status.PROCESSING
            await session.commit()

            file_obj = download_pdf_from_s3(s3_key)
            text = extract_text_from_pdf(file_obj)
            transactions = parse_transactions(text)

            for t in transactions:
                transaction = Transaction(
                    statement_id=statement.id,
                    date=t["date"],
                    description=t["description"],
                    amount=t["amount"],
                    transaction_type=TransactionType(t["transaction_type"]),
                    category=Category(t["category"]),
                )
                session.add(transaction)

            statement.status = Status.COMPLETED
            await session.commit()

        except Exception as e:
            logger.error(f"Error processing statement {statement_id}: {e}")
            await session.rollback()
            statement.status = Status.ERROR
            await session.commit()
