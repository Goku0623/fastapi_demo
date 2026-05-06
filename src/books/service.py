from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .schemas import BookCreateModel, BookUpdateModel
from src.db.models import Book

class BookService:
    async def get_all_books(self, session: AsyncSession):
        statement = select(Book).order_by(Book.created_at.desc())
        result = await session.execute(statement=statement)
        return result.scalars().all()

    async def get_book(self, book_uid: str, session: AsyncSession):
        statement = select(Book).where(Book.uid == book_uid)
        result = await session.execute(statement=statement)
        book = result.scalar_one_or_none()
        return book

    async def get_user_books(self, user_uid: str, session: AsyncSession):
        statement = select(Book).where(Book.user_uid == user_uid).order_by(Book.created_at.desc())
        result = await session.execute(statement=statement)
        return result.scalars().all()

    async def create_book(self, book_data: BookCreateModel, user_uid: str, session: AsyncSession):
        book_data_dict = book_data.model_dump()
        new_book = Book(**book_data_dict)
        new_book.user_uid = user_uid
        session.add(new_book)
        await session.commit()
        return new_book

    async def update_book(self, book_uid: str, update_data: BookUpdateModel, session: AsyncSession):
        book_to_update = await self.get_book(book_uid, session)
        if book_to_update is not None:
            update_book_dict = update_data.model_dump()
            for k, v in update_book_dict.items():
                setattr(book_to_update, k, v)
            await session.commit()
            return book_to_update
        else:
            return None

    async def delete_book(self, book_uid: str, session: AsyncSession):
        book_to_delete = await self.get_book(book_uid, session)
        if book_to_delete is not None:
            await session.delete(book_to_delete)
            await session.commit()
            return {}
        else:
            return None

