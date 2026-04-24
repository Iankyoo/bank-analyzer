from datetime import datetime, timedelta, timezone
from http import HTTPStatus

from fastapi import HTTPException
from jwt import decode, encode
from pwdlib import PasswordHash

from bank_analyzer.core.config import settings

pwd_context = PasswordHash.recommended()

credentials_exception = HTTPException(
    status_code=HTTPStatus.UNAUTHORIZED, detail="Incorrect Email or Password"
)


def get_hashed_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.TOKEN_EXPIRE_IN_MINUTES
    )

    to_encode.update({'exp': expire})

    jwt_encoded = encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return jwt_encoded


def decode_access_token(token: dict):
    try:
        payload = decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject_email = payload["sub"]
        if not subject_email:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    return subject_email
