from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from bank_analyzer.core.enums import Category, TransactionType
from bank_analyzer.services.analytics import calculate_overview


def make_transaction(amount, transaction_type, category, day=1):
    t = MagicMock()
    t.amount = Decimal(str(amount))
    t.transaction_type = transaction_type
    t.category = category
    t.date = date(2025, 1, day)
    return t


def test_calculate_overview_basic():
    transactions = [
        make_transaction(1000, TransactionType.CREDIT, Category.SALARY),
        make_transaction(500, TransactionType.CREDIT, Category.SALARY),
        make_transaction(300, TransactionType.DEBIT, Category.FOOD),
        make_transaction(200, TransactionType.DEBIT, Category.TRANSPORT),
    ]

    result = calculate_overview(transactions)

    assert result["total_income"] == Decimal("1500")
    assert result["total_expenses"] == Decimal("500")
    assert result["net_balance"] == Decimal("1000")
    assert round(result["savings_rate"], 2) == 66.67
