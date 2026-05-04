from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.database import get_session
from bank_analyzer.core.enums import Status
from bank_analyzer.models.statement import Statement

Session = Annotated[AsyncSession, Depends(get_session)]


async def create_statement(
    session: Session, user_id: str, filename: str, s3_key: str, file_hash: str
):
    new_statement = Statement(
        user_id=user_id,
        filename=filename,
        status=Status.PENDING,
        s3_key=s3_key,
        file_hash=file_hash,
    )

    try:
        session.add(new_statement)
        await session.commit()
        await session.refresh(new_statement)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Statement already exists"
        )
    return new_statement


async def get_statement_by_hash(session: Session, user_id: str, file_hash: str):
    result = await session.execute(
        select(Statement).where(
            Statement.user_id == user_id, Statement.file_hash == file_hash
        )
    )
    return result.scalar_one_or_none()
