from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from bank_analyzer.core.config import settings


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
            files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

    assert response.status_code == 200
    assert response.json()["filename"] == "test.pdf"
    assert response.json()["status"] == "pending"
    assert "file_path" not in response.json()

    saved_files = list(storage_dir.rglob("*.pdf"))
    assert len(saved_files) == 1
    assert saved_files[0].read_bytes() == b"fake pdf content"


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
            files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
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
