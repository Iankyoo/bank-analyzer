from http import HTTPStatus

from fastapi import HTTPException

MAX_FILE_SIZE = 10 * 1024 * 1024
PDF_SIGNATURE = b"%PDF-"


def validate_pdf_upload(filename: str | None, contents: bytes) -> None:
    # valida o conteúdo, não os metadados: file.size pode vir nulo e o
    # content-type é só o que o cliente declarou
    if not filename:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="File must have a name"
        )
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="File size exceeds 10MB"
        )
    if not contents.startswith(PDF_SIGNATURE):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Only PDF files are allowed",
        )
