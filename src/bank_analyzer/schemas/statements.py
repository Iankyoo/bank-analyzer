import uuid
from datetime import datetime

from pydantic import BaseModel

from bank_analyzer.core.enums import Status


class StatementCreate(BaseModel):
    filename: str


class StatementPublic(BaseModel):
    id: uuid.UUID
    filename: str
    status: Status
    uploaded_at: datetime
    s3_key: str
