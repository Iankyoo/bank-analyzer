from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.api.deps import get_current_user
from bank_analyzer.api.validators import validate_pdf_upload
from bank_analyzer.core.database import get_session
from bank_analyzer.models.user import User
from bank_analyzer.schemas.analytics import StatementAnalysis
from bank_analyzer.schemas.statements import StatementPublic
from bank_analyzer.services.analytics import analyze_statement
from bank_analyzer.services.parser import process_statement
from bank_analyzer.services.statement import create_statement, get_statement_by_hash
from bank_analyzer.services.storage import calculate_file_hash, upload_file

router = APIRouter(prefix="/statements", tags=["statements"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/upload", response_model=StatementPublic, status_code=HTTPStatus.OK)
async def upload(
    session: Session,
    user: CurrentUser,
    file: UploadFile,
    background_tasks: BackgroundTasks,
):
    validate_pdf_upload(file)

    contents = await file.read()
    file_hash = calculate_file_hash(contents)

    existing = await get_statement_by_hash(session, str(user.id), file_hash)
    if existing:
        return existing

    await file.seek(0)
    s3_key = await upload_file(file=file, user_id=str(user.id))
    statement = await create_statement(
        session=session,
        filename=file.filename,
        user_id=str(user.id),
        s3_key=s3_key,
        file_hash=file_hash,
    )

    background_tasks.add_task(process_statement, str(statement.id), s3_key)
    return statement


@router.get(
    "/{statement_id}/analysis",
    response_model=StatementAnalysis,
    status_code=HTTPStatus.OK,
)
async def get_analysis(
    statement_id: str,
    session: Session,
    user: CurrentUser,
):
    return await analyze_statement(statement_id, session)
