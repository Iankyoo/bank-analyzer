from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from bank_analyzer.api.auth import router as auth_router
from bank_analyzer.api.dashboard import router as dashboard_router
from bank_analyzer.api.statements import router as upload_router
from bank_analyzer.core.limiter import limiter

app = FastAPI(
    title="Bank Analyzer API",
    description="Intelligent bank statement analyzer with AI categorization",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(dashboard_router)
