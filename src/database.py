from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
import logging 

logger = logging.getLogger('uvicorn.error')


DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def init_db():
    logger.info("Connecting to database")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
