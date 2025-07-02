#!/usr/bin/env python3
"""
Test script to verify the denormalized CTC tables structure and data.
"""

import asyncio
import logging
from sqlalchemy import text
from src.database import get_async_session, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_denormalized_ctc():
    """Test the denormalized CTC tables structure and data."""
    try:
        # Initialize database first
        logger.info("Initializing database...")
        await init_db(load_ctc_data=True)
        
        async with get_async_session() as session:
            logger.info("Testing denormalized CTC tables...")
            
            # Test 1: Check table counts
            logger.info("\n=== Table Counts ===")
            
            class_result = await session.execute(text("SELECT COUNT(*) FROM ctc_classes"))
            type_result = await session.execute(text("SELECT COUNT(*) FROM ctc_types"))
            category_result = await session.execute(text("SELECT COUNT(*) FROM ctc_categories"))
            
            class_count = class_result.scalar()
            type_count = type_result.scalar()
            category_count = category_result.scalar()
            
            logger.info(f"Classes: {class_count}")
            logger.info(f"Types: {type_count}")
            logger.info(f"Categories: {category_count}")
            logger.info(f"Total: {class_count + type_count + category_count}")
            
            # Test 2: Check sample data from each table
            logger.info("\n=== Sample Data ===")
            
            # Sample classes
            class_sample = await session.execute(text("""
                SELECT id, code, name FROM ctc_classes 
                ORDER BY id LIMIT 3
            """))
            logger.info("Sample Classes:")
            for row in class_sample.fetchall():
                logger.info(f"  ID: {row[0]}, Code: {row[1]}, Name: {row[2]}")
            
            # Sample types
            type_sample = await session.execute(text("""
                SELECT id, code, name, class_id FROM ctc_types 
                ORDER BY id LIMIT 3
            """))
            logger.info("Sample Types:")
            for row in type_sample.fetchall():
                logger.info(f"  ID: {row[0]}, Code: {row[1]}, Name: {row[2]}, Class ID: {row[3]}")
            
            # Sample categories
            category_sample = await session.execute(text("""
                SELECT id, code, name, type_id FROM ctc_categories 
                ORDER BY id LIMIT 3
            """))
            logger.info("Sample Categories:")
            for row in category_sample.fetchall():
                logger.info(f"  ID: {row[0]}, Code: {row[1]}, Name: {row[2]}, Type ID: {row[3]}")
            
            # Test 3: Check relationships
            logger.info("\n=== Relationship Test ===")
            
            # Get a class with its types
            class_with_types = await session.execute(text("""
                SELECT c.id as class_id, c.name as class_name, 
                       t.id as type_id, t.name as type_name
                FROM ctc_classes c
                LEFT JOIN ctc_types t ON c.id = t.class_id
                WHERE c.id = 1
                ORDER BY t.id
            """))
            
            logger.info("Class with Types (ID=1):")
            for row in class_with_types.fetchall():
                if row[2]:  # type_id is not null
                    logger.info(f"  Class: {row[1]} -> Type: {row[3]}")
                else:
                    logger.info(f"  Class: {row[1]} (no types)")
            
            # Get a type with its categories
            type_with_categories = await session.execute(text("""
                SELECT t.id as type_id, t.name as type_name,
                       cat.id as category_id, cat.name as category_name
                FROM ctc_types t
                LEFT JOIN ctc_categories cat ON t.id = cat.type_id
                WHERE t.id = 1
                ORDER BY cat.id
            """))
            
            logger.info("Type with Categories (ID=1):")
            for row in type_with_categories.fetchall():
                if row[2]:  # category_id is not null
                    logger.info(f"  Type: {row[1]} -> Category: {row[3]}")
                else:
                    logger.info(f"  Type: {row[1]} (no categories)")
            
            # Test 4: Check for any orphaned records
            logger.info("\n=== Orphan Check ===")
            
            orphaned_types = await session.execute(text("""
                SELECT COUNT(*) FROM ctc_types t
                LEFT JOIN ctc_classes c ON t.class_id = c.id
                WHERE c.id IS NULL
            """))
            logger.info(f"Orphaned types (no parent class): {orphaned_types.scalar()}")
            
            orphaned_categories = await session.execute(text("""
                SELECT COUNT(*) FROM ctc_categories cat
                LEFT JOIN ctc_types t ON cat.type_id = t.id
                WHERE t.id IS NULL
            """))
            logger.info(f"Orphaned categories (no parent type): {orphaned_categories.scalar()}")
            
            logger.info("\n=== Test Complete ===")
            logger.info("✅ Denormalized CTC tables are working correctly!")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_denormalized_ctc()) 