from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bank_analyzer.core.database import get_session
from bank_analyzer.core.security import create_access_token, decode_access_token
from bank_analyzer.models.statement import Statement
from bank_analyzer.models.user import User
from bank_analyzer.services.analytics import analyze_statement
from bank_analyzer.services.auth import authenticate_user

router = APIRouter(tags=["dashboard"])

templates = Jinja2Templates(directory="src/bank_analyzer/templates")

Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/login")
async def login(
    request: Request,
    session: Session,
    username: str = Form(...),
    password: str = Form(...),
):
    try:
        user = await authenticate_user(username, password, session)
        token = create_access_token({"sub": user.email})
        response = RedirectResponse(url="/statements", status_code=302)
        response.set_cookie(key="access_token", value=token, httponly=True)
        return response
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Email ou senha incorretos"},
        )


@router.get("/dashboard/{statement_id}")
async def dashboard(
    request: Request,
    statement_id: str,
    session: Session,
    access_token: str = Cookie(default=None),
):
    if not access_token:
        return RedirectResponse(url="/login")

    try:
        decode_access_token(access_token)
    except Exception:
        return RedirectResponse(url="/login")

    analysis = await analyze_statement(statement_id, session)
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context={"analysis": analysis}
    )


@router.get("/statements")
async def statements_list(
    request: Request,
    session: Session,
    access_token: str = Cookie(default=None),
):
    if not access_token:
        return RedirectResponse(url="/login")

    try:
        email = decode_access_token(access_token)
    except Exception:
        return RedirectResponse(url="/login")

    # busca usuário pelo email
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # busca statements do usuário
    result = await session.execute(
        select(Statement).where(Statement.user_id == user.id)
    )
    statements = result.scalars().all()

    return templates.TemplateResponse(
        request=request, name="statements.html", context={"statements": statements}
    )
