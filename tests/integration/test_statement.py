from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from bank_analyzer.core.config import settings
from bank_analyzer.models.user import User
from bank_analyzer.services.statement import create_statement


@pytest.fixture(autouse=True)
def storage_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_DIR", str(tmp_path))
    return tmp_path


async def test_upload_statement(client: AsyncClient, auth_token: str, storage_dir):
    with patch(
        "bank_analyzer.api.statements.process_statement", new_callable=AsyncMock
    ):
        response = await client.post(
            "/statements/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

    assert response.status_code == 200
    assert response.json()["filename"] == "test.pdf"
    assert response.json()["status"] == "pending"
    assert "file_path" not in response.json()

    saved_files = list(storage_dir.rglob("*.pdf"))
    assert len(saved_files) == 1
    assert saved_files[0].read_bytes() == b"%PDF-1.4 fake"


async def test_upload_invalid_file_type(client: AsyncClient, auth_token: str):
    response = await client.post(
        "/statements/upload",
        files={"file": ("test.png", b"fake image content", "image/png")},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422


async def test_get_analysis_forbidden_for_other_user(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "userA@email.com", "password": "secret123"}
    )
    token_a = (
        await client.post(
            "/auth/token",
            data={"username": "userA@email.com", "password": "secret123"},
        )
    ).json()["access_token"]

    with patch(
        "bank_analyzer.api.statements.process_statement", new_callable=AsyncMock
    ):
        upload_response = await client.post(
            "/statements/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
            headers={"Authorization": f"Bearer {token_a}"},
        )
    statement_id = upload_response.json()["id"]

    await client.post(
        "/auth/register", json={"email": "userB@email.com", "password": "secret123"}
    )
    token_b = (
        await client.post(
            "/auth/token",
            data={"username": "userB@email.com", "password": "secret123"},
        )
    ).json()["access_token"]

    response = await client.get(
        f"/statements/{statement_id}/analysis",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 404


async def test_upload_same_file_twice_returns_same_statement(
    client: AsyncClient, auth_token: str, storage_dir
):
    headers = {"Authorization": f"Bearer {auth_token}"}
    files = {"file": ("test.pdf", b"%PDF-1.4 same content", "application/pdf")}

    with patch(
        "bank_analyzer.api.statements.process_statement", new_callable=AsyncMock
    ):
        first = await client.post("/statements/upload", files=files, headers=headers)
        second = await client.post("/statements/upload", files=files, headers=headers)

    assert first.json()["id"] == second.json()["id"]
    assert len(list(storage_dir.rglob("*.pdf"))) == 1


async def test_duplicate_statement_is_rejected_by_database(session):
    # simula dois uploads simultâneos que passaram pela checagem da aplicação
    user = User(email="race@email.com", hashed_password="hash")
    session.add(user)
    await session.commit()

    await create_statement(
        session, str(user.id), "a.pdf", file_path="a", file_hash="same-hash"
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_statement(
            session, str(user.id), "b.pdf", file_path="b", file_hash="same-hash"
        )

    assert exc_info.value.status_code == 409
