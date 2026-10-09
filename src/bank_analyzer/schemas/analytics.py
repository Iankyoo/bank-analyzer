from decimal import Decimal

from pydantic import BaseModel

from bank_analyzer.core.enums import Status


class AnomalySchema(BaseModel):
    description: str
    amount: Decimal
    category: str
    average_for_category: Decimal


class StatementAnalysis(BaseModel):
    status: Status

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

    # insight da IA, gerado uma vez no processamento (None se ainda não
    # processado ou se a geração falhou)
    ai_insight: str | None
