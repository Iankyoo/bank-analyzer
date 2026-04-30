from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from bank_analyzer.api.validators import validate_pdf_upload


def make_upload_file(content_type="application/pdf", size=1000, filename="test.pdf"):
    f = MagicMock()
    f.content_type = content_type
    f.size = size
    f.filename = filename
    return f


def test_valid_pdf():
    file = make_upload_file()
    validate_pdf_upload(file)  # não deve lançar exceção


def test_invalid_content_type():
    file = make_upload_file(content_type="image/png")

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_upload(file)

    assert exc_info.value.status_code == 422


def test_file_too_large():
    file = make_upload_file(size=11 * 1024 * 1024)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_upload(file)

    assert exc_info.value.status_code == 422


def test_missing_filename():
    file = make_upload_file(filename=None)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_upload(file)

    assert exc_info.value.status_code == 422
