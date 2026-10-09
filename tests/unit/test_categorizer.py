from unittest.mock import patch

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from bank_analyzer.core.enums import Category
from bank_analyzer.services.categorizer import categorize_batch_with_gemini

TRANSACTIONS = [
    {"description": "Aluguel Julho", "transaction_type": "debit"},
    {"description": "Uber Trip", "transaction_type": "debit"},
    {"description": "Supermercado Extra", "transaction_type": "debit"},
]


def categorize_with_response(response: str):
    """Passa uma resposta crua do modelo pelo prompt e pelo parser reais."""
    fake_model = FakeListChatModel(responses=[response])
    with patch("bank_analyzer.services.categorizer.model", fake_model):
        return categorize_batch_with_gemini(TRANSACTIONS)


def test_matches_by_index_even_if_description_is_rewritten():
    # resposta real observada: o modelo devolveu as descrições com sufixo
    response = """[
        {"index": 1, "description": "Aluguel Julho (debit)", "category": "housing"},
        {"index": 2, "description": "Uber Trip (debit)", "category": "transport"},
        {"index": 3, "description": "Supermercado Extra (debit)", "category": "food"}
    ]"""

    assert categorize_with_response(response) == [
        Category.HOUSING,
        Category.TRANSPORT,
        Category.FOOD,
    ]


def test_response_out_of_order():
    response = """[
        {"index": 3, "category": "food"},
        {"index": 1, "category": "housing"},
        {"index": 2, "category": "transport"}
    ]"""

    assert categorize_with_response(response) == [
        Category.HOUSING,
        Category.TRANSPORT,
        Category.FOOD,
    ]


def test_missing_invalid_or_out_of_range_entries_become_none():
    response = """[
        {"index": 1, "category": "categoria-inventada"},
        {"index": 9, "category": "food"},
        {"category": "food"},
        {"index": 3, "category": "food"}
    ]"""

    assert categorize_with_response(response) == [None, None, Category.FOOD]
