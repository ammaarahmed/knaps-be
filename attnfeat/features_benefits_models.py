from sqlalchemy import Column, Integer, Text, Boolean, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

# Add these imports to your existing imports in db_models.py
# from sqlalchemy import Index  # Add this if not already imported

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


# ============================================================================
# REQUIRED CHANGES TO EXISTING MODELS
# ============================================================================
# 
# Add these relationships to your existing models in src/db_models.py:
#
# In ProductClass model (around line 89), add:
#     features_benefits = relationship("ClassFeaturesBenefits", back_populates="product_class", cascade="all, delete-orphan")
#     type_features_benefits = relationship("TypeFeaturesBenefits", back_populates="product_class", cascade="all, delete-orphan")
#     category_features_benefits = relationship("CategoryFeaturesBenefits", back_populates="product_class", cascade="all, delete-orphan")
#
# In ProductType model (around line 120), add:
#     features_benefits = relationship("TypeFeaturesBenefits", back_populates="product_type", cascade="all, delete-orphan")
#     category_features_benefits = relationship("CategoryFeaturesBenefits", back_populates="product_type", cascade="all, delete-orphan")
#
# In ProductCategory model (around line 150), add:
#     features_benefits = relationship("CategoryFeaturesBenefits", back_populates="product_category", cascade="all, delete-orphan")
#
# ============================================================================ 