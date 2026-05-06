from sqlmodel import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config import Config


engine = AsyncEngine(create_engine(url=Config.DATABASE_URL))

async def get_session() -> AsyncSession:
    Session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with Session() as session:
        yield session