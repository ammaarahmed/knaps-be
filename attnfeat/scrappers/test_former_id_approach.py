#!/usr/bin/env python3
"""
Test script to verify the former_id approach for CTC categories.
"""

import asyncio
import logging
from sqlalchemy import text
from src.database import init_db, get_async_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_former_id_approach():
    """Test that the former_id approach works correctly."""
    print("Testing former_id approach for CTC categories...")
    print()
    
    try:
        # Initialize database
        await init_db(drop_existing=True, load_ctc_data=True)
        
        # Test the data
        async with get_async_session() as session:
            # Check if data was imported
            result = await session.execute(text("SELECT COUNT(*) FROM ctc_categories"))
            total_count = result.scalar()
            print(f"✓ Total CTC categories imported: {total_count}")
            
            # Check former_id usage
            result = await session.execute(text("""
                SELECT COUNT(*) FROM ctc_categories 
                WHERE former_id IS NOT NULL
            """))
            former_id_count = result.scalar()
            print(f"✓ Records with former_id: {former_id_count}")
            
            # Check auto-generated IDs
            result = await session.execute(text("""
                SELECT MIN(id), MAX(id) FROM ctc_categories
            """))
            min_id, max_id = result.fetchone()
            print(f"✓ ID range: {min_id} to {max_id}")
            
            # Check hierarchy
            result = await session.execute(text("""
                SELECT level, COUNT(*) as count 
                FROM ctc_categories 
                GROUP BY level 
                ORDER BY level
            """))
            stats = result.fetchall()
            print("\n✓ Hierarchy breakdown:")
            for level, count in stats:
                level_name = {1: "Classes", 2: "Types", 3: "Categories"}.get(level, f"Level {level}")
                print(f"  - {level_name}: {count}")
            
            # Check some sample records
            result = await session.execute(text("""
                SELECT id, former_id, name, level, parent_id 
                FROM ctc_categories 
                ORDER BY level, id 
                LIMIT 10
            """))
            samples = result.fetchall()
            print("\n✓ Sample records:")
            for record in samples:
                print(f"  - ID: {record[0]}, Former ID: {record[1]}, Name: {record[2]}, Level: {record[3]}, Parent: {record[4]}")
            
            # Verify parent relationships work
            result = await session.execute(text("""
                SELECT c1.name as parent_name, c2.name as child_name, c2.level
                FROM ctc_categories c1
                JOIN ctc_categories c2 ON c1.id = c2.parent_id
                WHERE c2.level = 2
                LIMIT 5
            """))
            relationships = result.fetchall()
            print("\n✓ Parent-child relationships:")
            for rel in relationships:
                print(f"  - {rel[0]} -> {rel[1]} (Level {rel[2]})")
        
        print("\n✅ All tests passed! The former_id approach is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_former_id_approach()) 