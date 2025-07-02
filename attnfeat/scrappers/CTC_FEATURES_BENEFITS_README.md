# CTC Features and Benefits Implementation

This document outlines the implementation of features and benefits scraping and storage for the CTC (Class-Type-Category) hierarchy.

## Overview

The CTC system consists of three hierarchical levels:
- **Class** - Top level product classification
- **Type** - Middle level product classification  
- **Category** - Bottom level product classification

Each level can have associated features and benefits that need to be scraped from the API and stored in the database.

## Files Created

1. **`ctc_features_benefits_scraper.py`** - Comprehensive scraper for all three levels
2. **`features_benefits_models.py`** - Database models for features and benefits
3. **`import_features_benefits.py`** - Data import script
4. **`test_api.py`** - API testing script
5. **`database_migration_features_benefits.py`** - Migration helper

## Database Schema Changes

### New Tables

Three new tables will be created:

1. **`class_features_benefits`** - Features and benefits for ProductClass
2. **`type_features_benefits`** - Features and benefits for ProductType  
3. **`category_features_benefits`** - Features and benefits for ProductCategory

### Schema Structure

Each table includes:
- `id` - Primary key
- `feature_name` - Name of the feature
- `feature_description` - Description of the feature
- `benefit_name` - Name of the benefit
- `benefit_description` - Description of the benefit
- `external_id` - ID from the external API
- `external_code` - Code from the external API
- `priority` - Priority/order of the feature/benefit
- `category` - Category classification
- `tags` - JSON string of tags
- `source_level` - 'class', 'type', or 'category'
- `source_level_id` - ID from the source level
- `scraped_at` - When this was scraped
- `is_active` - Whether the record is active
- `created_at` / `updated_at` - Timestamps
- Foreign keys to the respective CTC tables

## Implementation Steps

### Step 1: Update Database Models

1. Add the new models to `src/db_models.py`:

```python
# Add these imports at the top
from sqlalchemy import Index

# Add the new models (copy from features_benefits_models.py)
class FeaturesBenefitsBase(Base):
    # ... (copy the entire class)

class ClassFeaturesBenefits(FeaturesBenefitsBase):
    # ... (copy the entire class)

class TypeFeaturesBenefits(FeaturesBenefitsBase):
    # ... (copy the entire class)

class CategoryFeaturesBenefits(FeaturesBenefitsBase):
    # ... (copy the entire class)
```

2. Update existing models with new relationships:

```python
# In ProductClass model, add:
features_benefits = relationship("ClassFeaturesBenefits", back_populates="product_class", cascade="all, delete-orphan")
type_features_benefits = relationship("TypeFeaturesBenefits", back_populates="product_class", cascade="all, delete-orphan")
category_features_benefits = relationship("CategoryFeaturesBenefits", back_populates="product_class", cascade="all, delete-orphan")

# In ProductType model, add:
features_benefits = relationship("TypeFeaturesBenefits", back_populates="product_type", cascade="all, delete-orphan")
category_features_benefits = relationship("CategoryFeaturesBenefits", back_populates="product_type", cascade="all, delete-orphan")

# In ProductCategory model, add:
features_benefits = relationship("CategoryFeaturesBenefits", back_populates="product_category", cascade="all, delete-orphan")
```

### Step 2: Run Database Migrations

1. Generate a new migration:
```bash
alembic revision --autogenerate -m "Add features and benefits tables"
```

2. Apply the migration:
```bash
alembic upgrade head
```

### Step 3: Configure the Scraper

1. Update the session ID in `ctc_features_benefits_scraper.py`:
```python
SESSION_ID = "your_actual_session_id_here"
```

2. Test the API connection:
```bash
python test_api.py
```

### Step 4: Run the Scraper

1. Run the scraper to fetch all data:
```bash
python ctc_features_benefits_scraper.py
```

This will create:
- `features_benefits_class.csv` / `.json`
- `features_benefits_type.csv` / `.json`
- `features_benefits_category.csv` / `.json`

### Step 5: Import Data

1. Import all levels:
```bash
python import_features_benefits.py import
```

2. Or import specific levels:
```bash
python import_features_benefits.py import-level class features_benefits_class.csv
python import_features_benefits.py import-level type features_benefits_type.csv
python import_features_benefits.py import-level category features_benefits_category.csv
```

3. Validate data integrity:
```bash
python import_features_benefits.py validate
```

## API Endpoint

The scraper uses the following API endpoint:
```
GET https://staging.bi-rite.knaps.io/ctc/features-benefits/
```

Parameters:
- `id` - The ID of the class/type/category
- `level` - The level ('class', 'type', or 'category')

Headers:
- `Session-ID` - Authentication session ID
- `Accept: application/json`

## Data Flow

1. **Scraping**: The scraper iterates through IDs for each level and fetches features/benefits
2. **Storage**: Data is saved to CSV/JSON files for inspection
3. **Import**: Data is imported into the database with proper foreign key relationships
4. **Validation**: Data integrity is verified

## Querying Features and Benefits

Once imported, you can query features and benefits like this:

```python
# Get features and benefits for a specific product class
class_fb = db_session.query(ClassFeaturesBenefits).filter(
    ClassFeaturesBenefits.product_class_id == class_id,
    ClassFeaturesBenefits.is_active == True
).all()

# Get features and benefits for a specific product type
type_fb = db_session.query(TypeFeaturesBenefits).filter(
    TypeFeaturesBenefits.product_type_id == type_id,
    TypeFeaturesBenefits.is_active == True
).all()

# Get features and benefits for a specific product category
category_fb = db_session.query(CategoryFeaturesBenefits).filter(
    CategoryFeaturesBenefits.product_category_id == category_id,
    CategoryFeaturesBenefits.is_active == True
).all()

# Get all features and benefits for a product (across all levels)
product_class = db_session.query(ProductClass).filter(ProductClass.id == class_id).first()
all_fb = []
all_fb.extend(product_class.features_benefits)
all_fb.extend(product_class.type_features_benefits)
all_fb.extend(product_class.category_features_benefits)
```

## Maintenance

### Updating Data

To update features and benefits:

1. Run the scraper again to get fresh data
2. Run the import script - it will update existing records and create new ones
3. Validate the data integrity

### Monitoring

- Check the `scraped_at` field to see when data was last updated
- Use the `is_active` field to soft-delete features/benefits
- Monitor the validation script output for data integrity issues

## Troubleshooting

### Session Expired
If you get a 419 error, update the `SESSION_ID` in the scraper and try again.

### Missing Foreign Keys
If import fails due to missing foreign keys, ensure that:
1. ProductClass records exist before importing class features
2. ProductType records exist before importing type features  
3. ProductCategory records exist before importing category features

### Data Mapping Issues
If the API response structure differs from expected, update the `map_api_data_to_model()` function in `import_features_benefits.py`.

## Future Enhancements

1. **Scheduled Updates**: Set up automated scraping and import
2. **API Integration**: Direct API integration instead of scraping
3. **Caching**: Implement caching for frequently accessed features/benefits
4. **Search**: Add full-text search capabilities
5. **Analytics**: Track feature/benefit usage and effectiveness 