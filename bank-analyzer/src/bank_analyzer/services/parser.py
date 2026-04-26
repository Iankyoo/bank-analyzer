import io
import logging

import pdfplumber
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import select

from bank_analyzer.core.config import settings
from bank_analyzer.core.database import SessionLocal
from bank_analyzer.core.enums import Category, Status, TransactionType
from bank_analyzer.models.statement import Statement
from bank_analyzer.models.transaction import Transaction
from bank_analyzer.services.storage import s3_client


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


model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL, google_api_key=settings.GEMINI_API_KEY
)

logger = logging.getLogger(__name__)

parser = JsonOutputParser()

prompt = PromptTemplate(
    template="""Você é um analisador de extratos bancários.
Dado o texto abaixo, extraia todas as transações e retorne APENAS um JSON válido.

Cada transação deve ter:
- date: data no formato YYYY-MM-DD
- description: descrição da transação
- amount: valor absoluto como número decimal
- transaction_type: "credit" ou "debit"
- category: uma das opções: food, transport, health, housing, leisure, education,
salary, investments, other

Retorne APENAS o JSON, sem texto adicional, sem markdown, sem explicações.

Texto do extrato:
{text}""",
    input_variables=["text"],
)


def parse_transactions(text: str) -> list:
    chain = prompt | model | parser
    result = chain.invoke({"text": text})
    return result


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
