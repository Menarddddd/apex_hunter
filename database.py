from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from settings import settings

engine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(),
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """
    yield async session for db transactions
    """
    async with AsyncSessionLocal.begin() as db:
        yield db
