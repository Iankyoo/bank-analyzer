from fastapi import FastAPI

from bank_analyzer.api.auth import router as auth_router
from bank_analyzer.api.statements import router as upload_router

app = FastAPI(title="Bank Analyzer")

app.include_router(auth_router)
app.include_router(upload_router)
