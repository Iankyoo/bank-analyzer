from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.api.deps import get_current_user
from bank_analyzer.api.validators import validate_pdf_upload
from bank_analyzer.core.database import get_session
from bank_analyzer.models.user import User
from bank_analyzer.schemas.statements import StatementPublic
from bank_analyzer.services.statement import create_statement
from bank_analyzer.services.storage import upload_file

router = APIRouter(prefix="/statements", tags=["statements"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/upload", response_model=StatementPublic, status_code=HTTPStatus.OK)
async def upload(session: Session, user: CurrentUser, file: UploadFile):
    validate_pdf_upload(file)

    s3_key = await upload_file(file=file, user_id=str(user.id))
    statement = await create_statement(
        session=session, filename=file.filename, user_id=str(user.id)
    )

    return statement
