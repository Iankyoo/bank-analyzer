import asyncio
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

Transações (numeradas):
{transactions}

Para cada transação, retorne um objeto com:
- index: o número da transação na lista acima
- category: uma das opções:
    food, transport, health, housing, leisure, education, salary, investments, other

Regras:
- Retorne um objeto para cada número da lista, sem pular nenhum
- Use "salary" apenas para transações de CREDIT que representam renda de trabalho
- Use "investments" para rendimentos e aplicações financeiras
- Retorne APENAS o JSON, sem markdown, sem explicações

Formato esperado:
[{{"index": 1, "category": "..."}}]""",
    input_variables=["transactions"],
)


def parse_category(value: object) -> Category | None:
    try:
        return Category(value)
    except ValueError:
        return None


def categorize_batch_with_gemini(transactions: list) -> list[Category | None]:
    """Uma categoria por transação, na mesma ordem; None se o modelo não
    devolveu uma categoria válida para ela."""
    # a resposta é casada pelo índice, não pela descrição: o modelo às vezes
    # devolve a descrição reescrita (ex.: com " (debit)" no fim) e ela deixa
    # de bater com a original
    tx_list = "\n".join(
        f"{i}. {t['description']} ({t['transaction_type']})"
        for i, t in enumerate(transactions, start=1)
    )
    chain = prompt_categorize_batch | model | JsonOutputParser()
    results = chain.invoke({"transactions": tx_list})

    categories: list[Category | None] = [None] * len(transactions)
    for r in results if isinstance(results, list) else []:
        try:
            index = int(r["index"])
        except (TypeError, KeyError, ValueError):
            continue
        if 1 <= index <= len(transactions):
            categories[index - 1] = parse_category(r.get("category"))
    return categories


def extract_transactions(text: str) -> list:
    chain = prompt_extract | model | parser
    return chain.invoke({"text": text})


async def categorize_transactions(
    session: AsyncSession, user_id: uuid.UUID, transactions: list
) -> None:
    if not transactions:
        return

    descriptions = [t["description"] for t in transactions]
    vectors = await asyncio.to_thread(embed_descriptions, descriptions)

    unknown = []
    for t, vector in zip(transactions, vectors):
        category = await find_similar_category(session, user_id, vector)
        if category:
            t["category"] = category
        else:
            unknown.append((t, vector))

    if not unknown:
        return

    categories = await asyncio.to_thread(
        categorize_batch_with_gemini, [t for t, _ in unknown]
    )
    saved = set()
    for (t, vector), category in zip(unknown, categories):
        if category is None:
            # sem resposta válida do modelo: entra como "other", mas fica fora da
            # memória para não ensinar uma categoria errada aos próximos extratos
            logger.warning("Sem categoria para %r; usando other", t["description"])
            t["category"] = Category.OTHER
            continue

        t["category"] = category
        if t["description"] not in saved:
            save_embedding(session, user_id, t["description"], category, vector)
            saved.add(t["description"])
