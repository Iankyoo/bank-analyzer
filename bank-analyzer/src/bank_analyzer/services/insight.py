from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from bank_analyzer.core.config import settings

model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL, google_api_key=settings.GEMINI_API_KEY
)

prompt = PromptTemplate(
    template="""Você é um consultor financeiro direto e honesto.
Analise os dados abaixo e gere um insight PRECISO e ÚTIL em português.

DADOS:
- Receita total: R$ {total_income}
- Despesas totais: R$ {total_expenses}
- Saldo líquido: R$ {net_balance}
- Taxa de economia: {savings_rate}%
- Maior categoria de gasto: {top_category} (R$ {top_category_amount})
- Moradia representa {housing_pct}% das despesas totais
- Categoria mais frequente: {most_frequent_category}
- Ticket médio: R$ {average_transaction_value}
- Dia mais movimentado: dia {busiest_day}
- Transações anômalas: {anomaly_details}

REGRAS:
- Seja direto e específico — cite números reais
- Não bajule — seja honesto mesmo se a situação for boa
- Se moradia > 30% das despesas, alerte com o percentual exato
- Mencione cada transação anômala pelo nome
- Sem markdown, sem negrito, sem asteriscos
- Máximo 3 parágrafos curtos
- Termine com UMA sugestão prática e específica""",
    input_variables=[
        "total_income",
        "total_expenses",
        "net_balance",
        "savings_rate",
        "top_category",
        "top_category_amount",
        "housing_pct",
        "most_frequent_category",
        "average_transaction_value",
        "busiest_day",
        "anomaly_details",
    ],
)


def generate_insight(metrics: dict) -> str:
    expenses_by_category = metrics["expenses_by_category"]
    total_expenses = metrics["total_expenses"]

    top_category = metrics["top_category"]
    top_category_amount = expenses_by_category.get(top_category, 0)

    housing_amount = expenses_by_category.get("housing", 0)
    housing_pct = (
        round(float(housing_amount) / float(total_expenses) * 100, 1)
        if total_expenses > 0
        else 0
    )

    anomaly_details = (
        ", ".join([a["description"] for a in metrics["anomalies"]])
        if metrics["anomalies"]
        else "nenhuma"
    )

    chain = prompt | model | StrOutputParser()
    return chain.invoke(
        {
            "total_income": metrics["total_income"],
            "total_expenses": total_expenses,
            "net_balance": metrics["net_balance"],
            "savings_rate": round(metrics["savings_rate"], 1),
            "top_category": top_category,
            "top_category_amount": top_category_amount,
            "housing_pct": housing_pct,
            "most_frequent_category": metrics["most_frequent_category"],
            "average_transaction_value": metrics["average_transaction_value"],
            "busiest_day": metrics["busiest_day"],
            "anomaly_details": anomaly_details,
        }
    )
