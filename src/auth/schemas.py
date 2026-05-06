from pydantic import BaseModel, Field
import uuid
from typing import List
from src.books.schemas import Book
from src.reviews.schemas import ReviewModel
from datetime import datetime


class UserCreateModel(BaseModel):
    username: str = Field(max_length=8)
    email: str = Field(max_length=40)
    password: str = Field(min_length=6, max_length=20)


class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    email: str
    is_verified: bool
    password_hash: str = Field(exclude=True)
    created_at: datetime
    updated_at: datetime


class UserBookModel(UserModel):
    books: List[Book]
    reviews: List[ReviewModel]


class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6, max_length=20)


class EmailModel(BaseModel):
    addresses: List[str]


class PwdResetRequestModel(BaseModel):
    email: str


class PwdResetConfirmModel(BaseModel):
    new_pwd: str
    re_new_pwd: str