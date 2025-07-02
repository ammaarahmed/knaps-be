#!/usr/bin/env python3
"""
Script to import CTC categories from JSON into the normalized database structure.
This script reads the ctc_categories.json file and imports the hierarchical data
into the new CTCCategory table structure with UUID support.
"""

import json
import sys
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the src directory to the path so we can import our models
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import get_database_url
from src.db_models import CTCCategory, Base

def parse_datetime(dt_string):
    """Parse datetime string from the JSON format."""
    if not dt_string:
        return None
    # Remove timezone info for simplicity
    dt_string = dt_string.split('+')[0]
    return datetime.fromisoformat(dt_string)

def import_ctc_categories(json_file_path):
    """Import CTC categories from JSON file into the database."""
    
    # Create database engine and session
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Read the JSON file
        print(f"Reading CTC categories from {json_file_path}...")
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        print(f"Found {len(data)} product classes to import...")
        
        # Track imported records for reporting
        imported_classes = 0
        imported_types = 0
        imported_categories = 0
        
        # Track new IDs for parent references
        class_new_ids = {}  # former_id -> new_id
        type_new_ids = {}   # former_id -> new_id
        
        # Import each product class (level 1)
        for class_data in data:
            class_uuid = str(uuid.uuid4())
            # Create the product class (level 1)
            class_record = CTCCategory(
                former_id=class_data['id'],
                uuid=class_uuid,
                active=class_data['active'],
                modified_by=class_data['modified_by'],
                modified=parse_datetime(class_data['modified']),
                created_by=class_data['created_by'],
                created=parse_datetime(class_data['created']),
                deleted_by=class_data['deleted_by'],
                deleted=parse_datetime(class_data['deleted']),
                code=class_data['code'],
                name=class_data['name'],
                store=class_data['store'],
                level=1,
                parent_id=None,
                parent_uuid=None,
                product_id=None
            )
            
            session.add(class_record)
            session.flush()  # Get the auto-generated ID
            class_new_ids[class_data['id']] = class_record.id
            imported_classes += 1
            
            # Import product types (level 2) for this class
            for type_data in class_data.get('all_product_types', []):
                type_uuid = str(uuid.uuid4())
                type_record = CTCCategory(
                    former_id=type_data['id'],
                    uuid=type_uuid,
                    active=type_data['active'],
                    modified_by=type_data['modified_by'],
                    modified=parse_datetime(type_data['modified']),
                    created_by=type_data['created_by'],
                    created=parse_datetime(type_data['created']),
                    deleted_by=type_data['deleted_by'],
                    deleted=parse_datetime(type_data['deleted']),
                    code=type_data['code'],
                    name=type_data['name'],
                    store=type_data['store'],
                    level=2,
                    parent_id=class_new_ids[class_data['id']],
                    parent_uuid=class_uuid,
                    product_id=None
                )
                
                session.add(type_record)
                session.flush()  # Get the auto-generated ID
                type_new_ids[type_data['id']] = type_record.id
                imported_types += 1
                
                # Import product categories (level 3) for this type
                for category_data in type_data.get('all_product_categories', []):
                    category_record = CTCCategory(
                        former_id=category_data['id'],
                        uuid=str(uuid.uuid4()),
                        active=category_data['active'],
                        modified_by=category_data['modified_by'],
                        modified=parse_datetime(category_data['modified']),
                        created_by=category_data['created_by'],
                        created=parse_datetime(category_data['created']),
                        deleted_by=category_data['deleted_by'],
                        deleted=parse_datetime(category_data['deleted']),
                        code=category_data['code'],
                        name=category_data['name'],
                        store=category_data['store'],
                        level=3,
                        parent_id=type_new_ids[type_data['id']],
                        parent_uuid=type_uuid,
                        product_id=None
                    )
                    
                    session.add(category_record)
                    imported_categories += 1
        
        # Commit all changes
        print("Committing changes to database...")
        session.commit()
        
        print(f"Import completed successfully!")
        print(f"  - Product Classes (Level 1): {imported_classes}")
        print(f"  - Product Types (Level 2): {imported_types}")
        print(f"  - Product Categories (Level 3): {imported_categories}")
        print(f"  - Total records: {imported_classes + imported_types + imported_categories}")
        
    except Exception as e:
        print(f"Error during import: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def verify_import():
    """Verify the imported data by checking the hierarchy."""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Count records by level
        level_counts = {}
        for level in [1, 2, 3]:
            count = session.query(CTCCategory).filter(CTCCategory.level == level).count()
            level_counts[level] = count
        
        print("\nVerification Results:")
        print(f"  - Level 1 (Classes): {level_counts.get(1, 0)}")
        print(f"  - Level 2 (Types): {level_counts.get(2, 0)}")
        print(f"  - Level 3 (Categories): {level_counts.get(3, 0)}")
        
        # Check UUID generation
        uuid_count = session.query(CTCCategory).filter(CTCCategory.uuid.isnot(None)).count()
        total_count = sum(level_counts.values())
        print(f"  - Records with UUIDs: {uuid_count}/{total_count}")
        
        # Check some sample hierarchies
        print("\nSample Hierarchies:")
        classes = session.query(CTCCategory).filter(CTCCategory.level == 1).limit(3).all()
        
        for class_record in classes:
            print(f"\n  Class: {class_record.name} (ID: {class_record.id}, UUID: {class_record.uuid})")
            types = session.query(CTCCategory).filter(
                CTCCategory.level == 2,
                CTCCategory.parent_id == class_record.id
            ).limit(2).all()
            
            for type_record in types:
                print(f"    Type: {type_record.name} (ID: {type_record.id}, UUID: {type_record.uuid})")
                categories = session.query(CTCCategory).filter(
                    CTCCategory.level == 3,
                    CTCCategory.parent_id == type_record.id
                ).limit(2).all()
                
                for category_record in categories:
                    print(f"      Category: {category_record.name} (ID: {category_record.id}, UUID: {category_record.uuid})")
        
    finally:
        session.close()

if __name__ == "__main__":
    json_file = "ctc_categories.json"
    
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found!")
        sys.exit(1)
    
    print("Starting CTC Categories Import...")
    import_ctc_categories(json_file)
    verify_import()
    print("\nImport process completed!") 