from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime, date


class ORMBase(BaseModel):
    model_config = {"from_attributes": True}

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

class UpdateProduct(ORMBase):
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

class Product(InsertProduct):
    id: int
    created_at: datetime
    updated_at: datetime

# SellIn models
class InsertSellIn(ORMBase):
    product_id: int
    quantity: int
    unit_cost: Decimal
    total_cost: Decimal
    transaction_date: date
    month_partition: str = Field(..., min_length=7, max_length=7)
    notes: Optional[str] = None

class SellIn(InsertSellIn):
    id: int
    created_at: datetime

# SellThrough models
class InsertSellThrough(ORMBase):
    product_id: int
    quantity: int
    unit_price: Decimal
    total_revenue: Decimal
    transaction_date: date
    month_partition: str = Field(..., min_length=7, max_length=7)
    customer_info: Optional[str] = None

class SellThrough(InsertSellThrough):
    id: int
    created_at: datetime

# Analytics types
class ProductAnalytics(ORMBase):
    product_id: int
    product_name: str
    product_code: str
    brand_name: str
    sell_in_quantity: int
    sell_through_quantity: int
    turnover_rate: float
    total_revenue: Decimal
    current_stock: int

class OverallAnalytics(ORMBase):
    total_sell_in: int
    total_sell_through: int
    average_turnover_rate: float
    total_revenue: Decimal
