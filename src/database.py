from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, text
import logging 
import json
import pandas as pd
import asyncio
import os

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
        # Use CASCADE to handle foreign key dependencies
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    logger.info("All tables dropped successfully")

async def init_db(drop_existing: bool = True, load_ctc_data: bool = False, load_brands_data: bool = False):
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
    
    # Load CTC data if requested
    if load_ctc_data:
        try:
            logger.info("Initializing CTC categories data...")
            from .ctc_init import initialize_ctc_categories
            
            # Run the async initialization directly
            success = await initialize_ctc_categories()
            
            if success:
                logger.info("CTC categories data initialized successfully")
            else:
                logger.warning("CTC categories initialization failed or not needed")
        except Exception as e:
            logger.error(f"Failed to initialize CTC data: {e}")
            # Don't fail the entire startup if CTC loading fails
    
    # Load brands data if requested
    if load_brands_data:
        try:
            logger.info("Initializing brands and distributors data...")
            from .brands_init import initialize_brands_data
            
            # Run the async initialization directly
            success = await initialize_brands_data()
            
            if success:
                logger.info("Brands and distributors data initialized successfully")
            else:
                logger.warning("Brands and distributors initialization failed or not needed")
        except Exception as e:
            logger.error(f"Failed to initialize brands data: {e}")
            # Don't fail the entire startup if brands loading fails

def get_async_session():
    """Get the async session factory. Raises an error if not initialized."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return AsyncSessionLocal()

def get_database_url():
    """Get the database URL for synchronous operations."""
    from .config import settings
    return settings.database_url
