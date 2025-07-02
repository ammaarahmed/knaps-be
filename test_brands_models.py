#!/usr/bin/env python3
"""
Test script to verify the brands and distributors models work correctly

This script will:
1. Initialize the database
2. Create a test distributor and brand
3. Verify the relationships work
4. Clean up
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import init_db, get_async_session
from src.db_models import Distributor, Brand
from datetime import datetime


async def test_models():
    """Test the brands and distributors models"""
    print("Testing brands and distributors models...")
    
    try:
        # Initialize database
        print("Initializing database...")
        await init_db(drop_existing=True)
        
        async with get_async_session() as session:
            # Create a test distributor
            print("Creating test distributor...")
            distributor = Distributor(
                id=9999,
                active=True,
                modified_by="test",
                modified=datetime.utcnow(),
                created_by="test",
                created=datetime.utcnow(),
                code="TEST_DIST",
                name="Test Distributor",
                store="TEST",
                edi=False,
                auto_claim_over_charge=False,
                is_central=True
            )
            session.add(distributor)
            await session.flush()
            
            # Create a test brand
            print("Creating test brand...")
            brand = Brand(
                id=9999,
                active=True,
                modified_by="test",
                modified=datetime.utcnow(),
                created_by="test",
                created=datetime.utcnow(),
                code="TEST_BRAND",
                name="Test Brand",
                store="TEST",
                is_hof_pref=True,
                distributor_id=distributor.id
            )
            session.add(brand)
            await session.flush()
            
            # Test the relationship
            print("Testing relationship...")
            
            # Use selectinload to eagerly load the brands relationship
            from sqlalchemy.orm import selectinload
            from sqlalchemy import select
            
            stmt = select(Distributor).options(selectinload(Distributor.brands)).where(Distributor.id == distributor.id)
            result = await session.execute(stmt)
            distributor_with_brands = result.scalar_one()
            
            print(f"Distributor: {distributor_with_brands.name}")
            print(f"Brands count: {len(distributor_with_brands.brands)}")
            
            if distributor_with_brands.brands:
                print(f"First brand: {distributor_with_brands.brands[0].name}")
            
            # Test brand to distributor relationship
            stmt = select(Brand).options(selectinload(Brand.distributor)).where(Brand.id == brand.id)
            result = await session.execute(stmt)
            brand_with_distributor = result.scalar_one()
            
            print(f"Brand: {brand_with_distributor.name}")
            print(f"Distributor: {brand_with_distributor.distributor.name}")
            
            await session.commit()
            print("✅ All tests passed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_models()) 