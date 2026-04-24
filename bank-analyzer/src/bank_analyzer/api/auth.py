from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.database import get_session
from bank_analyzer.core.security import create_access_token
from bank_analyzer.schemas.token import Token
from bank_analyzer.schemas.user import UserCreate, UserPublic
from bank_analyzer.services.auth import authenticate_user, create_user

router = APIRouter(prefix="/auth", tags=["auth"])

OAuth2form = Annotated[OAuth2PasswordRequestForm, Depends()]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.post("/register", response_model=UserPublic, status_code=HTTPStatus.CREATED)
async def register(user: UserCreate, session: Session):
    return await create_user(user, session)


@router.post("/token", response_model=Token, status_code=HTTPStatus.OK)
async def token(form_data: OAuth2form, session: Session):
    user = await authenticate_user(form_data.username, form_data.password, session)
    access_token = create_access_token({"sub": user.email})
    return Token(access_token=access_token, token_type="bearer")
