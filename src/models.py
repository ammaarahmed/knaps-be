from pydantic import BaseModel, Field
from typing import Literal, Optional, Union, List
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID, uuid4


class ORMBase(BaseModel):
    model_config = {"from_attributes": True}

# Auth models
class Org(ORMBase):
    org_name: str
    org_id: int
    org_uuid: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

class Store(ORMBase):
    store_name: str
    store_id: int
    store_uuid: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    level: Optional[Literal['superadmin', 'admin', 'user']] = None
    org: Optional[Org] = None
    store: Optional[Store] = None
    created_at: datetime
    updated_at: datetime
    
class Token(ORMBase):
    access_token: str
    token_type: str

# Price Level models
class PriceLevel(ORMBase):
    id: Optional[int] = None
    price_level: str  # e.g., "MWP", "Trade", "GO", "RRP"
    type: str  # e.g., "Standard", "Promotional", "Bulk", etc.
    value_excl: Decimal  # Value excluding tax
    value_incl: Optional[Decimal] = None  # Value including tax
    comments: Optional[str] = None  # Additional comments about this price level
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class InsertPriceLevel(ORMBase):
    price_level: str
    type: str
    value_excl: Decimal
    value_incl: Optional[Decimal] = None
    comments: Optional[str] = None

# Product models
class InsertProduct(ORMBase):
    distributor_name: str
    brand_name: str
    product_code: str
    product_secondary_code: Optional[str] = None
    product_name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    shipping_class: Optional[str] = None
    category_name: str
    product_availability: str = 'In Stock'
    status: str = 'Active'
    online: bool = True
    superceded_by: Optional[str] = None
    ean: Optional[str] = None
    pack_size: int = 1
    price_levels: List[InsertPriceLevel] = []
    core_group: Optional[str] = None
    tax_exmt: bool = False
    hyperlink: Optional[str] = None
    web_title: Optional[str] = None
    features_and_benefits_codes: Optional[str] = None
    badges_codes: Optional[str] = None
    stock_unmanaged: bool = False

class Product(ORMBase):
    uuid: Optional[str] = None  # Optional UUID field for updates
    distributor_name: Optional[str] = None
    brand_name: Optional[str] = None
    product_code: Optional[str] = None
    product_secondary_code: Optional[str] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    shipping_class: Optional[str] = None
    category_name: Optional[str] = None
    product_availability: Optional[str] = None
    status: Optional[str] = None
    online: Optional[bool] = None
    superceded_by: Optional[str] = None
    ean: Optional[str] = None
    pack_size: Optional[int] = None
    price_levels: Optional[List[PriceLevel]] = None
    core_group: Optional[str] = None
    tax_exmt: Optional[bool] = None
    hyperlink: Optional[str] = None
    web_title: Optional[str] = None
    features_and_benefits_codes: Optional[str] = None
    badges_codes: Optional[str] = None
    stock_unmanaged: Optional[bool] = None

# Rebate models

class RebateTierCreate(ORMBase):
    rebate_agreement_uuid: Optional[str] = None
    from_quantity: Optional[float] = None
    to_quantity: Optional[float] = None  # None if open-ended
    from_amount: Optional[float] = None
    to_amount: Optional[float] = None  # None if open-ended
    rebate_value: float         # percentage or per-unit amount
    rebate_unit: Literal["percentage", "per_unit", "fixed"]

class RebateAgreementCreate(ORMBase):
    agreement_type: Literal["vendor", "customer"]
    distributor_id: int  # vendor ID or customer ID 
    description: str  # Changed from 'name' to match database schema
    start_date: date
    end_date: date
    calc_frequency: Literal["invoice", "daily", "monthly", "quarterly", "yearly"]  # Added 'daily', kept 'invoice'
    basis: Literal["quantity", "amount"] 
    rate_type: Literal["percentage", "per_unit", "fixed"]
    approval_required: bool = False
    products: List[int] = []           # product IDs this agreement applies to
    product_category_ids: List[int] = []  # alternatively or additionally, categories
    tiers: List[RebateTierCreate] = []  # tier definitions (if any)

class RebateTierRead(ORMBase):
    id: int
    uuid: str
    agreement_id: int
    rebate_agreement_uuid: str
    from_quantity: Optional[float] = None
    to_quantity: Optional[float] = None  # None if open-ended
    from_amount: Optional[float] = None
    to_amount: Optional[float] = None  # None if open-ended
    rebate_value: float         # percentage or per-unit amount
    rebate_unit: Literal["percentage", "per_unit", "fixed"]

class RebateAgreementRead(ORMBase):
    id: int
    uuid: str
    agreement_type: str 
    distributor_id: int 
    description: str  # Changed from 'name' to match database schema
    start_date: date 
    end_date: date 
    calc_frequency: str 
    basis: str 
    rate_type: str 
    approval_required: bool 
    products: List[int] 
    product_category_ids: List[int] 
    tiers: List[RebateTierRead] 
    status: str


# Analytics types
class ProductAnalytics(ORMBase):
    product_id: int
    product_name: str
    product_code: str
    brand_name: str
    turnover_rate: float
    total_revenue: Decimal
    current_stock: int

class OverallAnalytics(ORMBase):
    average_turnover_rate: float
    total_revenue: Decimal
    total_products: int
    active_products: int
    total_brands: int
    total_categories: int
    total_distributors: int

class CategoryAttributeSchema(ORMBase):
    id: Optional[int]
    name: str
    unit: Optional[str] = None
    value: str


class ProductCategorySchema(ORMBase):
    id: int
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str]
    deleted: Optional[datetime]
    code: str
    name: str
    store: str
    product_type_id: int
    attributes: List[CategoryAttributeSchema] = []

    class Config:
        orm_mode = True


class ProductTypeSchema(ORMBase):
    id: int
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str]
    deleted: Optional[datetime]
    code: str
    name: str
    store: str
    product_class_id: int
    categories: List[ProductCategorySchema] = []


class ProductClassSchema(ORMBase):
    id: int
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str]
    deleted: Optional[datetime]
    code: str
    name: str
    store: str
    types: List[ProductTypeSchema] = []

