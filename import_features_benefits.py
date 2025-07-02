# import_features_benefits.py

import csv
import json
import sys
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

# Import your database models and session
from src.database import get_db
from src.db_models import (
    ClassFeaturesBenefits, 
    TypeFeaturesBenefits, 
    CategoryFeaturesBenefits,
    ProductClass,
    ProductType,
    ProductCategory
)

def map_api_data_to_model(data: Dict[str, Any], level: str, level_id: int) -> Dict[str, Any]:
    """
    Map API response data to our database model fields
    This function should be customized based on the actual API response structure
    """
    # This is a template - you'll need to adjust based on actual API response
    mapped_data = {
        'feature_name': data.get('feature_name', data.get('name', '')),
        'feature_description': data.get('feature_description', data.get('description', '')),
        'benefit_name': data.get('benefit_name', data.get('benefit', '')),
        'benefit_description': data.get('benefit_description', data.get('benefit_desc', '')),
        'external_id': data.get('id', data.get('external_id')),
        'external_code': data.get('code', data.get('external_code')),
        'priority': data.get('priority', data.get('order', None)),
        'category': data.get('category', data.get('type', None)),
        'tags': json.dumps(data.get('tags', [])) if data.get('tags') else None,
        'source_level': level,
        'source_level_id': level_id,
        'scraped_at': datetime.utcnow(),
        'is_active': True
    }
    
    return mapped_data

def import_from_csv(csv_file: str, level: str, db_session: Session):
    """
    Import features and benefits from CSV file
    """
    table_map = {
        "class": ClassFeaturesBenefits,
        "type": TypeFeaturesBenefits,
        "category": CategoryFeaturesBenefits
    }
    
    table_class = table_map.get(level)
    if not table_class:
        raise ValueError(f"Invalid level: {level}")
    
    records_created = 0
    records_skipped = 0
    records_updated = 0
    
    print(f"Importing {level} level features and benefits from {csv_file}")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, 1):
            try:
                level_id = int(row.get('level_id', 0))
                if level_id == 0:
                    print(f"Row {row_num}: Skipping - no level_id")
                    records_skipped += 1
                    continue
                
                # Check if record already exists (based on external_id and source_level_id)
                existing_record = db_session.query(table_class).filter(
                    table_class.external_id == row.get('external_id'),
                    table_class.source_level_id == level_id,
                    table_class.source_level == level
                ).first()
                
                if existing_record:
                    # Update existing record
                    mapped_data = map_api_data_to_model(row, level, level_id)
                    for key, value in mapped_data.items():
                        if hasattr(existing_record, key):
                            setattr(existing_record, key, value)
                    existing_record.updated_at = datetime.utcnow()
                    records_updated += 1
                else:
                    # Create new record
                    mapped_data = map_api_data_to_model(row, level, level_id)
                    
                    # Create the record
                    record = table_class(**mapped_data)
                    
                    # Set foreign keys based on level
                    if level == "class":
                        # Verify product_class exists
                        product_class = db_session.query(ProductClass).filter(
                            ProductClass.id == level_id
                        ).first()
                        if not product_class:
                            print(f"Row {row_num}: ProductClass with id {level_id} not found")
                            records_skipped += 1
                            continue
                        record.product_class_id = level_id
                        
                    elif level == "type":
                        # Verify product_type exists
                        product_type = db_session.query(ProductType).filter(
                            ProductType.id == level_id
                        ).first()
                        if not product_type:
                            print(f"Row {row_num}: ProductType with id {level_id} not found")
                            records_skipped += 1
                            continue
                        record.product_type_id = level_id
                        record.product_class_id = product_type.product_class_id
                        
                    elif level == "category":
                        # Verify product_category exists
                        product_category = db_session.query(ProductCategory).filter(
                            ProductCategory.id == level_id
                        ).first()
                        if not product_category:
                            print(f"Row {row_num}: ProductCategory with id {level_id} not found")
                            records_skipped += 1
                            continue
                        record.product_category_id = level_id
                        record.product_type_id = product_category.product_type_id
                        record.product_class_id = product_category.product_type.product_class_id
                    
                    db_session.add(record)
                    records_created += 1
                
                # Commit every 100 records to avoid memory issues
                if (records_created + records_updated) % 100 == 0:
                    db_session.commit()
                    print(f"Processed {records_created + records_updated} records...")
                
            except Exception as e:
                print(f"Row {row_num}: Error importing - {e}")
                records_skipped += 1
                continue
    
    # Final commit
    db_session.commit()
    
    print(f"Import complete:")
    print(f"  Created: {records_created}")
    print(f"  Updated: {records_updated}")
    print(f"  Skipped: {records_skipped}")
    print(f"  Total: {records_created + records_updated + records_skipped}")

def import_all_levels():
    """
    Import features and benefits for all three levels
    """
    csv_files = {
        "class": "features_benefits_class.csv",
        "type": "features_benefits_type.csv",
        "category": "features_benefits_category.csv"
    }
    
    db_session = next(get_db())
    
    try:
        for level, csv_file in csv_files.items():
            try:
                import_from_csv(csv_file, level, db_session)
                print(f"\n{'='*50}")
            except FileNotFoundError:
                print(f"CSV file {csv_file} not found. Skipping {level} level.")
            except Exception as e:
                print(f"Error importing {level} level: {e}")
                
    finally:
        db_session.close()

def validate_data_integrity():
    """
    Validate that imported data has proper foreign key relationships
    """
    db_session = next(get_db())
    
    try:
        print("Validating data integrity...")
        
        # Check class features benefits
        class_fb_count = db_session.query(ClassFeaturesBenefits).count()
        class_fb_with_valid_fk = db_session.query(ClassFeaturesBenefits).join(ProductClass).count()
        print(f"Class Features Benefits: {class_fb_count} total, {class_fb_with_valid_fk} with valid FK")
        
        # Check type features benefits
        type_fb_count = db_session.query(TypeFeaturesBenefits).count()
        type_fb_with_valid_fk = db_session.query(TypeFeaturesBenefits).join(ProductType).count()
        print(f"Type Features Benefits: {type_fb_count} total, {type_fb_with_valid_fk} with valid FK")
        
        # Check category features benefits
        category_fb_count = db_session.query(CategoryFeaturesBenefits).count()
        category_fb_with_valid_fk = db_session.query(CategoryFeaturesBenefits).join(ProductCategory).count()
        print(f"Category Features Benefits: {category_fb_count} total, {category_fb_with_valid_fk} with valid FK")
        
    finally:
        db_session.close()

if __name__ == "__main__":
    print("Features and Benefits Data Import")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "import":
            import_all_levels()
        elif command == "validate":
            validate_data_integrity()
        elif command == "import-level":
            if len(sys.argv) < 4:
                print("Usage: python import_features_benefits.py import-level <level> <csv_file>")
                sys.exit(1)
            level = sys.argv[2]
            csv_file = sys.argv[3]
            db_session = next(get_db())
            try:
                import_from_csv(csv_file, level, db_session)
            finally:
                db_session.close()
        else:
            print(f"Unknown command: {command}")
    else:
        print("Usage:")
        print("  python import_features_benefits.py import          # Import all levels")
        print("  python import_features_benefits.py validate        # Validate data integrity")
        print("  python import_features_benefits.py import-level <level> <csv_file>  # Import specific level") 