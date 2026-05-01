from httpx import AsyncClient


async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={"email": "test@email.com", "password": "secret123"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "test@email.com"
    assert "id" in response.json()
    assert "password" not in response.json()


async def test_register_duplicate_email(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "test@email.com", "password": "secret123"},
    )

    response = await client.post(
        "/auth/register",
        json={"email": "test@email.com", "password": "secret123"},
    )

    assert response.status_code == 409


async def test_login_success(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "test@email.com", "password": "secret123"},
    )

    response = await client.post(
        "/auth/token",
        data={"username": "test@email.com", "password": "secret123"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "test@email.com", "password": "secret123"},
    )

    response = await client.post(
        "/auth/token",
        data={"username": "test@email.com", "password": "wrong"},
    )

    assert response.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={"username": "nonexistent@email.com", "password": "secret123"},
    )

    assert response.status_code == 401
