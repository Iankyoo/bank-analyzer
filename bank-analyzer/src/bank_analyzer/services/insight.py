from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from bank_analyzer.core.config import settings

model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL, google_api_key=settings.GEMINI_API_KEY
)

prompt = PromptTemplate(
    template="""Você é um assistente financeiro pessoal.
Com base nas métricas abaixo, gere um insight personalizado em português,
de forma clara e amigável, com no máximo 3 parágrafos.

Inclua:
- Uma avaliação geral da saúde financeira
- O principal ponto de atenção
- Uma sugestão prática de melhoria

Métricas:
- Receita total: R$ {total_income}
- Despesas totais: R$ {total_expenses}
- Saldo líquido: R$ {net_balance}
- Taxa de economia: {savings_rate}%
- Categoria com maior gasto: {top_category}
- Categoria mais frequente: {most_frequent_category}
- Ticket médio: R$ {average_transaction_value}
- Dia mais movimentado: dia {busiest_day}
- Anomalias detectadas: {anomalies_count} transação(ões) fora do padrão

Gere o insight de forma personalizada e humana, sem repetir os números brutos.""",
    input_variables=[
        "total_income",
        "total_expenses",
        "net_balance",
        "savings_rate",
        "top_category",
        "most_frequent_category",
        "average_transaction_value",
        "busiest_day",
        "anomalies_count",
    ],
)


def generate_insight(metrics: dict) -> str:
    chain = prompt | model | StrOutputParser()
    return chain.invoke(
        {
            "total_income": metrics["total_income"],
            "total_expenses": metrics["total_expenses"],
            "net_balance": metrics["net_balance"],
            "savings_rate": round(metrics["savings_rate"], 1),
            "top_category": metrics["top_category"],
            "most_frequent_category": metrics["most_frequent_category"],
            "average_transaction_value": metrics["average_transaction_value"],
            "busiest_day": metrics["busiest_day"],
            "anomalies_count": len(metrics["anomalies"]),
        }
    )
