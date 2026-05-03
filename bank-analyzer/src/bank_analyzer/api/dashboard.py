from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.api.deps import get_current_user
from bank_analyzer.core.database import get_session
from bank_analyzer.models.user import User
from bank_analyzer.services.analytics import analyze_statement

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

templates = Jinja2Templates(directory="src/bank_analyzer/templates")

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/{statement_id}")
async def dashboard(
    request: Request,
    statement_id: str,
    session: Session,
    user: CurrentUser,
):
    analysis = await analyze_statement(statement_id, session)
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "analysis": analysis}
    )
