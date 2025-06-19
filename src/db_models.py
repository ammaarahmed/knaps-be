from datetime import datetime, date
from sqlalchemy import (Column, Integer, Text, Boolean, String, Numeric, DateTime, Date, ForeignKey)
from sqlalchemy.orm import relationship

from .database import Base

class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
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
    mwp = Column(Numeric(10, 2))
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

    sell_ins = relationship("SellInModel", back_populates="product")
    sell_throughs = relationship("SellThroughModel", back_populates="product")

class SellInModel(Base):
    __tablename__ = "sell_ins"

    id = Column(Integer, primary_key=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    month_partition = Column(String(7), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("ProductModel", back_populates="sell_ins")

class SellThroughModel(Base):
    __tablename__ = "sell_throughs"

    id = Column(Integer, primary_key=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_revenue = Column(Numeric(10, 2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    month_partition = Column(String(7), nullable=False)
    customer_info = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("ProductModel", back_populates="sell_throughs")
