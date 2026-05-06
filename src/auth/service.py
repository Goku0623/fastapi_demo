from src.db.models import User
from .schemas import UserCreateModel
from .utils import generate_pwd_hash
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select

class UserService:
    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email==email)
        res = await session.execute(statement)
        user = res.scalar_one_or_none()
        return user

    async def user_exists(self, email, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        return False if user is None else True
    
    async def create_user(self, user_data: UserCreateModel, session: AsyncSession):
        user_data_dict = user_data.model_dump()
        new_user = User(
            **user_data_dict
        )
        new_user.password_hash = generate_pwd_hash(user_data_dict["password"])
        new_user.role = "user"
        session.add(new_user)
        await session.commit()
        return new_user
    
    async def update_user(self, user: User, user_data: dict, session: AsyncSession):
        for u, v in user_data.items():
            setattr(user, u, v)
        await session.commit()
        return user