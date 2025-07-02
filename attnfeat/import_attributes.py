# import_attributes.py

import csv
import json
import sys
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

# Import your database models and session
from src.database import get_db
from src.db_models import (
    CategoryAttribute,
    AttributeValue,
    AttributeGroup,
    ProductCategory,
    ProductType,
    ProductClass
)

def map_api_data_to_model(data: Dict[str, Any], category_id: int) -> Dict[str, Any]:
    """
    Map API response data to our database model fields
    This function should be customized based on the actual API response structure
    """
    # This is a template - you'll need to adjust based on actual API response
    mapped_data = {
        'attribute_id': data.get('id'),
        'attribute_code': data.get('code', data.get('attribute_code')),
        'attribute_name': data.get('name', data.get('attribute_name', '')),
        'attribute_type': data.get('type', data.get('attribute_type')),
        'attribute_value': data.get('value', data.get('default_value')),
        'attribute_options': data.get('options', data.get('choices')),
        'attribute_unit': data.get('unit', data.get('measurement_unit')),
        'attribute_description': data.get('description', data.get('help_text')),
        'attribute_help_text': data.get('help_text', data.get('description')),
        'attribute_placeholder': data.get('placeholder'),
        'is_required': data.get('required', False),
        'is_visible': data.get('visible', True),
        'is_searchable': data.get('searchable', False),
        'is_filterable': data.get('filterable', False),
        'display_order': data.get('order', data.get('rank', data.get('display_order'))),
        'min_value': data.get('min_value'),
        'max_value': data.get('max_value'),
        'pattern': data.get('pattern', data.get('validation_pattern')),
        'is_active': True,
        'scraped_at': datetime.utcnow(),
        'external_data': data  # Store the original data as JSON
    }
    
    return mapped_data

def import_from_csv(csv_file: str, db_session: Session):
    """
    Import attributes from CSV file
    """
    records_created = 0
    records_skipped = 0
    records_updated = 0
    
    print(f"Importing attributes from {csv_file}")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, 1):
            try:
                category_id = int(row.get('category_id', 0))
                if category_id == 0:
                    print(f"Row {row_num}: Skipping - no category_id")
                    records_skipped += 1
                    continue
                
                # Check if record already exists (based on attribute_id and category_id)
                existing_record = db_session.query(CategoryAttribute).filter(
                    CategoryAttribute.attribute_id == row.get('id'),
                    CategoryAttribute.category_id == category_id
                ).first()
                
                if existing_record:
                    # Update existing record
                    mapped_data = map_api_data_to_model(row, category_id)
                    for key, value in mapped_data.items():
                        if hasattr(existing_record, key):
                            setattr(existing_record, key, value)
                    existing_record.updated_at = datetime.utcnow()
                    records_updated += 1
                else:
                    # Create new record
                    mapped_data = map_api_data_to_model(row, category_id)
                    
                    # Create the record
                    record = CategoryAttribute(**mapped_data)
                    
                    # Set foreign keys
                    record.category_id = category_id
                    
                    # Get product_type_id and product_class_id from the category
                    product_category = db_session.query(ProductCategory).filter(
                        ProductCategory.id == category_id
                    ).first()
                    
                    if product_category:
                        record.product_type_id = product_category.product_type_id
                        record.product_class_id = product_category.product_type.product_class_id
                    else:
                        print(f"Row {row_num}: ProductCategory with id {category_id} not found")
                        records_skipped += 1
                        continue
                    
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

