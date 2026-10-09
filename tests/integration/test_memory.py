from unittest.mock import patch

import pytest_asyncio
from sqlalchemy import select

from bank_analyzer.core.enums import Category
from bank_analyzer.models.embedding import EMBEDDING_DIMENSIONS, TransactionEmbedding
from bank_analyzer.models.user import User
from bank_analyzer.services.categorizer import categorize_transactions
from bank_analyzer.services.memory import find_similar_category, save_embedding


def vector(*values: float) -> list[float]:
    return list(values) + [0.0] * (EMBEDDING_DIMENSIONS - len(values))


FOOD = vector(1.0)
FOOD_LIKE = vector(1.0, 0.1)  # distância de cosseno ~0.005 de FOOD
TRANSPORT = vector(0.0, 0.0, 1.0)  # distância de cosseno 1 de FOOD


async def create_user(session, email: str) -> User:
    user = User(email=email, hashed_password="hash")
    session.add(user)
    await session.commit()
    return user


@pytest_asyncio.fixture
async def user(session):
    return await create_user(session, "memory@email.com")


async def test_find_similar_category_within_threshold(session, user):
    save_embedding(session, user.id, "iFood Almoco", Category.FOOD, FOOD)
    await session.commit()

    assert await find_similar_category(session, user.id, FOOD_LIKE) == Category.FOOD


async def test_find_similar_category_beyond_threshold(session, user):
    save_embedding(session, user.id, "iFood Almoco", Category.FOOD, FOOD)
    await session.commit()

    assert await find_similar_category(session, user.id, TRANSPORT) is None


async def test_find_similar_category_empty_memory(session, user):
    assert await find_similar_category(session, user.id, FOOD) is None


async def test_find_similar_category_isolated_by_user(session, user):
    other_user = await create_user(session, "other@email.com")
    save_embedding(session, other_user.id, "iFood Almoco", Category.FOOD, FOOD)
    await session.commit()

    assert await find_similar_category(session, user.id, FOOD) is None


async def test_categorize_transactions_uses_memory_before_gemini(session, user):
    save_embedding(session, user.id, "iFood Almoco", Category.FOOD, FOOD)
    await session.commit()

    transactions = [
        {"description": "IFOOD *RESTAURANTE", "transaction_type": "debit"},
        {"description": "Uber Trip", "transaction_type": "debit"},
    ]

    with (
        patch(
            "bank_analyzer.services.categorizer.embed_descriptions",
            return_value=[FOOD_LIKE, TRANSPORT],
        ),
        patch(
            "bank_analyzer.services.categorizer.categorize_batch_with_gemini",
            return_value=[Category.TRANSPORT],
        ) as mock_gemini,
    ):
        await categorize_transactions(session, user.id, transactions)
        await session.commit()

    # só a transação desconhecida vai para o Gemini
    mock_gemini.assert_called_once_with([transactions[1]])
    assert transactions[0]["category"] == Category.FOOD
    assert transactions[1]["category"] == Category.TRANSPORT

    # e passa a fazer parte da memória do usuário
    saved = (await session.execute(select(TransactionEmbedding.description))).all()
    assert {row.description for row in saved} == {"iFood Almoco", "Uber Trip"}


async def test_uncategorized_transaction_becomes_other_and_stays_out_of_memory(
    session, user
):
    transactions = [{"description": "Compra X", "transaction_type": "debit"}]

    with (
        patch(
            "bank_analyzer.services.categorizer.embed_descriptions",
            return_value=[FOOD],
        ),
        patch(
            "bank_analyzer.services.categorizer.categorize_batch_with_gemini",
            return_value=[None],
        ),
    ):
        await categorize_transactions(session, user.id, transactions)
        await session.commit()

    assert transactions[0]["category"] == Category.OTHER
    # um "other" por falta de resposta não pode virar memória
    saved = (await session.execute(select(TransactionEmbedding))).all()
    assert saved == []
