import uuid

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.config import settings
from bank_analyzer.core.enums import Category
from bank_analyzer.models.embedding import EMBEDDING_DIMENSIONS, TransactionEmbedding

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001", google_api_key=settings.GEMINI_API_KEY
)


def embed_descriptions(descriptions: list[str]) -> list[list[float]]:
    # uma única chamada à API para todas as descrições do extrato
    return embeddings.embed_documents(
        descriptions, output_dimensionality=EMBEDDING_DIMENSIONS
    )


async def find_similar_category(
    session: AsyncSession, user_id: uuid.UUID, embedding: list[float]
) -> Category | None:
    distance = TransactionEmbedding.embedding.cosine_distance(embedding)
    result = await session.execute(
        select(TransactionEmbedding.category, distance.label("distance"))
        .where(TransactionEmbedding.user_id == user_id)
        .order_by(distance)
        .limit(1)
    )
    closest = result.first()

    if closest is None or closest.distance > settings.SIMILARITY_DISTANCE_THRESHOLD:
        return None

    return closest.category


def save_embedding(
    session: AsyncSession,
    user_id: uuid.UUID,
    description: str,
    category: Category,
    embedding: list[float],
) -> None:
    # sem commit: o embedding entra na mesma transação das transações do extrato
    session.add(
        TransactionEmbedding(
            user_id=user_id,
            description=description,
            category=category,
            embedding=embedding,
        )
    )
