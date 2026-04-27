from decimal import Decimal

from pydantic import BaseModel


class AnomalySchema(BaseModel):
    description: str
    amount: Decimal
    category: str
    average_for_category: Decimal


class StatementAnalysis(BaseModel):
    # visão geral
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    savings_rate: float  # percentual 0-100

    # por categoria
    expenses_by_category: dict[str, Decimal]
    top_category: str
    most_frequent_category: str
    average_transaction_value: Decimal

    # comportamento
    busiest_day: int  # dia do mês (1-31)

    # anomalias
    anomalies: list[AnomalySchema]

    # insight da IA
    ai_insight: str
