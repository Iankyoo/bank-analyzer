from httpx import AsyncClient

from bank_analyzer.core.security import create_access_token


async def register(client: AsyncClient, email: str = "dash@email.com"):
    await client.post("/auth/register", json={"email": email, "password": "secret123"})


async def test_login_sets_cookie_and_redirects(client: AsyncClient):
    await register(client)

    response = await client.post(
        "/login", data={"username": "dash@email.com", "password": "secret123"}
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/statements"
    cookie = response.headers["set-cookie"]
    assert "access_token=" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie


async def test_login_wrong_password_shows_error(client: AsyncClient):
    await register(client)

    response = await client.post(
        "/login", data={"username": "dash@email.com", "password": "wrong-pass"}
    )

    assert response.status_code == 200
    assert "Email ou senha incorretos" in response.text


async def test_statements_without_cookie_redirects_to_login(client: AsyncClient):
    response = await client.get("/statements")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


async def test_statements_with_invalid_token_redirects_to_login(client: AsyncClient):
    client.cookies.set("access_token", "not-a-jwt")

    response = await client.get("/statements")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


async def test_statements_with_token_of_deleted_user_redirects_to_login(
    client: AsyncClient,
):
    client.cookies.set("access_token", create_access_token({"sub": "ghost@email.com"}))

    response = await client.get("/statements")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


async def test_statements_with_valid_cookie(client: AsyncClient):
    await register(client)
    client.cookies.set("access_token", create_access_token({"sub": "dash@email.com"}))

    response = await client.get("/statements")

    assert response.status_code == 200
