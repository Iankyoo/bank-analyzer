import uuid

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str


class UserDB(BaseModel):
    id: uuid.UUID
    email: str
    hashed_password: str
