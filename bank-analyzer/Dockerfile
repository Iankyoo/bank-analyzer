FROM python:3.13-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN adduser --disabled-password --gecos '' appuser

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root

COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "bank_analyzer.main:app", "--host", "0.0.0.0", "--port", "8000"]