from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.database import get_session
from bank_analyzer.core.security import get_hashed_password, verify_password
from bank_analyzer.models.user import User
from bank_analyzer.schemas.user import UserCreate

Session = Annotated[AsyncSession, Depends(get_session)]


async def create_user(user: UserCreate, session: Session):
    result = await session.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="User already exists"
        )
    new_user = User(
        email=user.email, hashed_password=get_hashed_password(user.password)
    )
    try:
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="User already exists"
        )
    return new_user


async def authenticate_user(user: UserCreate, session: Session):
    result = await session.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if not existing_user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Incorrect email or password"
        )
    if not verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Incorrect email or password",  # Não especifico tanto de proposito
        )
    return existing_user
