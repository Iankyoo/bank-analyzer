from fastapi import FastAPI

from bank_analyzer.api.auth import router as auth_router

app = FastAPI(title="Bank Analyzer")

app.include_router(auth_router)
