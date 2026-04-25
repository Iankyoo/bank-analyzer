from http import HTTPStatus

from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_pdf_upload(file: UploadFile) -> None:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Only PDF files are allowed",
        )
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="File size exceeds 10MB"
        )
    if not file.filename:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="File must have a name"
        )
