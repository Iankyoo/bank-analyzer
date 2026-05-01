from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def test_upload_statement(client: AsyncClient, auth_token: str):
    with patch("bank_analyzer.services.storage.s3_client") as mock_s3:
        mock_s3.upload_fileobj = AsyncMock(return_value=None)

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


async def test_upload_invalid_file_type(client: AsyncClient, auth_token: str):
    response = await client.post(
        "/statements/upload",
        files={"file": ("test.png", b"fake image content", "image/png")},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422
