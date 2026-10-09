import logging
import uuid

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.config import settings
from bank_analyzer.core.enums import Category
from bank_analyzer.services.memory import (
    embed_descriptions,
    find_similar_category,
    save_embedding,
)

model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL, google_api_key=settings.GEMINI_API_KEY
)

logger = logging.getLogger(__name__)

parser = JsonOutputParser()

prompt_extract = PromptTemplate(
    template="""Você é um analisador de extratos bancários.
Dado o texto abaixo, extraia todas as transações e retorne APENAS um JSON válido.

Cada transação deve ter:
- date: data no formato YYYY-MM-DD
- description: descrição da transação
- amount: valor absoluto como número decimal
- transaction_type: "credit" ou "debit"

NÃO inclua category. Retorne APENAS o JSON, sem markdown, sem explicações.

Texto do extrato:
{text}""",
    input_variables=["text"],
)


prompt_categorize_batch = PromptTemplate(
    template="""Você é um analisador de extratos bancários.
Categorize cada transação abaixo e retorne APENAS um JSON válido.

Transações:
{transactions}

Para cada transação, retorne um objeto com:
- description: a descrição original
- category: 
    uma das opções:
        food, transport, health, housing, leisure, education, salary, investments, other

Regras:
- Use "salary" apenas para transações de CREDIT que representam renda de trabalho
- Use "investments" para rendimentos e aplicações financeiras
- Retorne APENAS o JSON, sem markdown, sem explicações

Formato esperado:
[{{"description": "...", "category": "..."}}]""",
    input_variables=["transactions"],
)


def categorize_batch_with_gemini(transactions: list) -> dict:
    tx_list = "\n".join(
        [f"- {t['description']} ({t['transaction_type']})" for t in transactions]
    )
    chain = prompt_categorize_batch | model | JsonOutputParser()
    results = chain.invoke({"transactions": tx_list})
    return {r["description"]: r["category"] for r in results}


def to_category(value: str | None) -> Category:
    # o LLM pode devolver uma categoria fora da lista; nesse caso vira "other"
    try:
        return Category(value)
    except ValueError:
        return Category.OTHER


def extract_transactions(text: str) -> list:
    chain = prompt_extract | model | parser
    return chain.invoke({"text": text})


async def categorize_transactions(
    session: AsyncSession, user_id: uuid.UUID, transactions: list
) -> None:
    if not transactions:
        return

    vectors = embed_descriptions([t["description"] for t in transactions])

    unknown = []
    for t, vector in zip(transactions, vectors):
        category = await find_similar_category(session, user_id, vector)
        if category:
            t["category"] = category
        else:
            unknown.append((t, vector))

    if not unknown:
        return

    categories = categorize_batch_with_gemini([t for t, _ in unknown])
    saved = set()
    for t, vector in unknown:
        t["category"] = to_category(categories.get(t["description"]))
        if t["description"] not in saved:
            save_embedding(session, user_id, t["description"], t["category"], vector)
            saved.add(t["description"])
