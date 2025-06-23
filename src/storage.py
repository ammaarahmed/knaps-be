from typing import List, Optional, Literal
from sqlalchemy import select
from .database import get_async_session
from .db_models import ProductModel, DealsModel
from .models import (
    BaseDeal,
    Product,
    InsertProduct,
    ProductAnalytics,
    OverallAnalytics,
)
import logging 
import uuid

logger = logging.getLogger('uvicorn.error')


def to_schema(obj, schema_cls):
    if hasattr(schema_cls, "model_validate"):
        logger.debug(f"Model {obj} or {schema_cls}")
        return schema_cls.model_validate(obj, from_attributes=True)
    return schema_cls.from_orm(obj)


class SQLStorage:
    # Product operations
    async def get_products(self) -> List[Product]:
        async with get_async_session() as session:
            result = await session.execute(select(ProductModel))
            return [to_schema(row, Product) for row in result.scalars().all()]

    async def get_product(self, pid: int) -> Optional[Product]:
        async with get_async_session() as session:
            result = await session.get(ProductModel, pid)
            return to_schema(result, Product) if result else None

    async def get_product_by_code(self, code: str) -> Optional[Product]:
        async with get_async_session() as session:
            stmt = select(ProductModel).where(ProductModel.product_code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, Product) if row else None
    
    async def get_product_by_uuid(self, uuid: str) -> Optional[Product]:
        async with get_async_session() as session:
            stmt = select(ProductModel).where(ProductModel.uuid == uuid)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, Product) if row else None

    async def search_products(self, query: str) -> List[Product]:
        q = f"%{query.lower()}%"
        logger.info(f"Printing query {q}")
        async with get_async_session() as session:
            stmt = select(ProductModel).where(
                (ProductModel.product_name.ilike(q))
                | (ProductModel.product_code.ilike(q))
                | (ProductModel.brand_name.ilike(q))
                | (ProductModel.category_name.ilike(q))
            )
            result = await session.execute(stmt)
            return [to_schema(p, Product) for p in result.scalars().all()]

    async def create_product(self, data: InsertProduct) -> Product:
        async with get_async_session() as session:
            product_data = data.dict()
            product_data['uuid'] = str(uuid.uuid4())
            obj = ProductModel(**product_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, Product)

    async def update_product(self, pid: int, data: dict) -> Optional[Product]:
        async with get_async_session() as session:
            obj = await session.get(ProductModel, pid)
            if not obj:
                return None
            for k, v in data.items():
                setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, Product)

    async def delete_product(self, pid: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(ProductModel, pid)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # Deal operations
    async def create_deal(self, data: BaseDeal) -> BaseDeal:
        async with get_async_session() as session:
            deal_data = data.dict()
            deal_data['uuid'] = str(uuid.uuid4())
            obj = DealsModel(**deal_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, BaseDeal)

    async def update_deal(self, uuid: str, data: BaseDeal) -> BaseDeal:
        async with get_async_session() as session:
            obj = await session.get(DealsModel, uuid)
            if not obj:
                return None
            for k, v in data.dict().items():
                setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, BaseDeal)

    async def delete_deal(self, uuid: str) -> bool:
        async with get_async_session() as session:
            obj = await session.get(DealsModel, uuid)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True 
        
    async def get_deals(
        self, product_uuid: Optional[str] = None, product_code: Optional[str] = None, month: Optional[str] = None
    ) -> List[BaseDeal]:
        async with get_async_session() as session:
            stmt = select(DealsModel)
            if product_uuid is not None: 
                stmt = stmt.where(DealsModel.product_uuid == product_uuid)
            if product_code is not None:
                stmt = stmt.where(DealsModel.product_code == product_code)
            if month:
                stmt = stmt.where(DealsModel.yeamonth_partition == month)
            result = await session.execute(stmt)
            return [to_schema(s, BaseDeal) for s in result.scalars().all()]

    async def get_by_specific_dealtype(self,
        deal_type: Literal['sell_in', 'sell_through', 'price_protection', 'off_invoice_discount'],
        product_code: Optional[int] = None, 
        yearmonth: Optional[str] = None, 
    ) -> List[BaseDeal]:
        async with get_async_session() as session:
            stmt = select(DealsModel)
            if product_code is not None:
                stmt = stmt.where(DealsModel.product_code == product_code)
            if yearmonth:
                stmt = stmt.where(DealsModel.yeamonth_partition == yearmonth)
            if deal_type:
                stmt = stmt.where(DealsModel.deal_type == deal_type)
            result = await session.execute(stmt)
            return [to_schema(s, BaseDeal) for s in result.scalars().all()]
        
    async def get_deal(self, uuid: str) -> BaseDeal:
        async with get_async_session() as session:
            result = await session.get(DealsModel, uuid)
            return to_schema(result, BaseDeal) if result else None
        
    async def create_deals(self, data: List[BaseDeal]) -> List[BaseDeal]:
        async with get_async_session() as session:
            objs = []
            for d in data:
                deal_data = d.dict()
                deal_data['uuid'] = str(uuid.uuid4())
                objs.append(DealsModel(**deal_data))
            session.add_all(objs)
            await session.commit()
            for obj in objs:
                await session.refresh(obj)
            return [to_schema(o, BaseDeal) for o in objs]   

    # Analytics operations
    async def get_product_analytics(
        self, product_code: Optional[int] = None
    ) -> List[ProductAnalytics]:
        async with get_async_session() as session:
            prod_stmt = select(ProductModel)
            if product_code is not None:
                prod_stmt = prod_stmt.where(ProductModel.id == product_code)
            products = (await session.execute(prod_stmt)).scalars().all()
            analytics: List[ProductAnalytics] = []
            for p in products:
                analytics.append(
                    ProductAnalytics(
                        product_id=p.id,
                        product_name=p.product_name,
                        product_code=p.product_code,
                        brand_name=p.brand_name,
                        turnover_rate=0.0,  # TODO: Calculate from deals data
                        total_revenue=p.trade,  # TODO: Calculate from deals data
                        current_stock=0,  # TODO: Get from inventory data
                    )
                )
            analytics.sort(key=lambda a: a.product_name)
            return analytics

    async def get_overall_analytics(self) -> OverallAnalytics:
        async with get_async_session() as session:
            products = (await session.execute(select(ProductModel))).scalars().all()
            total_products = len(products)
            active_products = len([p for p in products if p.status == 'Active'])
            total_brands = len(set(p.brand_name for p in products))
            total_categories = len(set(p.category_name for p in products))
            total_distributors = len(set(p.distributor_name for p in products))
            
            return OverallAnalytics(
                average_turnover_rate=0.0,  # TODO: Calculate from deals data
                total_revenue=sum(p.trade for p in products),  # TODO: Calculate from deals data
                total_products=total_products,
                active_products=active_products,
                total_brands=total_brands,
                total_categories=total_categories,
                total_distributors=total_distributors,
            )


storage = SQLStorage()
