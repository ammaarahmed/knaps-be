#!/usr/bin/env python3
"""
Test script to verify CTC attributes import and demonstrate querying the data.
"""

import logging
from sqlalchemy.orm import joinedload
from src.database import get_db
from src.db_models import (
    CTCAttribute, CTCAttributeGroup, CTCDataType, CTCUnitOfMeasure, CTCCategory
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_import_verification():
    """Test and verify the imported CTC attributes data"""
    try:
        db = next(get_db())
        
        logger.info("=== CTC Attributes Import Verification ===")
        
        # Count records in each table
        tables = [
            ("CTCAttributeGroup", CTCAttributeGroup),
            ("CTCDataType", CTCDataType),
            ("CTCUnitOfMeasure", CTCUnitOfMeasure),
            ("CTCAttribute", CTCAttribute)
        ]
        
        for table_name, model in tables:
            count = db.query(model).count()
            logger.info(f"{table_name}: {count} records")
        
        # Show some sample data
        logger.info("\n=== Sample Attribute Groups ===")
        groups = db.query(CTCAttributeGroup).limit(5).all()
        for group in groups:
            logger.info(f"  - {group.name} (Code: {group.code}, Store: {group.store})")
        
        logger.info("\n=== Sample Data Types ===")
        data_types = db.query(CTCDataType).limit(5).all()
        for dt in data_types:
            logger.info(f"  - {dt.name} (Code: {dt.code}, Store: {dt.store})")
        
        logger.info("\n=== Sample Units of Measure ===")
        uoms = db.query(CTCUnitOfMeasure).limit(5).all()
        for uom in uoms:
            logger.info(f"  - {uom.name} (Code: {uom.code}, Store: {uom.store})")
        
        logger.info("\n=== Sample Attributes ===")
        attributes = db.query(CTCAttribute).options(
            joinedload(CTCAttribute.attribute_group),
            joinedload(CTCAttribute.data_type),
            joinedload(CTCAttribute.uom)
        ).limit(10).all()
        
        for attr in attributes:
            uom_name = attr.uom.name if attr.uom else "None"
            logger.info(f"  - {attr.name} (Rank: {attr.rank}, Group: {attr.attribute_group.name}, Type: {attr.data_type.name}, UOM: {uom_name})")
        
        # Test some specific queries
        logger.info("\n=== Query Examples ===")
        
        # Find all text attributes
        text_attrs = db.query(CTCAttribute).join(CTCDataType).filter(
            CTCDataType.name == "Text"
        ).limit(5).all()
        logger.info(f"Text attributes found: {len(text_attrs)}")
        
        # Find attributes by store
        qhof_attrs = db.query(CTCAttribute).filter(
            CTCAttribute.store == "QHOF"
        ).count()
        logger.info(f"QHOF store attributes: {qhof_attrs}")
        
        # Find attributes by category
        if attributes:
            sample_category_id = attributes[0].category_id
            category_attrs = db.query(CTCAttribute).filter(
                CTCAttribute.category_id == sample_category_id
            ).count()
            logger.info(f"Attributes for category {sample_category_id}: {category_attrs}")
        
        # Find filterable attributes
        filter_attrs = db.query(CTCAttribute).filter(
            CTCAttribute.as_filter == True
        ).count()
        logger.info(f"Filterable attributes: {filter_attrs}")
        
        logger.info("\n=== Import Verification Complete ===")
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        raise
    finally:
        db.close()


def test_relationships():
    """Test the relationships between tables"""
    try:
        db = next(get_db())
        
        logger.info("=== Testing Relationships ===")
        
        # Test attribute with all relationships
        attr = db.query(CTCAttribute).options(
            joinedload(CTCAttribute.attribute_group),
            joinedload(CTCAttribute.data_type),
            joinedload(CTCAttribute.uom),
            joinedload(CTCAttribute.category)
        ).first()
        
        if attr:
            logger.info(f"Sample attribute: {attr.name}")
            logger.info(f"  - Group: {attr.attribute_group.name}")
            logger.info(f"  - Data Type: {attr.data_type.name}")
            logger.info(f"  - UOM: {attr.uom.name if attr.uom else 'None'}")
            logger.info(f"  - Category: {attr.category.name if attr.category else 'None'}")
        
        # Test reverse relationships
        if attr and attr.attribute_group:
            group_attrs_count = len(attr.attribute_group.attributes)
            logger.info(f"  - Group has {group_attrs_count} attributes")
        
        if attr and attr.data_type:
            type_attrs_count = len(attr.data_type.attributes)
            logger.info(f"  - Data type has {type_attrs_count} attributes")
        
        logger.info("=== Relationship Test Complete ===")
        
    except Exception as e:
        logger.error(f"Error testing relationships: {str(e)}")
        raise
    finally:
        db.close()


def main():
    """Main test function"""
    try:
        logger.info("Starting CTC attributes import verification...")
        
        # Test import verification
        test_import_verification()
        
        # Test relationships
        test_relationships()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    main() 