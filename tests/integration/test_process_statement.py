from decimal import Decimal
from unittest.mock import patch

import pytest_asyncio
from sqlalchemy import select

from bank_analyzer.core.enums import Category, Status
from bank_analyzer.models.embedding import EMBEDDING_DIMENSIONS
from bank_analyzer.models.statement import Statement
from bank_analyzer.models.transaction import Transaction
from bank_analyzer.models.user import User
from bank_analyzer.services.analytics import analyze_statement
from bank_analyzer.services.parser import process_statement
from tests.conftest import SessionTest

EXTRACTED = [
    {
        "date": "2026-03-01",
        "description": "Salario",
        "amount": 5000.0,
        "transaction_type": "credit",
    },
    {
        "date": "2026-03-05",
        "description": "Aluguel",
        "amount": 1500.5,
        "transaction_type": "debit",
    },
]


@pytest_asyncio.fixture
async def statement(session):
    user = User(email="process@email.com", hashed_password="hash")
    session.add(user)
    await session.commit()

    statement = Statement(
        user_id=user.id,
        filename="extrato.pdf",
        file_path="irrelevante.pdf",
        status=Status.PENDING,
        file_hash="hash",
    )
    session.add(statement)
    await session.commit()
    return statement


def pipeline_mocks(insight):
    """Mocka tudo que é externo: leitura do PDF e chamadas ao Gemini."""
    return (
        patch("bank_analyzer.services.parser.SessionLocal", SessionTest),
        patch("bank_analyzer.services.parser.read_pdf"),
        patch(
            "bank_analyzer.services.parser.extract_text_from_pdf", return_value="..."
        ),
        patch(
            "bank_analyzer.services.parser.extract_transactions",
            return_value=[dict(t) for t in EXTRACTED],
        ),
        patch(
            "bank_analyzer.services.categorizer.embed_descriptions",
            return_value=[[1.0] * EMBEDDING_DIMENSIONS] * len(EXTRACTED),
        ),
        patch(
            "bank_analyzer.services.categorizer.categorize_batch_with_gemini",
            return_value={"Salario": "salary", "Aluguel": "housing"},
        ),
        patch("bank_analyzer.services.parser.generate_insight", **insight),
    )


async def run_pipeline(statement, insight):
    mocks = pipeline_mocks(insight)
    for m in mocks:
        m.start()
    try:
        await process_statement(str(statement.id), statement.file_path)
    finally:
        for m in mocks:
            m.stop()


async def test_process_statement_saves_transactions_and_insight(session, statement):
    await run_pipeline(statement, {"return_value": "Seu aluguel pesa 100%."})

    await session.refresh(statement)
    assert statement.status == Status.COMPLETED
    assert statement.ai_insight == "Seu aluguel pesa 100%."

    result = await session.execute(
        select(Transaction).where(Transaction.statement_id == statement.id)
    )
    transactions = {t.description: t for t in result.scalars()}
    assert transactions["Aluguel"].amount == Decimal("1500.50")
    assert transactions["Aluguel"].category == Category.HOUSING


async def test_analysis_reads_saved_insight_without_calling_gemini(session, statement):
    await run_pipeline(statement, {"return_value": "Insight salvo."})
    statement_id, user_id = str(statement.id), str(statement.user_id)
    # o processamento usou outra sessão; descarta o que esta sessão tem em cache
    session.expire_all()

    with patch(
        "bank_analyzer.services.insight.generate_insight",
        side_effect=AssertionError("não deveria chamar o Gemini"),
    ):
        analysis = await analyze_statement(statement_id, user_id, session)

    assert analysis.status == Status.COMPLETED
    assert analysis.ai_insight == "Insight salvo."
    assert analysis.total_expenses == Decimal("1500.50")


async def test_insight_failure_keeps_statement_completed(session, statement):
    await run_pipeline(statement, {"side_effect": RuntimeError("Gemini fora")})

    await session.refresh(statement)
    assert statement.status == Status.COMPLETED
    assert statement.ai_insight is None
