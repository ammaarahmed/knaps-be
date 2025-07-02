# CTC Attributes Import System

This system handles the import of CTC (Category, Type, Class) attributes data from JSON into the database. The system creates a normalized structure to store attribute metadata including groups, data types, units of measure, and individual attributes.

## Database Schema

The system creates the following tables:

### 1. `ctc_attribute_groups`
Stores attribute groups (e.g., "Key Specifications", "Ungrouped")
- `id`: Primary key
- `uuid`: Unique identifier
- `active`: Whether the group is active
- `modified_by`, `created_by`: Audit fields
- `modified`, `created`, `deleted`: Timestamps
- `code`: Group code
- `name`: Group name
- `store`: Store identifier

### 2. `ctc_data_types`
Stores data types (e.g., "Text", "Number", "Boolean")
- Similar structure to attribute groups
- `code`: Data type code (e.g., "txt", "num")
- `name`: Data type name

### 3. `ctc_units_of_measure`
Stores units of measure (e.g., "Litres", "Kilograms", "Meters")
- Similar structure to attribute groups
- `code`: UOM code (e.g., "l", "kg", "m")
- `name`: UOM name

### 4. `ctc_attributes`
Stores individual CTC attributes with their metadata
- `id`: Primary key (uses original ID from JSON)
- `uuid`: Unique identifier
- `name`: Attribute name
- `rank`: Display order
- `as_filter`: Whether attribute can be used as a filter
- `scraped_at`: When the data was scraped
- Foreign keys to categories, groups, data types, and UOMs

## Scripts

### 1. Database Migration (`database_migration_ctc_attributes.py`)
Creates the necessary database tables and indexes.

```bash
python database_migration_ctc_attributes.py
```

This script:
- Creates all CTC attributes tables
- Verifies table structure
- Creates performance indexes
- Checks foreign key constraints

### 2. Data Import (`import_ctc_attributes.py`)
Imports CTC attributes data from the JSON file into the database.

```bash
python import_ctc_attributes.py
```

This script:
- Loads data from `ctc_attributes.json`
- Creates or finds existing attribute groups, data types, and UOMs
- Imports individual attributes with proper relationships
- Handles duplicate detection
- Provides detailed logging

### 3. Test and Verification (`test_ctc_attributes_import.py`)
Verifies the import and demonstrates how to query the data.

```bash
python test_ctc_attributes_import.py
```

This script:
- Counts records in each table
- Shows sample data
- Tests relationships between tables
- Demonstrates common queries

## Usage Workflow

1. **Run the migration** to create tables:
   ```bash
   python database_migration_ctc_attributes.py
   ```

2. **Import the data**:
   ```bash
   python import_ctc_attributes.py
   ```

3. **Verify the import**:
   ```bash
   python test_ctc_attributes_import.py
   ```

## Data Structure

The JSON file contains an array of category entries, each with:
```json
{
  "category_id": 165,
  "scraped_at": "2025-07-01T22:56:49.271367",
  "attributes": [
    {
      "id": 5302,
      "active": true,
      "modified_by": "fatima_qhof",
      "modified": "2024-01-22T15:48:28.537325+11:00",
      "created_by": "omar",
      "created": "2023-04-11T10:19:56.426809+10:00",
      "deleted_by": null,
      "deleted": null,
      "name": "Finish Colour",
      "store": "QHOF",
      "rank": 3,
      "attribute_group": { /* group data */ },
      "uom": null,
      "data_type": { /* data type data */ },
      "as_filter": false
    }
  ]
}
```

## Query Examples

### Get all attributes for a category
```python
from src.database import get_db
from src.db_models import CTCAttribute

db = next(get_db())
attributes = db.query(CTCAttribute).filter(
    CTCAttribute.category_id == 165
).all()
```

### Get attributes with relationships
```python
from sqlalchemy.orm import joinedload

attributes = db.query(CTCAttribute).options(
    joinedload(CTCAttribute.attribute_group),
    joinedload(CTCAttribute.data_type),
    joinedload(CTCAttribute.uom)
).filter(CTCAttribute.category_id == 165).all()
```

### Find text attributes
```python
text_attrs = db.query(CTCAttribute).join(CTCDataType).filter(
    CTCDataType.name == "Text"
).all()
```

### Find filterable attributes
```python
filter_attrs = db.query(CTCAttribute).filter(
    CTCAttribute.as_filter == True
).all()
```

## Features

- **Normalized Structure**: Separates concerns into different tables
- **Relationship Management**: Proper foreign key relationships
- **Audit Trail**: Tracks creation, modification, and deletion
- **Performance**: Includes indexes for common queries
- **Error Handling**: Robust error handling and logging
- **Duplicate Detection**: Prevents duplicate imports
- **Batch Processing**: Commits in batches for large datasets

## Notes

- The system preserves original IDs from the JSON data
- All timestamps are converted to UTC
- The import is idempotent - running it multiple times won't create duplicates
- Categories must exist in the `ctc_categories` table before importing attributes
- The system handles missing or null values gracefully 