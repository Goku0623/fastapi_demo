from fastapi import status
from fastapi.exceptions import HTTPException
from sqlmodel import desc, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.books.service import BookService
from src.db.models import Tag

from .schemas import TagAddModel, TagCreateModel
from src.errors import BookNotFound, TagNotFound, TagAlreadyExists

book_service = BookService()


server_error = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="出现了一些错误"
)


class TagService:

    async def get_tags(self, session: AsyncSession):
        """获取全部标签"""

        statement = select(Tag).order_by(Tag.created_at.desc())

        result = await session.execute(statement)

        return result.scalars().all()


    async def add_tags_to_book(
        self, book_uid: str, tag_data: TagAddModel, session: AsyncSession
    ):
        """向某本书增加标签"""

        book = await book_service.get_book(book_uid=book_uid, session=session)

        if not book:
            raise BookNotFound()

        for tag_item in tag_data.tags:
            result = await session.execute(select(Tag).where(Tag.name == tag_item.name))

            tag = result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_item.name)

            book.tags.append(tag)
        session.add(book)
        await session.commit()
        await session.refresh(book)
        return book


    async def get_tag_by_uid(self, tag_uid: str, session: AsyncSession):
        """通过uid获取标签"""

        statement = select(Tag).where(Tag.uid == tag_uid)

        result = await session.execute(statement)

        return result.scalar_one_or_none()


    async def add_tag(self, tag_data: TagCreateModel, session: AsyncSession):
        """新增标签"""

        statement = select(Tag).where(Tag.name == tag_data.name)

        result = await session.execute(statement)

        tag = result.scalar_one_or_none()

        if tag:
            raise TagAlreadyExists()
        new_tag = Tag(name=tag_data.name)

        session.add(new_tag)

        await session.commit()

        return new_tag


    async def update_tag(
        self, tag_uid, tag_update_data: TagCreateModel, session: AsyncSession
    ):
        """更新标签"""

        tag = await self.get_tag_by_uid(tag_uid, session)

        if not tag:
            raise TagNotFound()

        update_data_dict = tag_update_data.model_dump()

        for k, v in update_data_dict.items():
            setattr(tag, k, v)

            await session.commit()

            await session.refresh(tag)

        return tag


    async def delete_tag(self, tag_uid: str, session: AsyncSession):
        """删除标签"""

        tag = await self.get_tag_by_uid(tag_uid,session)

        if not tag:
            raise TagNotFound()

        await session.delete(tag)

        await session.commit()
