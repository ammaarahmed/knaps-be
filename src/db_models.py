from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (Column, Integer, Text, Boolean, String, Numeric, DateTime, Date, ForeignKey, Enum, Index, PrimaryKeyConstraint)
from sqlalchemy.orm import relationship
import uuid

from .database import Base

### PRODUCT MODELS ###

class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String, nullable=False, unique=True)
    distributor_name = Column(Text, nullable=False)
    brand_name = Column(Text, nullable=False)
    product_code = Column(Text, nullable=False, unique=True)
    product_secondary_code = Column(Text)
    product_name = Column(Text, nullable=False)
    description = Column(Text)
    summary = Column(Text)
    shipping_class = Column(Text)
    category_name = Column(Text, nullable=False)
    product_availability = Column(Text, nullable=False, default="In Stock")
    status = Column(Text, nullable=False, default="Active")
    online = Column(Boolean, nullable=False, default=True)
    superceded_by = Column(Text)
    ean = Column(Text)
    pack_size = Column(Integer, nullable=False, default=1)
    core_group = Column(Text)
    tax_exmt = Column(Boolean, nullable=False, default=False)
    hyperlink = Column(Text)
    web_title = Column(Text)
    features_and_benefits_codes = Column(Text)
    badges_codes = Column(Text)
    stock_unmanaged = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    price_levels = relationship("PriceLevel", back_populates="product", cascade="all, delete-orphan")
    
    # CTC relationships
    ctc_categories = relationship("CTCCategory", back_populates="product")
    
    # Rebate relationships
    rebate_agreements = relationship("RebateAgreementProduct", back_populates="product")
    rebate_claims = relationship("RebateClaim", back_populates="product")


class PriceLevel(Base):
    __tablename__ = "price_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price_level = Column(String, nullable=False)  # e.g., "MWP", "Trade", "GO", "RRP"
    type = Column(String, nullable=False)  # e.g., "Standard", "Promotional", "Bulk", etc.
    value_excl = Column(Numeric(10, 2), nullable=False)  # Value excluding tax
    value_incl = Column(Numeric(10, 2), nullable=True)   # Value including tax
    comments = Column(Text, nullable=True)  # Additional comments about this price level
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("ProductModel", back_populates="price_levels")

    # Ensure unique combination of product, price level, and type
    __table_args__ = (
        # Add a unique constraint to prevent duplicate price levels for the same product
        # You might want to adjust this based on your business logic
    )


