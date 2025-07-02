#!/usr/bin/env python3
"""
Database migration script for CTC attributes tables.
This script creates the necessary tables for storing CTC attributes data.
"""

import logging
from sqlalchemy import text
from src.database import engine, get_db
from src.db_models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_ctc_attributes_tables():
    """Create CTC attributes tables"""
    try:
        logger.info("Creating CTC attributes tables...")
        
        # Create all tables defined in the models
        Base.metadata.create_all(bind=engine)
        
        logger.info("CTC attributes tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            # Check if tables exist
            tables_to_check = [
                'ctc_attribute_groups',
                'ctc_data_types', 
                'ctc_units_of_measure',
                'ctc_attributes'
            ]
            
            for table_name in tables_to_check:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table_name}'
                    );
                """))
                exists = result.scalar()
                if exists:
                    logger.info(f"✓ Table '{table_name}' exists")
                else:
                    logger.error(f"✗ Table '{table_name}' does not exist")
                    
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise


def verify_table_structure():
    """Verify the structure of created tables"""
    try:
        logger.info("Verifying table structure...")
        
        with engine.connect() as conn:
            # Check ctc_attributes table structure
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'ctc_attributes'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            logger.info("ctc_attributes table columns:")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
                
            # Check foreign key constraints
            result = conn.execute(text("""
                SELECT 
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ('ctc_attributes', 'ctc_attribute_groups', 'ctc_data_types', 'ctc_units_of_measure');
            """))
            
            fks = result.fetchall()
            logger.info("Foreign key constraints:")
            for fk in fks:
                logger.info(f"  - {fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]}")
                
    except Exception as e:
        logger.error(f"Error verifying table structure: {str(e)}")
        raise


def create_indexes():
    """Create additional indexes for performance"""
    try:
        logger.info("Creating additional indexes...")
        
        with engine.connect() as conn:
            # Create composite indexes for better query performance
            indexes = [
                ("idx_ctc_attributes_category_rank", 
                 "CREATE INDEX idx_ctc_attributes_category_rank ON ctc_attributes (category_id, rank)"),
                ("idx_ctc_attributes_store_active", 
                 "CREATE INDEX idx_ctc_attributes_store_active ON ctc_attributes (store, active)"),
                ("idx_ctc_attributes_group_type", 
                 "CREATE INDEX idx_ctc_attributes_group_type ON ctc_attributes (attribute_group_id, data_type_id)"),
            ]
            
            for index_name, index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                    logger.info(f"✓ Created index: {index_name}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.info(f"✓ Index {index_name} already exists")
                    else:
                        logger.warning(f"Could not create index {index_name}: {str(e)}")
                        
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
        raise


def main():
    """Main migration function"""
    try:
        logger.info("Starting CTC attributes database migration...")
        
        # Create tables
        create_ctc_attributes_tables()
        
        # Verify structure
        verify_table_structure()
        
        # Create additional indexes
        create_indexes()
        
        logger.info("CTC attributes database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    main() 