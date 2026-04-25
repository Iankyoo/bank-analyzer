from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.database import get_session
from bank_analyzer.core.enums import Status
from bank_analyzer.models.statement import Statement

Session = Annotated[AsyncSession, Depends(get_session)]


async def create_statement(
    session: Session,
    user_id: str,
    filename: str,
):
    new_statement = Statement(user_id=user_id, filename=filename, status=Status.PENDING)

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
