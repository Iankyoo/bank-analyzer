import chromadb
from chromadb.utils.embedding_functions import EmbeddingFunction
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from bank_analyzer.core.config import settings

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004", google_api_key=settings.GEMINI_API_KEY
)


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: list[str]) -> list:
        return embeddings.embed_documents(input)


client = chromadb.Client()

collection = client.get_or_create_collection(
    name="transactions", embedding_function=GeminiEmbeddingFunction()
)


def find_similar_transaction(description: str) -> str | None:
    results = collection.query(query_texts=[description], n_results=1)

    if not results["metadatas"][0]:
        return None
    return results["metadatas"][0][0]["category"]


def save_transaction_embedding(id: str, description: str, category: str) -> None:
    collection.add(
        documents=[description], metadatas=[{"category": category}], ids=[id]
    )
