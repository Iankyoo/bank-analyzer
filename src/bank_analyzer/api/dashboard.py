from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.api.deps import get_current_user_from_cookie
from bank_analyzer.core.database import get_session
from bank_analyzer.core.limiter import limiter
from bank_analyzer.core.security import create_access_token
from bank_analyzer.models.statement import Statement
from bank_analyzer.models.user import User
from bank_analyzer.services.analytics import analyze_statement
from bank_analyzer.services.auth import authenticate_user

router = APIRouter(tags=["dashboard"])

templates = Jinja2Templates(directory="src/bank_analyzer/templates")

Session = Annotated[AsyncSession, Depends(get_session)]
CookieUser = Annotated[User, Depends(get_current_user_from_cookie)]


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    session: Session,
    username: str = Form(...),
    password: str = Form(...),
):
    try:
        user = await authenticate_user(username, password, session)
    except HTTPException:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Email ou senha incorretos"},
        )

    token = create_access_token({"sub": user.email})
    response = RedirectResponse(url="/statements", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return response


@router.get("/dashboard/{statement_id}")
async def dashboard(
    request: Request, statement_id: str, session: Session, user: CookieUser
):
    analysis = await analyze_statement(statement_id, str(user.id), session)
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context={"analysis": analysis}
    )


@router.get("/statements")
async def statements_list(request: Request, session: Session, user: CookieUser):
    result = await session.execute(
        select(Statement)
        .where(Statement.user_id == user.id)
        .order_by(Statement.uploaded_at.desc())
    )
    statements = result.scalars().all()

    return templates.TemplateResponse(
        request=request, name="statements.html", context={"statements": statements}
    )
