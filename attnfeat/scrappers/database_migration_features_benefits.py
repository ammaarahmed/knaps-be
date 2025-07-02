# database_migration_features_benefits.py

from sqlalchemy import Column, Integer, Text, Boolean, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class FeaturesBenefitsBase(Base):
    """
    Base class for features and benefits tables
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    feature_name = Column(String, nullable=False)
    feature_description = Column(Text, nullable=True)
    benefit_name = Column(String, nullable=False)
    benefit_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Additional fields that might come from the API
    external_id = Column(String, nullable=True, index=True)  # ID from the external system
    external_code = Column(String, nullable=True, index=True)  # Code from the external system
    priority = Column(Integer, nullable=True)  # Priority/order of the feature/benefit
    category = Column(String, nullable=True)  # Category of the feature/benefit
    tags = Column(Text, nullable=True)  # JSON string of tags
    
    # Metadata
    scraped_at = Column(DateTime, nullable=True)  # When this was scraped from the API
    source_level = Column(String, nullable=False)  # 'class', 'type', or 'category'
    source_level_id = Column(Integer, nullable=False)  # ID from the source level


class ClassFeaturesBenefits(FeaturesBenefitsBase):
    """
    Features and benefits for ProductClass level
    """
    __tablename__ = "class_features_benefits"
    
    # Foreign key to product_class table
    product_class_id = Column(
        Integer,
        ForeignKey("product_class.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    product_class = relationship("ProductClass", back_populates="features_benefits")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_class_fb_external', 'external_id', 'source_level_id'),
        Index('idx_class_fb_active', 'is_active', 'product_class_id'),
    )


class TypeFeaturesBenefits(FeaturesBenefitsBase):
    """
    Features and benefits for ProductType level
    """
    __tablename__ = "type_features_benefits"
    
    # Foreign keys
    product_type_id = Column(
        Integer,
        ForeignKey("product_type.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_class_id = Column(
        Integer,
        ForeignKey("product_class.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    product_type = relationship("ProductType", back_populates="features_benefits")
    product_class = relationship("ProductClass", back_populates="type_features_benefits")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_type_fb_external', 'external_id', 'source_level_id'),
        Index('idx_type_fb_active', 'is_active', 'product_type_id'),
        Index('idx_type_fb_class', 'product_class_id', 'is_active'),
    )


class CategoryFeaturesBenefits(FeaturesBenefitsBase):
    """
    Features and benefits for ProductCategory level
    """
    __tablename__ = "category_features_benefits"
    
    # Foreign keys
    product_category_id = Column(
        Integer,
        ForeignKey("product_category.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_type_id = Column(
        Integer,
        ForeignKey("product_type.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_class_id = Column(
        Integer,
        ForeignKey("product_class.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    product_category = relationship("ProductCategory", back_populates="features_benefits")
    product_type = relationship("ProductType", back_populates="category_features_benefits")
    product_class = relationship("ProductClass", back_populates="category_features_benefits")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_category_fb_external', 'external_id', 'source_level_id'),
        Index('idx_category_fb_active', 'is_active', 'product_category_id'),
        Index('idx_category_fb_type', 'product_type_id', 'is_active'),
        Index('idx_category_fb_class', 'product_class_id', 'is_active'),
    )


# Update existing models to include relationships
def update_existing_models():
    """
    This function would be called to update the existing models with new relationships.
    In practice, you would need to modify the existing model files.
    """
    
    # Add to ProductClass model:
    # features_benefits = relationship("ClassFeaturesBenefits", back_populates="product_class", cascade="all, delete-orphan")
    # type_features_benefits = relationship("TypeFeaturesBenefits", back_populates="product_class", cascade="all, delete-orphan")
    # category_features_benefits = relationship("CategoryFeaturesBenefits", back_populates="product_class", cascade="all, delete-orphan")
    
    # Add to ProductType model:
    # features_benefits = relationship("TypeFeaturesBenefits", back_populates="product_type", cascade="all, delete-orphan")
    # category_features_benefits = relationship("CategoryFeaturesBenefits", back_populates="product_type", cascade="all, delete-orphan")
    
    # Add to ProductCategory model:
    # features_benefits = relationship("CategoryFeaturesBenefits", back_populates="product_category", cascade="all, delete-orphan")
    
    pass


# Data import functions
def import_features_benefits_from_csv(csv_file: str, level: str, db_session):
    """
    Import features and benefits from CSV file into the appropriate table
    """
    import csv
    import json
    from datetime import datetime
    
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
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Create the record
                record = table_class(
                    feature_name=row.get('feature_name', ''),
                    feature_description=row.get('feature_description'),
                    benefit_name=row.get('benefit_name', ''),
                    benefit_description=row.get('benefit_description'),
                    external_id=row.get('external_id'),
                    external_code=row.get('external_code'),
                    priority=row.get('priority'),
                    category=row.get('category'),
                    tags=row.get('tags'),
                    source_level=level,
                    source_level_id=int(row.get('level_id', 0)),
                    scraped_at=datetime.fromisoformat(row.get('scraped_at')) if row.get('scraped_at') else None,
                    is_active=True
                )
                
                # Set foreign keys based on level
                if level == "class":
                    record.product_class_id = int(row.get('level_id', 0))
                elif level == "type":
                    record.product_type_id = int(row.get('level_id', 0))
                    record.product_class_id = int(row.get('product_class_id', 0))
                elif level == "category":
                    record.product_category_id = int(row.get('level_id', 0))
                    record.product_type_id = int(row.get('product_type_id', 0))
                    record.product_class_id = int(row.get('product_class_id', 0))
                
                db_session.add(record)
                records_created += 1
                
            except Exception as e:
                print(f"Error importing row: {e}")
                records_skipped += 1
                continue
    
    db_session.commit()
    print(f"Import complete: {records_created} created, {records_skipped} skipped")


if __name__ == "__main__":
    print("Features and Benefits Database Migration")
    print("=" * 50)
    print("This script defines the database models for features and benefits.")
    print("To use:")
    print("1. Add these models to your db_models.py file")
    print("2. Update existing models with the new relationships")
    print("3. Run database migrations")
    print("4. Use import_features_benefits_from_csv() to import data") 