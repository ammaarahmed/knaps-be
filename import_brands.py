#!/usr/bin/env python3
"""
Standalone script to import brands and distributors data from brands_data.json

Usage:
    python import_brands.py

This script will:
1. Initialize the database connection
2. Import all brands and distributors from brands_data.json
3. Display a summary of the import results
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import init_db
from src.brands_init import initialize_brands_data, get_brands_summary


async def main():
    """Main function to run the brands import"""
    print("Starting brands and distributors import...")
    
    try:
        # Initialize database (don't drop existing tables)
        print("Initializing database connection...")
        await init_db(drop_existing=False)
        
        # Import brands data
        print("Importing brands and distributors data...")
        success = await initialize_brands_data()
        
        if success:
            print("\n✅ Brands data imported successfully!")
            
            # Get and display summary
            print("\n📊 Import Summary:")
            summary = await get_brands_summary()
            
            if summary:
                print(f"  Total Distributors: {summary['total_distributors']}")
                print(f"  Total Brands: {summary['total_brands']}")
                
                if summary['brands_per_distributor']:
                    print("\n  Brands per Distributor:")
                    for dist_code, brand_count in summary['brands_per_distributor'].items():
                        print(f"    {dist_code}: {brand_count} brands")
            else:
                print("  Unable to retrieve summary")
        else:
            print("\n❌ Failed to import brands data")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 