from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from bank_analyzer.core.enums import Category, TransactionType
from bank_analyzer.services.analytics import (
    calculate_category_metrics,
    calculate_overview,
    detect_anomalies,
)


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


def test_calculate_overview_no_income():
    transactions = [make_transaction(100, TransactionType.DEBIT, Category.FOOD)]

    result = calculate_overview(transactions)

    assert result["total_income"] == Decimal("0")
    assert result["savings_rate"] == 0.0


def test_calculate_category_metrics():
    transactions = [
        make_transaction(300, TransactionType.DEBIT, Category.FOOD),
        make_transaction(300, TransactionType.DEBIT, Category.FOOD),
        make_transaction(500, TransactionType.DEBIT, Category.HOUSING),
        make_transaction(1000, TransactionType.CREDIT, Category.SALARY),
    ]

    result = calculate_category_metrics(transactions)

    assert result["top_category"] == "housing"
    assert result["most_frequent_category"] == "food"
    assert result["expenses_by_category"] == {
        "food": Decimal("600"),
        "housing": Decimal("500"),
    }
    assert round(result["average_transaction_value"], 2) == Decimal("366.67")
