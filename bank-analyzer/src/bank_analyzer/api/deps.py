from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.database import get_session
from bank_analyzer.core.security import decode_access_token
from bank_analyzer.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
Session = Annotated[AsyncSession, Depends(get_session)]
Token = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(token: Token, session: Session):
    email = decode_access_token(token)
    result = await session.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    if not existing_user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="User not found"
        )
    return existing_user
