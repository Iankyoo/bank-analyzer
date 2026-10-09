import io
from unittest.mock import AsyncMock, MagicMock, patch

from bank_analyzer.core.config import settings
from bank_analyzer.core.enums import Status
from bank_analyzer.services.parser import (
    extract_text_from_pdf,
    process_statement,
    read_pdf,
)
from bank_analyzer.services.storage import save_file


def test_read_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_DIR", str(tmp_path))
    file_path = save_file(contents=b"fake pdf content", user_id="user_id")

    result = read_pdf(file_path)

    assert isinstance(result, io.BytesIO)
    assert result.read() == b"fake pdf content"


def test_extract_text_from_pdf():
    with patch("bank_analyzer.services.parser.pdfplumber") as mock_plumber:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Salary 1000.00"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_plumber.open.return_value.__enter__.return_value = mock_pdf

        file_obj = io.BytesIO(b"fake pdf")
        result = extract_text_from_pdf(file_obj)

        assert result == "Salary 1000.00"


def _mock_session_context(mock_session):
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__.return_value = mock_session
    mock_session_cm.__aexit__.return_value = None
    return mock_session_cm


async def test_process_statement_query_failure_does_not_raise():
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("db down")

    with patch(
        "bank_analyzer.services.parser.SessionLocal",
        return_value=_mock_session_context(mock_session),
    ):
        await process_statement("some-id", "some-path")

    mock_session.rollback.assert_awaited_once()
    mock_session.commit.assert_not_awaited()


async def test_process_statement_processing_failure_sets_error_status():
    fake_statement = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_statement

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    with (
        patch(
            "bank_analyzer.services.parser.SessionLocal",
            return_value=_mock_session_context(mock_session),
        ),
        patch(
            "bank_analyzer.services.parser.read_pdf",
            side_effect=FileNotFoundError("file missing"),
        ),
    ):
        await process_statement("some-id", "some-path")

    assert fake_statement.status == Status.ERROR
    mock_session.rollback.assert_awaited_once()
