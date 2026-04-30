import pytest
from fastapi import HTTPException

from bank_analyzer.core.security import (
    create_access_token,
    decode_access_token,
    get_hashed_password,
    verify_password,
)


def test_get_hashed_password():
    password = "test"

    hashed_password = get_hashed_password(password)

    assert hashed_password != password
    assert hashed_password is not None
    assert len(hashed_password) > 0


def test_verify_password():
    password = "secret"

    hashed_password = get_hashed_password(password)

    assert verify_password(password, hashed_password) is True
    assert verify_password("wrong_password", hashed_password) is False


def test_create_access_token():
    sub = {"sub": "username"}
    token = create_access_token(sub)

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token():
    email = "test@email.com"

    token = create_access_token({"sub": email})

    result = decode_access_token(token)

    assert result == email


def test_decode_access_token_invalid():

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("token_invalido")

    assert exc_info.value.status_code == 401