### USER MODELS ###

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    keycloak_id   = Column(String, unique=True, index=True)
    email         = Column(String, unique=True, index=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


### CTC MODELS ###

class CTCClass(Base):
    """
    Stores CTC product classes (level 1)
    """
    __tablename__ = "ctc_classes"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Relationships
    types = relationship("CTCType", back_populates="class_", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_classes_uuid', 'uuid'),
        Index('idx_ctc_classes_code', 'code'),
        Index('idx_ctc_classes_store', 'store'),
    )


class CTCType(Base):
    """
    Stores CTC product types (level 2)
    """
    __tablename__ = "ctc_types"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Foreign key to class
    class_id = Column(
        Integer,
        ForeignKey("ctc_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    class_ = relationship("CTCClass", back_populates="types")
    categories = relationship("CTCCategory", back_populates="type_", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_types_uuid', 'uuid'),
        Index('idx_ctc_types_code', 'code'),
        Index('idx_ctc_types_store', 'store'),
        Index('idx_ctc_types_class_id', 'class_id'),
    )


class CTCCategory(Base):
    """
    Stores CTC product categories (level 3)
    """
    __tablename__ = "ctc_categories"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Foreign key to type
    type_id = Column(
        Integer,
        ForeignKey("ctc_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Product association (only for categories at level 3)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True
    )

    # Relationships
    type_ = relationship("CTCType", back_populates="categories")
    product = relationship("ProductModel", back_populates="ctc_categories")

    # Attributes for categories (level 3)
    attributes = relationship(
        "CategoryAttribute",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    # CTC attributes for categories (level 3)
    ctc_attributes = relationship(
        "CTCAttribute",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_ctc_categories_uuid', 'uuid'),
        Index('idx_ctc_categories_code', 'code'),
        Index('idx_ctc_categories_store', 'store'),
        Index('idx_ctc_categories_type_id', 'type_id'),
        Index('idx_ctc_categories_product_id', 'product_id'),
    )


class CategoryAttribute(Base):
    __tablename__ = "category_attribute"

    id = Column(Integer, primary_key=True)
    category_id = Column(
        Integer,
        ForeignKey("ctc_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String, nullable=False)
    value = Column(Text, nullable=False)

    category = relationship("CTCCategory", back_populates="attributes")


### CTC ATTRIBUTE MODELS ###

class CTCAttributeGroup(Base):
    """
    Stores attribute groups (e.g., "Key Specifications", "Ungrouped")
    """
    __tablename__ = "ctc_attribute_groups"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Relationships
    attributes = relationship("CTCAttribute", back_populates="attribute_group")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_attribute_groups_uuid', 'uuid'),
        Index('idx_ctc_attribute_groups_store', 'store'),
    )


class CTCDataType(Base):
    """
    Stores data types (e.g., "Text", "Number", "Boolean")
    """
    __tablename__ = "ctc_data_types"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Relationships
    attributes = relationship("CTCAttribute", back_populates="data_type")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_data_types_uuid', 'uuid'),
        Index('idx_ctc_data_types_store', 'store'),
    )


class CTCUnitOfMeasure(Base):
    """
    Stores units of measure (e.g., "Litres", "Kilograms", "Meters")
    """
    __tablename__ = "ctc_units_of_measure"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)

    # Relationships
    attributes = relationship("CTCAttribute", back_populates="uom")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_units_of_measure_uuid', 'uuid'),
        Index('idx_ctc_units_of_measure_store', 'store'),
    )


class CTCAttribute(Base):
    """
    Stores individual CTC attributes with their metadata
    """
    __tablename__ = "ctc_attributes"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    rank = Column(Integer, nullable=False, default=0)
    as_filter = Column(Boolean, nullable=False, default=False)
    scraped_at = Column(DateTime, nullable=True)

    # Foreign keys
    category_id = Column(
        Integer,
        ForeignKey("ctc_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    attribute_group_id = Column(
        Integer,
        ForeignKey("ctc_attribute_groups.id", ondelete="CASCADE"),
        nullable=False
    )
    data_type_id = Column(
        Integer,
        ForeignKey("ctc_data_types.id", ondelete="CASCADE"),
        nullable=False
    )
    uom_id = Column(
        Integer,
        ForeignKey("ctc_units_of_measure.id", ondelete="CASCADE"),
        nullable=True
    )

    # Relationships
    category = relationship("CTCCategory", back_populates="ctc_attributes")
    attribute_group = relationship("CTCAttributeGroup", back_populates="attributes")
    data_type = relationship("CTCDataType", back_populates="attributes")
    uom = relationship("CTCUnitOfMeasure", back_populates="attributes")

    # Indexes
    __table_args__ = (
        Index('idx_ctc_attributes_uuid', 'uuid'),
        Index('idx_ctc_attributes_category_id', 'category_id'),
        Index('idx_ctc_attributes_store', 'store'),
        Index('idx_ctc_attributes_rank', 'rank'),
    )


# Add relationship to CTCCategory for CTC attributes
CTCCategory.ctc_attributes = relationship("CTCAttribute", back_populates="category", cascade="all, delete-orphan")


### DISTRIBUTOR AND BRAND MODELS ###

class Distributor(Base):
    """
    Stores distributor information
    """
    __tablename__ = "distributors"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    edi = Column(Boolean, nullable=False, default=False)
    auto_claim_over_charge = Column(Boolean, nullable=False, default=False)
    is_central = Column(Boolean, nullable=False, default=True)
    icon_owner = Column(String, nullable=True)
    gln = Column(String, nullable=True)
    business_number = Column(String, nullable=True)
    accounting_date = Column(Integer, nullable=True)
    web_portal_url = Column(String, nullable=True)
    pp_claim_from = Column(String, nullable=True)
    fis_minimum_order = Column(String, nullable=True)
    default_extended_credits_code = Column(String, nullable=True)
    default_extended_credits_name = Column(String, nullable=True)

    # Relationships
    brands = relationship("Brand", back_populates="distributor")

    # Indexes
    __table_args__ = (
        Index('idx_distributors_uuid', 'uuid'),
        Index('idx_distributors_code', 'code'),
        Index('idx_distributors_store', 'store'),
    )


class Brand(Base):
    """
    Stores brand information with relationship to distributors
    """
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    active = Column(Boolean, nullable=False, default=True)
    modified_by = Column(String, nullable=False)
    modified = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    deleted_by = Column(String, nullable=True)
    deleted = Column(DateTime, nullable=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    store = Column(String, nullable=False)
    is_hof_pref = Column(Boolean, nullable=False, default=True)
    comments = Column(Text, nullable=True)
    narta_rept = Column(Boolean, nullable=False, default=True)

    # Foreign key to distributor
    distributor_id = Column(
        Integer,
        ForeignKey("distributors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    distributor = relationship("Distributor", back_populates="brands")

    # Indexes
    __table_args__ = (
        Index('idx_brands_uuid', 'uuid'),
        Index('idx_brands_code', 'code'),
        Index('idx_brands_store', 'store'),
        Index('idx_brands_distributor_id', 'distributor_id'),
    )


### REBATE MODELS ###

class RebateAgreement(Base):
    __tablename__ = "rebate_agreements"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    agreement_type = Column(
        Enum("vendor", "customer", name="agreement_types"), nullable=False
    )
    distributor_id = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    calc_frequency = Column(
        Enum(
            "invoice",
            "daily",
            "monthly",
            "quarterly",
            "yearly",
            name="calc_frequencies",
        ),
        nullable=False,
    )
    basis = Column(Enum("quantity", "amount", name="rebate_bases"), nullable=False)
    rate_type = Column(
        Enum("percentage", "per_unit", "fixed", name="rate_types"), nullable=False
    )
    approval_required = Column(Boolean, default=False, nullable=False)
    status = Column(
        Enum("active", "expired", name="rebate_statuses"), default="active", nullable=False
    )

    # Relationships
    products = relationship(
        "RebateAgreementProduct", back_populates="agreement", cascade="all, delete-orphan"
    )
    tiers = relationship(
        "RebateTier", back_populates="agreement", cascade="all, delete-orphan"
    )
    claims = relationship(
        "RebateClaim", back_populates="agreement", cascade="all, delete-orphan"
    )


class RebateAgreementProduct(Base):
    __tablename__ = "rebate_agreement_products"

    id = Column(Integer, primary_key=True)
    rebate_agreement_id = Column(
        Integer, ForeignKey("rebate_agreements.id"), nullable=False
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("ctc_categories.id"), nullable=True)

    # Relationships
    agreement = relationship("RebateAgreement", back_populates="products")
    product = relationship("ProductModel", back_populates="rebate_agreements")


class RebateTier(Base):
    __tablename__ = "rebate_tiers"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    rebate_agreement_id = Column(
        Integer, ForeignKey("rebate_agreements.id"), nullable=False
    )
    rebate_agreement_uuid = Column(String, nullable=False)

    # Thresholds—use quantity fields for quantity-based deals,
    # amount fields for amount-based deals.
    from_quantity = Column(Numeric, nullable=True)
    to_quantity = Column(Numeric, nullable=True)
    from_amount = Column(Numeric, nullable=True)
    to_amount = Column(Numeric, nullable=True)

    # Rebate value and interpretation unit
    rebate_value = Column(Numeric, nullable=False)
    rebate_unit = Column(
        Enum("percentage", "per_unit", "fixed", name="rebate_units"), nullable=False
    )

    agreement = relationship("RebateAgreement", back_populates="tiers")


class RebateClaim(Base):
    __tablename__ = "rebate_claims"

    id = Column(Integer, primary_key=True)
    rebate_agreement_id = Column(
        Integer, ForeignKey("rebate_agreements.id"), nullable=False
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    # TODO: Uncomment when invoice_lines table is available
    # invoice_line_id = Column(Integer, ForeignKey("invoice_lines.id"), nullable=True)

    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)

    quantity_accumulated = Column(Numeric, nullable=True)
    amount_accumulated = Column(Numeric, nullable=True)
    rebate_amount = Column(Numeric, nullable=False)

    status = Column(
        Enum("To Calculate", "Pending", "Approved", "Paid", name="claim_statuses"),
        default="To Calculate",
        nullable=False,
    )
    calculation_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    agreement = relationship("RebateAgreement", back_populates="claims")
    product = relationship("ProductModel", back_populates="rebate_claims")

