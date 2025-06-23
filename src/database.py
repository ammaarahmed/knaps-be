from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import logging 

logger = logging.getLogger('uvicorn.error')

# Remove the circular import - we'll get settings when needed
# DATABASE_URL = settings.database_url

# We'll create the engine when init_db is called
engine = None
AsyncSessionLocal = None
Base = declarative_base()

async def drop_all_tables():
    """Drop all tables from the database."""
    if engine is None:
        logger.warning("Engine not initialized, cannot drop tables")
        return
    
    logger.info("Dropping all tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("All tables dropped successfully")
    


async def init_db(drop_existing: bool = True):
    from .config import settings  # Local import to avoid circular dependency
    global engine, AsyncSessionLocal
    DATABASE_URL = settings.database_url

    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    logger.info("Connecting to database")

    # Import models to ensure they are registered with SQLAlchemy
    from . import db_models

    if drop_existing:
        await drop_all_tables()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def get_async_session():
    """Get the async session factory. Raises an error if not initialized."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return AsyncSessionLocal()