def import_from_json(json_file: str, db_session: Session):
    """
    Import attributes from JSON file
    """
    records_created = 0
    records_skipped = 0
    records_updated = 0
    
    print(f"Importing attributes from {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for record_num, category_data in enumerate(data, 1):
        try:
            category_id = category_data.get('category_id')
            if not category_id:
                print(f"Record {record_num}: Skipping - no category_id")
                records_skipped += 1
                continue
            
            # Extract attributes from the response
            attributes = category_data.get('attributes', [])
            if not attributes:
                print(f"Record {record_num}: No attributes found for category {category_id}")
                continue
            
            for attr in attributes:
                try:
                    # Check if record already exists
                    existing_record = db_session.query(CategoryAttribute).filter(
                        CategoryAttribute.attribute_id == attr.get('id'),
                        CategoryAttribute.category_id == category_id
                    ).first()
                    
                    if existing_record:
                        # Update existing record
                        mapped_data = map_api_data_to_model(attr, category_id)
                        for key, value in mapped_data.items():
                            if hasattr(existing_record, key):
                                setattr(existing_record, key, value)
                        existing_record.updated_at = datetime.utcnow()
                        records_updated += 1
                    else:
                        # Create new record
                        mapped_data = map_api_data_to_model(attr, category_id)
                        
                        # Create the record
                        record = CategoryAttribute(**mapped_data)
                        
                        # Set foreign keys
                        record.category_id = category_id
                        
                        # Get product_type_id and product_class_id from the category
                        product_category = db_session.query(ProductCategory).filter(
                            ProductCategory.id == category_id
                        ).first()
                        
                        if product_category:
                            record.product_type_id = product_category.product_type_id
                            record.product_class_id = product_category.product_type.product_class_id
                        else:
                            print(f"Record {record_num}: ProductCategory with id {category_id} not found")
                            records_skipped += 1
                            continue
                        
                        db_session.add(record)
                        records_created += 1
                    
                except Exception as e:
                    print(f"Record {record_num}, Attribute: Error importing - {e}")
                    records_skipped += 1
                    continue
            
            # Commit every 50 categories to avoid memory issues
            if record_num % 50 == 0:
                db_session.commit()
                print(f"Processed {record_num} categories...")
                
        except Exception as e:
            print(f"Record {record_num}: Error processing category - {e}")
            records_skipped += 1
            continue
    
    # Final commit
    db_session.commit()
    
    print(f"Import complete:")
    print(f"  Created: {records_created}")
    print(f"  Updated: {records_updated}")
    print(f"  Skipped: {records_skipped}")
    print(f"  Total: {records_created + records_updated + records_skipped}")

def validate_data_integrity():
    """
    Validate that imported data has proper foreign key relationships
    """
    db_session = next(get_db())
    
    try:
        print("Validating attributes data integrity...")
        
        # Check category attributes
        attr_count = db_session.query(CategoryAttribute).count()
        attr_with_valid_fk = db_session.query(CategoryAttribute).join(ProductCategory).count()
        print(f"Category Attributes: {attr_count} total, {attr_with_valid_fk} with valid FK")
        
        # Check attribute values
        value_count = db_session.query(AttributeValue).count()
        print(f"Attribute Values: {value_count} total")
        
        # Check attribute groups
        group_count = db_session.query(AttributeGroup).count()
        print(f"Attribute Groups: {group_count} total")
        
    finally:
        db_session.close()

if __name__ == "__main__":
    print("CTC Attributes Data Import")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "import-csv":
            if len(sys.argv) < 3:
                print("Usage: python import_attributes.py import-csv <csv_file>")
                sys.exit(1)
            csv_file = sys.argv[2]
            db_session = next(get_db())
            try:
                import_from_csv(csv_file, db_session)
            finally:
                db_session.close()
                
        elif command == "import-json":
            if len(sys.argv) < 3:
                print("Usage: python import_attributes.py import-json <json_file>")
                sys.exit(1)
            json_file = sys.argv[2]
            db_session = next(get_db())
            try:
                import_from_json(json_file, db_session)
            finally:
                db_session.close()
                
        elif command == "validate":
            validate_data_integrity()
        else:
            print(f"Unknown command: {command}")
    else:
        print("Usage:")
        print("  python import_attributes.py import-csv <csv_file>  # Import from CSV")
        print("  python import_attributes.py import-json <json_file>  # Import from JSON")
        print("  python import_attributes.py validate        # Validate data integrity") 