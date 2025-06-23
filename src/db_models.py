from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (Column, Integer, Text, Boolean, String, Numeric, DateTime, Date, ForeignKey)
from sqlalchemy.orm import relationship

from .database import Base

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
    mwp = Column(Numeric(10, 2), nullable=False)
    trade = Column(Numeric(10, 2), nullable=False)
    go = Column(Numeric(10, 2))
    rrp = Column(Numeric(10, 2), nullable=False)
    core_group = Column(Text)
    tax_exmt = Column(Boolean, nullable=False, default=False)
    hyperlink = Column(Text)
    web_title = Column(Text)
    features_and_benefits_codes = Column(Text)
    badges_codes = Column(Text)
    stock_unmanaged = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deals = relationship("DealsModel", back_populates="product")

class DealsModel(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String, nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    deal_type = Column(String, nullable=False, default="sell_in")
    deal_id = Column(Integer, nullable=False)  
    amount_type = Column(String, nullable=False, default="quantity")
    amount = Column(Numeric, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    yeamonth_partition = Column(String(7), nullable=False)
    provider = Column(String, nullable=False, default="head office")
    store_amount = Column(Numeric)
    head_office_amount = Column(Numeric)
    trade_price = Column(Numeric)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String)

    product = relationship("ProductModel", back_populates="deals")




