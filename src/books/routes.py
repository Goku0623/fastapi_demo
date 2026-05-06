from fastapi import status, APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from typing import List
from src.books.service import BookService
from src.books.schemas import Book, BookCreateModel, BookUpdateModel, BookDetailModel
from src.db.main import get_session
from src.auth.dependencies import AccessTokenBear, RoleChecker
from src.errors import BookNotFound


book_router = APIRouter()
book_service = BookService()
access_token_bear = AccessTokenBear()
role_checker = Depends(RoleChecker(["admin", "user"]))

@book_router.get("/", response_model=List[Book], dependencies=[role_checker])
async def get_all_books(
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bear)
):
    """获取全部书籍"""
    books = await book_service.get_all_books(session)
    return books


@book_router.get("/user/{user_uid}", response_model=List[Book], dependencies=[role_checker])
async def get_user_book_submissions(
    user_uid: str,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bear)
):
    """获取用户提交的所有书籍"""
    books = await book_service.get_user_books(user_uid, session)
    return books


@book_router.post("/", status_code=status.HTTP_201_CREATED, response_model=Book, dependencies=[role_checker])
async def create_a_book(
    book_data: BookCreateModel, 
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bear)
):
    """新增某本书"""
    user_id = token_details.get("user")["user_uid"]
    new_book = await book_service.create_book(book_data, user_id, session)
    return new_book


@book_router.get("/{book_uid}", response_model=BookDetailModel, dependencies=[role_checker])
async def get_book(book_uid: str, 
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bear)
):
    """获取某本书"""
    book = await book_service.get_book(book_uid, session)
    if book:
        return book
    else:
        raise BookNotFound()
    

@book_router.patch("/{book_uid}", response_model=Book, dependencies=[role_checker])
async def update_book(book_uid: str, 
    book_update_data: BookUpdateModel, 
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bear)
):
    """更新某本书"""
    updated_book = await book_service.update_book(book_uid, book_update_data, session)
    if updated_book is None:
        raise BookNotFound()   
    else:
        return updated_book


@book_router.delete("/{book_uid}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[role_checker])
async def delete_book(book_uid: str,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bear)
):
    deleted_book = await book_service.delete_book(book_uid, session)
    if deleted_book is None:
        raise BookNotFound()
    else:
        return {}