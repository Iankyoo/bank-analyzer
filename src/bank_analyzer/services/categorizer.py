import logging

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from bank_analyzer.core.config import settings
from bank_analyzer.services.memory import (
    find_similar_transaction,
    save_transaction_embedding,
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

prompt_categorize = PromptTemplate(
    template="""Qual a categoria dessa transação financeira: "{description}"?
Retorne APENAS uma palavra, sem explicações, sem markdown.
Opções: food, transport, health, housing, leisure, education, salary, investments,
other""",
    input_variables=["description"],
)


def categorize_with_gemini(description: str) -> str:
    chain = prompt_categorize | model | StrOutputParser()
    return chain.invoke({"description": description}).strip().lower()


def parse_transactions(text: str) -> list:
    # 1. extrai todas as transações sem categoria
    chain = prompt_extract | model | parser
    transactions = chain.invoke({"text": text})

    # 2. categoriza cada transação
    for t in transactions:
        category = find_similar_transaction(t["description"])

        if not category:
            category = categorize_with_gemini(t["description"])
            save_transaction_embedding(
                id=f"{t['date']}-{t['description']}",
                description=t["description"],
                category=category,
            )

        t["category"] = category

    return transactions
