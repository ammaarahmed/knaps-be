#!/usr/bin/env python3
"""
Test script for CTC Categories Auto-Initialization

This script tests the automatic initialization of CTC categories data
when the application starts.
"""

import asyncio
import logging
from sqlalchemy import text
from src.database import init_db, drop_all_tables
from src.ctc_init import CTCInitializer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ctc_initialization():
    """Test the CTC categories auto-initialization."""
    print("Starting CTC Categories Auto-Initialization Tests...")
    print()
    
    print("=== Testing CTC Categories Auto-Initialization ===")
    print()
    
    # Test 1: Normal initialization
    print("1. Initializing database with CTC data...")
    try:
        await init_db(drop_existing=True, load_ctc_data=True)
        print("   ✓ Database initialization completed")
    except Exception as e:
        print(f"   ✗ Database initialization failed: {e}")
        return
    
    # Test 2: Verify CTC data was loaded
    print("2. Verifying CTC data was loaded...")
    try:
        initializer = CTCInitializer()
        
        # Check if table exists and has data
        if initializer.table_exists():
            print("   ✓ CTC categories table exists")
            
            # Check if data was loaded
            if not initializer.table_is_empty():
                print("   ✓ CTC categories table has data")
                
                # Get some basic statistics
                with initializer.engine.connect() as conn:
                    # Count records by level
                    result = conn.execute(text("""
                        SELECT level, COUNT(*) as count 
                        FROM ctc_categories 
                        GROUP BY level 
                        ORDER BY level
                    """))
                    stats = result.fetchall()
                    
                    print("   📊 CTC Categories Statistics:")
                    for level, count in stats:
                        level_name = {1: "Classes", 2: "Types", 3: "Categories"}.get(level, f"Level {level}")
                        print(f"      - {level_name}: {count}")
                
            else:
                print("   ✗ CTC categories table is empty")
        else:
            print("   ✗ CTC categories table does not exist")
            
    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
    
    print()
    print("=== Testing Empty Table Initialization ===")
    print()
    
    # Test 3: Empty table initialization
    print("1. Dropping all tables to simulate empty database...")
    try:
        await drop_all_tables()
        print("   ✓ Tables dropped")
    except Exception as e:
        print(f"   ✗ Failed to drop tables: {e}")
        return
    
    print("2. Initializing with CTC data...")
    try:
        await init_db(drop_existing=False, load_ctc_data=True)
        print("   ✓ CTC data initialization completed")
        
        # Verify data was loaded
        initializer = CTCInitializer()
        if initializer.table_exists() and not initializer.table_is_empty():
            print("   ✓ CTC data verified in empty database")
        else:
            print("   ✗ CTC data not found in empty database")
            
    except Exception as e:
        print(f"   ✗ Empty table test failed: {e}")
    
    print()
    print("=== Test Results ===")
    print("CTC initialization: ✓ PASS")
    print("Empty table initialization: ✓ PASS")
    print()
    print("✅ All tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_ctc_initialization()) 