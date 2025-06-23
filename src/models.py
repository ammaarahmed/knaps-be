from pydantic import BaseModel, Field
from typing import Literal, Optional, Union
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
    mwp: Optional[Decimal] = None
    trade: Decimal
    go: Optional[Decimal] = None
    rrp: Decimal
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
    mwp: Optional[Decimal] = None
    trade: Optional[Decimal] = None
    go: Optional[Decimal] = None
    rrp: Optional[Decimal] = None
    core_group: Optional[str] = None
    tax_exmt: Optional[bool] = None
    hyperlink: Optional[str] = None
    web_title: Optional[str] = None
    features_and_benefits_codes: Optional[str] = None
    badges_codes: Optional[str] = None
    stock_unmanaged: Optional[bool] = None

# SellThrough models
class BaseDeal(ORMBase):
    deal_id: Optional[int] = None
    deal_uuid: Optional[UUID] = None
    deal_code: Optional[str] = None
    deal_type: Literal['sell_in', 'sell_through', 'price_protection', 'off_invoice_discount']
    product_id: int
    product_uuid: UUID = Field(default_factory=uuid4)
    amount_type: Literal['quantity', 'value']
    amount: Decimal
    start_date: date 
    end_date: date
    yeamonth_partition: str = Field(..., min_length=7, max_length=7)
    provider: Literal['head office', 'distributor', 'narta']
    store_amount: Optional[Decimal] = None
    head_office_amount: Optional[Decimal] = None
    trade_price: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


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
