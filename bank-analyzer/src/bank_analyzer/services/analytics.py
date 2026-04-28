from collections import Counter
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.enums import TransactionType
from bank_analyzer.models.transaction import Transaction
from bank_analyzer.schemas.analytics import StatementAnalysis
from bank_analyzer.services.insight import generate_insight


async def get_statement_transactions(
    statement_id: str, session: AsyncSession
) -> list[Transaction]:
    result = await session.execute(
        select(Transaction).where(Transaction.statement_id == statement_id)
    )
    return list(result.scalars().all())


def calculate_overview(transactions: list[Transaction]) -> dict:
    total_income = sum(
        t.amount for t in transactions if t.transaction_type == TransactionType.CREDIT
    )
    total_expenses = sum(
        t.amount for t in transactions if t.transaction_type == TransactionType.DEBIT
    )
    net_balance = total_income - total_expenses
    savings_rate = (net_balance / total_income * 100) if total_income > 0 else 0.0

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": net_balance,
        "savings_rate": float(savings_rate),
    }


def calculate_category_metrics(transactions: list[Transaction]) -> dict:
    debits = [t for t in transactions if t.transaction_type == TransactionType.DEBIT]

    # gasto total por categoria
    expenses_by_category: dict[str, Decimal] = {}
    for t in debits:
        key = t.category.value
        expenses_by_category[key] = expenses_by_category.get(key, Decimal(0)) + t.amount

    # categoria com maior gasto
    top_category = (
        max(expenses_by_category, key=expenses_by_category.get)
        if expenses_by_category
        else "other"
    )

    # categoria mais frequente
    category_counts = Counter(t.category.value for t in debits)
    most_frequent_category = (
        category_counts.most_common(1)[0][0] if category_counts else "other"
    )

    # ticket médio
    average_transaction_value = (
        (sum(t.amount for t in debits) / len(debits)) if debits else Decimal(0)
    )

    return {
        "expenses_by_category": expenses_by_category,
        "top_category": top_category,
        "most_frequent_category": most_frequent_category,
        "average_transaction_value": average_transaction_value,
    }


def calculate_behavior_metrics(transactions: list[Transaction]) -> dict:
    day_counts = Counter(t.date.day for t in transactions)
    busiest_day = day_counts.most_common(1)[0][0] if day_counts else 1

    return {"busiest_day": busiest_day}


def detect_anomalies(transactions: list[Transaction]) -> list[dict]:
    debits = [t for t in transactions if t.transaction_type == TransactionType.DEBIT]

    # calcula média por categoria
    category_totals: dict[str, list[Decimal]] = {}
    for t in debits:
        key = t.category.value
        if key not in category_totals:
            category_totals[key] = []
        category_totals[key].append(t.amount)

    category_averages = {
        category: sum(amounts) / len(amounts)
        for category, amounts in category_totals.items()
    }

    # detecta anomalias
    anomalies = []
    for t in debits:
        average = category_averages[t.category.value]
        if t.amount > average * 2:
            anomalies.append(
                {
                    "description": t.description,
                    "amount": t.amount,
                    "category": t.category.value,
                    "average_for_category": average,
                }
            )

    return anomalies


async def analyze_statement(
    statement_id: str, session: AsyncSession
) -> StatementAnalysis:
    transactions = await get_statement_transactions(statement_id, session)

    overview = calculate_overview(transactions)
    category_metrics = calculate_category_metrics(transactions)
    behavior = calculate_behavior_metrics(transactions)
    anomalies = detect_anomalies(transactions)

    metrics = {**overview, **category_metrics, **behavior, "anomalies": anomalies}

    ai_insight = generate_insight(metrics)

    return StatementAnalysis(**metrics, ai_insight=ai_insight)
