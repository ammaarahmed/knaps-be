from typing import List, Optional
from sqlalchemy import select
from .database import AsyncSessionLocal
from .db_models import ProductModel, SellInModel, SellThroughModel
from .models import (
    Product,
    InsertProduct,
    UpdateProduct,
    SellIn,
    InsertSellIn,
    SellThrough,
    InsertSellThrough,
    ProductAnalytics,
    OverallAnalytics,
)
import logging 

logger = logging.getLogger('uvicorn.error')


def to_schema(obj, schema_cls):
    if hasattr(schema_cls, "model_validate"):
        logger.debug(f"Model {obj} or {schema_cls}")
        return schema_cls.model_validate(obj, from_attributes=True)
    return schema_cls.from_orm(obj)


class SQLStorage:
    # Product operations
    async def get_products(self) -> List[Product]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ProductModel))
            return [to_schema(row, Product) for row in result.scalars().all()]

    async def get_product(self, pid: int) -> Optional[Product]:
        async with AsyncSessionLocal() as session:
            result = await session.get(ProductModel, pid)
            return to_schema(result, Product) if result else None

    async def get_product_by_code(self, code: str) -> Optional[Product]:
        async with AsyncSessionLocal() as session:
            stmt = select(ProductModel).where(ProductModel.product_code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, Product) if row else None

    async def search_products(self, query: str) -> List[Product]:
        q = f"%{query.lower()}%"
        logger.info(f"Printing query {q}")
        async with AsyncSessionLocal() as session:
            stmt = select(ProductModel).where(
                (ProductModel.product_name.ilike(q))
                | (ProductModel.product_code.ilike(q))
                | (ProductModel.brand_name.ilike(q))
                | (ProductModel.category_name.ilike(q))
            )
            result = await session.execute(stmt)
            return [to_schema(p, Product) for p in result.scalars().all()]

    async def create_product(self, data: InsertProduct) -> Product:
        async with AsyncSessionLocal() as session:
            obj = ProductModel(**data.dict())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, Product)

    async def update_product(self, pid: int, data: dict) -> Optional[Product]:
        async with AsyncSessionLocal() as session:
            obj = await session.get(ProductModel, pid)
            if not obj:
                return None
            for k, v in data.items():
                setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, Product)

    async def delete_product(self, pid: int) -> bool:
        async with AsyncSessionLocal() as session:
            obj = await session.get(ProductModel, pid)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    # SellIn operations
    async def get_sell_ins(
        self, product_id: Optional[int] = None, month: Optional[str] = None
    ) -> List[SellIn]:
        async with AsyncSessionLocal() as session:
            stmt = select(SellInModel)
            if product_id is not None:
                stmt = stmt.where(SellInModel.product_id == product_id)
            if month:
                stmt = stmt.where(SellInModel.month_partition == month)
            result = await session.execute(stmt)
            return [to_schema(s, SellIn) for s in result.scalars().all()]

    async def create_sell_in(self, data: InsertSellIn) -> SellIn:
        async with AsyncSessionLocal() as session:
            obj = SellInModel(**data.dict())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, SellIn)

    # SellThrough operations
    async def get_sell_throughs(
        self, product_id: Optional[int] = None, month: Optional[str] = None
    ) -> List[SellThrough]:
        async with AsyncSessionLocal() as session:
            stmt = select(SellThroughModel)
            if product_id is not None:
                stmt = stmt.where(SellThroughModel.product_id == product_id)
            if month:
                stmt = stmt.where(SellThroughModel.month_partition == month)
            result = await session.execute(stmt)
            return [to_schema(s, SellThrough) for s in result.scalars().all()]

    async def create_sell_through(self, data: InsertSellThrough) -> SellThrough:
        async with AsyncSessionLocal() as session:
            obj = SellThroughModel(**data.dict())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, SellThrough)

    # Analytics operations
    async def get_product_analytics(
        self, product_id: Optional[int] = None, month: Optional[str] = None
    ) -> List[ProductAnalytics]:
        async with AsyncSessionLocal() as session:
            prod_stmt = select(ProductModel)
            if product_id is not None:
                prod_stmt = prod_stmt.where(ProductModel.id == product_id)
            products = (await session.execute(prod_stmt)).scalars().all()
            analytics: List[ProductAnalytics] = []
            for p in products:
                si_stmt = select(SellInModel).where(SellInModel.product_id == p.id)
                st_stmt = select(SellThroughModel).where(
                    SellThroughModel.product_id == p.id
                )
                if month:
                    si_stmt = si_stmt.where(SellInModel.month_partition == month)
                    st_stmt = st_stmt.where(SellThroughModel.month_partition == month)
                sell_ins = (await session.execute(si_stmt)).scalars().all()
                sell_throughs = (await session.execute(st_stmt)).scalars().all()
                sell_in_qty = sum(si.quantity for si in sell_ins)
                sell_through_qty = sum(st.quantity for st in sell_throughs)
                total_revenue = sum(float(st.total_revenue) for st in sell_throughs)
                current_stock = sell_in_qty - sell_through_qty
                turnover_rate = (sell_through_qty / sell_in_qty * 100) if sell_in_qty else 0
                logger.info(f"Product ID {p.id} and var type {type(p.id)}")
                analytics.append(
                    ProductAnalytics(
                        product_id=p.id,
                        product_name=p.product_name,
                        product_code=p.product_code,
                        brand_name=p.brand_name,
                        sell_in_quantity=sell_in_qty,
                        sell_through_quantity=sell_through_qty,
                        turnover_rate=round(turnover_rate, 1),
                        total_revenue=total_revenue,
                        current_stock=current_stock,
                    )
                )
            analytics.sort(key=lambda a: a.total_revenue, reverse=True)
            return analytics

    async def get_overall_analytics(self, month: Optional[str] = None) -> OverallAnalytics:
        async with AsyncSessionLocal() as session:
            si_stmt = select(SellInModel)
            st_stmt = select(SellThroughModel)
            if month:
                si_stmt = si_stmt.where(SellInModel.month_partition == month)
                st_stmt = st_stmt.where(SellThroughModel.month_partition == month)
            sell_ins = (await session.execute(si_stmt)).scalars().all()
            sell_throughs = (await session.execute(st_stmt)).scalars().all()
            total_sell_in = sum(si.quantity for si in sell_ins)
            total_sell_through = sum(st.quantity for st in sell_throughs)
            total_revenue = sum(float(st.total_revenue) for st in sell_throughs)
            avg_turnover = (total_sell_through / total_sell_in * 100) if total_sell_in else 0
            return OverallAnalytics(
                total_sell_in=total_sell_in,
                total_sell_through=total_sell_through,
                average_turnover_rate=round(avg_turnover, 1),
                total_revenue=total_revenue,
            )


storage = SQLStorage()
