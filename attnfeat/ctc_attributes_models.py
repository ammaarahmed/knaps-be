# ctc_attributes_models.py
# Add these models to your existing src/db_models.py file

from sqlalchemy import Column, Integer, Text, Boolean, String, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

# Add these imports to your existing imports in db_models.py
# from sqlalchemy import JSON  # Add this if not already imported

class CategoryAttribute(Base):
    """
    Enhanced CategoryAttribute model for storing detailed attribute information
    This replaces or extends the existing CategoryAttribute model
    """
    __tablename__ = "category_attributes"

    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    category_id = Column(
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
    
    # Attribute identification
    attribute_id = Column(Integer, nullable=True, index=True)  # ID from external system
    attribute_code = Column(String, nullable=True, index=True)  # Code from external system
    attribute_name = Column(String, nullable=False)
    attribute_type = Column(String, nullable=True)  # e.g., 'text', 'number', 'boolean', 'select'
    
    # Attribute values and options
    attribute_value = Column(Text, nullable=True)  # Current/default value
    attribute_options = Column(JSON, nullable=True)  # JSON array of possible values
    attribute_unit = Column(String, nullable=True)  # Unit of measurement (e.g., 'kg', 'cm', 'W')
    
    # Attribute metadata
    attribute_description = Column(Text, nullable=True)
    attribute_help_text = Column(Text, nullable=True)
    attribute_placeholder = Column(String, nullable=True)
    
    # Display and validation
    is_required = Column(Boolean, default=False, nullable=False)
    is_visible = Column(Boolean, default=True, nullable=False)
    is_searchable = Column(Boolean, default=False, nullable=False)
    is_filterable = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, nullable=True)
    
    # Validation rules
    min_value = Column(String, nullable=True)  # Minimum value (as string to handle different types)
    max_value = Column(String, nullable=True)  # Maximum value
    pattern = Column(String, nullable=True)  # Regex pattern for validation
    
    # Status and tracking
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Metadata
    scraped_at = Column(DateTime, nullable=True)  # When this was scraped from the API
    external_data = Column(JSON, nullable=True)  # Store any additional external data as JSON
    
    # Relationships
    category = relationship("ProductCategory", back_populates="detailed_attributes")
    product_type = relationship("ProductType", back_populates="category_attributes")
    product_class = relationship("ProductClass", back_populates="category_attributes")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_category_attr_external', 'attribute_id', 'attribute_code'),
        Index('idx_category_attr_active', 'is_active', 'category_id'),
        Index('idx_category_attr_searchable', 'is_searchable', 'is_active'),
        Index('idx_category_attr_filterable', 'is_filterable', 'is_active'),
        Index('idx_category_attr_type', 'product_type_id', 'is_active'),
        Index('idx_category_attr_class', 'product_class_id', 'is_active'),
    )


class AttributeValue(Base):
    """
    Store specific attribute values for products or categories
    This allows for multiple values per attribute if needed
    """
    __tablename__ = "attribute_values"

    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    category_attribute_id = Column(
        Integer,
        ForeignKey("category_attributes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,  # Can be null if it's a category-level attribute
        index=True
    )
    
    # Value data
    value = Column(Text, nullable=False)
    value_numeric = Column(String, nullable=True)  # Numeric representation if applicable
    value_boolean = Column(Boolean, nullable=True)  # Boolean representation if applicable
    
    # Value metadata
    value_label = Column(String, nullable=True)  # Human-readable label
    value_description = Column(Text, nullable=True)
    value_unit = Column(String, nullable=True)
    
    # Status and tracking
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    category_attribute = relationship("CategoryAttribute", back_populates="values")
    product = relationship("ProductModel", back_populates="attribute_values")
    
    # Indexes
    __table_args__ = (
        Index('idx_attr_value_product', 'product_id', 'is_active'),
        Index('idx_attr_value_category_attr', 'category_attribute_id', 'is_active'),
    )


class AttributeGroup(Base):
    """
    Group attributes together for better organization
    """
    __tablename__ = "attribute_groups"

    id = Column(Integer, primary_key=True)
    
    # Group identification
    group_name = Column(String, nullable=False)
    group_code = Column(String, nullable=True, unique=True)
    group_description = Column(Text, nullable=True)
    
    # Group metadata
    display_order = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    attributes = relationship("CategoryAttribute", back_populates="group")
    
    # Indexes
    __table_args__ = (
        Index('idx_attr_group_active', 'is_active'),
        Index('idx_attr_group_code', 'group_code'),
    )


# ============================================================================
# REQUIRED CHANGES TO EXISTING MODELS
# ============================================================================
# 
# Add these relationships to your existing models in src/db_models.py:
#
# In ProductCategory model, add:
#     detailed_attributes = relationship("CategoryAttribute", back_populates="category", cascade="all, delete-orphan")
#     attribute_values = relationship("AttributeValue", back_populates="category")
#
# In ProductType model, add:
#     category_attributes = relationship("CategoryAttribute", back_populates="product_type", cascade="all, delete-orphan")
#
# In ProductClass model, add:
#     category_attributes = relationship("CategoryAttribute", back_populates="product_class", cascade="all, delete-orphan")
#
# In ProductModel, add:
#     attribute_values = relationship("AttributeValue", back_populates="product", cascade="all, delete-orphan")
#
# In CategoryAttribute model, add:
#     values = relationship("AttributeValue", back_populates="category_attribute", cascade="all, delete-orphan")
#     group = relationship("AttributeGroup", back_populates="attributes")
#
# ============================================================================ 