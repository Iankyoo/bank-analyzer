import uuid

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr


class UserDB(BaseModel):
    id: uuid.UUID
    email: EmailStr
    hashed_password: str
