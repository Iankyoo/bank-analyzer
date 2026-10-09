import pytest
from fastapi import HTTPException

from bank_analyzer.api.validators import MAX_FILE_SIZE, validate_pdf_upload

PDF = b"%PDF-1.4 conteudo"


def assert_rejected(filename, contents):
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_upload(filename, contents)
    assert exc_info.value.status_code == 422


def test_valid_pdf():
    validate_pdf_upload("extrato.pdf", PDF)  # não deve lançar exceção


def test_rejects_file_that_is_not_pdf_even_with_pdf_name():
    assert_rejected("extrato.pdf", b"\x89PNG\r\n imagem renomeada")


def test_rejects_empty_file():
    assert_rejected("extrato.pdf", b"")


def test_rejects_file_too_large():
    assert_rejected("extrato.pdf", PDF + b"0" * MAX_FILE_SIZE)


def test_rejects_missing_filename():
    assert_rejected(None, PDF)
