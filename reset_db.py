#!/usr/bin/env python3
"""
Script to drop and recreate all database tables.
This will delete all data in the database.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import init_db

async def main():
    print("⚠️  WARNING: This will delete ALL data in your database!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    print("Dropping and recreating all tables...")
    await init_db(drop_existing=True)
    print("✅ Database reset complete!")

if __name__ == "__main__":
    asyncio.run(main()) 