from bank_analyzer.core.security import get_hashed_password, verify_password


def test_get_hashed_password():
    password = 'test'

    hashed_password = get_hashed_password(password)

    assert hashed_password != password
    assert hashed_password is not None
    assert len(hashed_password) > 0


def test_verify_password():
    password = 'secret'

    hashed_password = get_hashed_password(password)

    assert verify_password(password, hashed_password) is True
    assert verify_password("wrong_password", hashed_password) is False
