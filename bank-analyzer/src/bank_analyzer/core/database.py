from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bank_analyzer.core.config import settings

engine = create_async_engine(settings.DATABASE_URL)

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
