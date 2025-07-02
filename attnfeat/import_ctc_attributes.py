#!/usr/bin/env python3
"""
Script to import CTC attributes data from JSON into the database.
This script handles the hierarchical structure of CTC attributes including:
- Attribute Groups
- Data Types  
- Units of Measure
- Individual Attributes
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import get_db, engine
from src.db_models import (
    Base, CTCAttributeGroup, CTCDataType, CTCUnitOfMeasure, 
    CTCAttribute, CTCCategory
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CTCAttributesImporter:
    """Handles the import of CTC attributes data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.attribute_groups_cache: Dict[str, CTCAttributeGroup] = {}
        self.data_types_cache: Dict[str, CTCDataType] = {}
        self.units_of_measure_cache: Dict[str, CTCUnitOfMeasure] = {}
        self.categories_cache: Dict[int, CTCCategory] = {}
        
    def parse_datetime(self, dt_str: str) -> datetime:
        """Parse datetime string to datetime object"""
        if not dt_str:
            return datetime.utcnow()
        try:
            # Handle timezone info if present
            if '+' in dt_str or dt_str.endswith('Z'):
                # Remove timezone info for simplicity
                dt_str = dt_str.split('+')[0].split('Z')[0]
            return datetime.fromisoformat(dt_str.replace('T', ' '))
        except ValueError:
            logger.warning(f"Could not parse datetime: {dt_str}, using current time")
            return datetime.utcnow()
    
    def get_or_create_attribute_group(self, group_data: Dict[str, Any]) -> CTCAttributeGroup:
        """Get or create an attribute group"""
        cache_key = f"{group_data['store']}_{group_data['code']}_{group_data['name']}"
        
        if cache_key in self.attribute_groups_cache:
            return self.attribute_groups_cache[cache_key]
        
        # Check if exists in database
        existing = self.db.query(CTCAttributeGroup).filter(
            CTCAttributeGroup.store == group_data['store'],
            CTCAttributeGroup.code == group_data['code'],
            CTCAttributeGroup.name == group_data['name']
        ).first()
        
        if existing:
            self.attribute_groups_cache[cache_key] = existing
            return existing
        
        # Create new attribute group
        new_group = CTCAttributeGroup(
            uuid=str(uuid.uuid4()),
            active=group_data.get('active', True),
            modified_by=group_data.get('modified_by', 'system'),
            modified=self.parse_datetime(group_data.get('modified', '')),
            created_by=group_data.get('created_by', 'system'),
            created=self.parse_datetime(group_data.get('created', '')),
            deleted_by=group_data.get('deleted_by'),
            deleted=self.parse_datetime(group_data.get('deleted', '')) if group_data.get('deleted') else None,
            code=group_data.get('code', ''),
            name=group_data.get('name', ''),
            store=group_data.get('store', '')
        )
        
        self.db.add(new_group)
        self.db.flush()  # Get the ID
        self.attribute_groups_cache[cache_key] = new_group
        logger.info(f"Created attribute group: {new_group.name}")
        
        return new_group
    
    def get_or_create_data_type(self, data_type_data: Dict[str, Any]) -> CTCDataType:
        """Get or create a data type"""
        cache_key = f"{data_type_data['store']}_{data_type_data['code']}_{data_type_data['name']}"
        
        if cache_key in self.data_types_cache:
            return self.data_types_cache[cache_key]
        
        # Check if exists in database
        existing = self.db.query(CTCDataType).filter(
            CTCDataType.store == data_type_data['store'],
            CTCDataType.code == data_type_data['code'],
            CTCDataType.name == data_type_data['name']
        ).first()
        
        if existing:
            self.data_types_cache[cache_key] = existing
            return existing
        
        # Create new data type
        new_data_type = CTCDataType(
            uuid=str(uuid.uuid4()),
            active=data_type_data.get('active', True),
            modified_by=data_type_data.get('modified_by', 'system'),
            modified=self.parse_datetime(data_type_data.get('modified', '')),
            created_by=data_type_data.get('created_by', 'system'),
            created=self.parse_datetime(data_type_data.get('created', '')),
            deleted_by=data_type_data.get('deleted_by'),
            deleted=self.parse_datetime(data_type_data.get('deleted', '')) if data_type_data.get('deleted') else None,
            code=data_type_data.get('code', ''),
            name=data_type_data.get('name', ''),
            store=data_type_data.get('store', '')
        )
        
        self.db.add(new_data_type)
        self.db.flush()  # Get the ID
        self.data_types_cache[cache_key] = new_data_type
        logger.info(f"Created data type: {new_data_type.name}")
        
        return new_data_type
    
    def get_or_create_unit_of_measure(self, uom_data: Optional[Dict[str, Any]]) -> Optional[CTCUnitOfMeasure]:
        """Get or create a unit of measure"""
        if not uom_data:
            return None
            
        cache_key = f"{uom_data['store']}_{uom_data['code']}_{uom_data['name']}"
        
        if cache_key in self.units_of_measure_cache:
            return self.units_of_measure_cache[cache_key]
        
        # Check if exists in database
        existing = self.db.query(CTCUnitOfMeasure).filter(
            CTCUnitOfMeasure.store == uom_data['store'],
            CTCUnitOfMeasure.code == uom_data['code'],
            CTCUnitOfMeasure.name == uom_data['name']
        ).first()
        
        if existing:
            self.units_of_measure_cache[cache_key] = existing
            return existing
        
        # Create new unit of measure
        new_uom = CTCUnitOfMeasure(
            uuid=str(uuid.uuid4()),
            active=uom_data.get('active', True),
            modified_by=uom_data.get('modified_by', 'system'),
            modified=self.parse_datetime(uom_data.get('modified', '')),
            created_by=uom_data.get('created_by', 'system'),
            created=self.parse_datetime(uom_data.get('created', '')),
            deleted_by=uom_data.get('deleted_by'),
            deleted=self.parse_datetime(uom_data.get('deleted', '')) if uom_data.get('deleted') else None,
            code=uom_data.get('code', ''),
            name=uom_data.get('name', ''),
            store=uom_data.get('store', '')
        )
        
        self.db.add(new_uom)
        self.db.flush()  # Get the ID
        self.units_of_measure_cache[cache_key] = new_uom
        logger.info(f"Created unit of measure: {new_uom.name}")
        
        return new_uom
    
    def get_category(self, category_id: int) -> Optional[CTCCategory]:
        """Get a category by its ID"""
        if category_id in self.categories_cache:
            return self.categories_cache[category_id]
        
        category = self.db.query(CTCCategory).filter(CTCCategory.id == category_id).first()
        if category:
            self.categories_cache[category_id] = category
        
        return category
    
    def import_attributes_for_category(self, category_data: Dict[str, Any]) -> None:
        """Import all attributes for a specific category"""
        category_id = category_data['category_id']
        attributes = category_data.get('attributes', [])
        scraped_at = self.parse_datetime(category_data.get('scraped_at', ''))
        
        # Get the category
        category = self.get_category(category_id)
        if not category:
            logger.warning(f"Category {category_id} not found, skipping attributes")
            return
        
        logger.info(f"Importing {len(attributes)} attributes for category {category_id}")
        
        for attr_data in attributes:
            try:
                # Get or create related entities
                attribute_group = self.get_or_create_attribute_group(attr_data['attribute_group'])
                data_type = self.get_or_create_data_type(attr_data['data_type'])
                uom = self.get_or_create_unit_of_measure(attr_data.get('uom'))
                
                # Check if attribute already exists
                existing_attr = self.db.query(CTCAttribute).filter(
                    CTCAttribute.id == attr_data['id']
                ).first()
                
                if existing_attr:
                    logger.info(f"Attribute {attr_data['id']} already exists, skipping")
                    continue
                
                # Create new attribute
                new_attribute = CTCAttribute(
                    id=attr_data['id'],  # Use original ID
                    uuid=str(uuid.uuid4()),
                    active=attr_data.get('active', True),
                    modified_by=attr_data.get('modified_by', 'system'),
                    modified=self.parse_datetime(attr_data.get('modified', '')),
                    created_by=attr_data.get('created_by', 'system'),
                    created=self.parse_datetime(attr_data.get('created', '')),
                    deleted_by=attr_data.get('deleted_by'),
                    deleted=self.parse_datetime(attr_data.get('deleted', '')) if attr_data.get('deleted') else None,
                    name=attr_data.get('name', ''),
                    store=attr_data.get('store', ''),
                    rank=attr_data.get('rank', 0),
                    as_filter=attr_data.get('as_filter', False),
                    scraped_at=scraped_at,
                    category_id=category_id,
                    attribute_group_id=attribute_group.id,
                    data_type_id=data_type.id,
                    uom_id=uom.id if uom else None
                )
                
                self.db.add(new_attribute)
                logger.info(f"Created attribute: {new_attribute.name} (ID: {new_attribute.id})")
                
            except Exception as e:
                logger.error(f"Error importing attribute {attr_data.get('id', 'unknown')}: {str(e)}")
                self.db.rollback()
                continue
    
    def import_all_attributes(self, json_file_path: str) -> None:
        """Import all CTC attributes from JSON file"""
        try:
            logger.info(f"Loading data from {json_file_path}")
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Found {len(data)} category entries to process")
            
            for i, category_data in enumerate(data, 1):
                try:
                    logger.info(f"Processing category {i}/{len(data)}: {category_data.get('category_id', 'unknown')}")
                    self.import_attributes_for_category(category_data)
                    
                    # Commit every 100 records to avoid large transactions
                    if i % 100 == 0:
                        self.db.commit()
                        logger.info(f"Committed {i} categories")
                        
                except Exception as e:
                    logger.error(f"Error processing category {category_data.get('category_id', 'unknown')}: {str(e)}")
                    self.db.rollback()
                    continue
            
            # Final commit
            self.db.commit()
            logger.info("Import completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during import: {str(e)}")
            self.db.rollback()
            raise


def create_tables():
    """Create all tables if they don't exist"""
    logger.info("Creating tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully!")


def main():
    """Main function to run the import"""
    import uuid  # Import here to avoid circular import
    
    try:
        # Create tables
        create_tables()
        
        # Get database session
        db = next(get_db())
        
        # Create importer and run import
        importer = CTCAttributesImporter(db)
        importer.import_all_attributes('ctc_attributes.json')
        
        logger.info("CTC attributes import completed successfully!")
        
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main() 