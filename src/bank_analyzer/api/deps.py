from http import HTTPStatus
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.database import get_session
from bank_analyzer.core.security import decode_access_token
from bank_analyzer.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
Session = Annotated[AsyncSession, Depends(get_session)]
Token = Annotated[str, Depends(oauth2_scheme)]


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_current_user(token: Token, session: Session) -> User:
    """API: token no header Authorization. Falha com 401."""
    email = decode_access_token(token)
    user = await get_user_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="User not found"
        )
    return user


async def get_current_user_from_cookie(
    session: Session, access_token: Annotated[str | None, Cookie()] = None
) -> User:
    """Dashboard: token no cookie. Falha redirecionando para /login."""
    redirect_to_login = HTTPException(
        status_code=HTTPStatus.SEE_OTHER, headers={"Location": "/login"}
    )
    if not access_token:
        raise redirect_to_login

    try:
        email = decode_access_token(access_token)
    except HTTPException:
        raise redirect_to_login

    user = await get_user_by_email(session, email)
    if not user:
        raise redirect_to_login
    return user
