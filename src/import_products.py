import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import init_db, get_async_session
from .db_models import Distributor, Brand, ProductModel, PriceLevel, MyPrice


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        return None


def parse_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


async def get_or_create_distributor(session: AsyncSession, data: Dict[str, Any]) -> Distributor:
    stmt = select(Distributor).where(Distributor.id == data["id"])
    result = await session.execute(stmt)
    distributor = result.scalar_one_or_none()
    if distributor:
        return distributor
    distributor = Distributor(
        id=data["id"],
        active=data.get("active", True),
        modified_by=data.get("modified_by"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        code=data.get("code"),
        name=data.get("name"),
        store=data.get("store"),
        icon_owner=data.get("icon_owner"),
    )
    session.add(distributor)
    await session.flush()
    return distributor


async def get_or_create_brand(session: AsyncSession, data: Dict[str, Any], distributor: Distributor) -> Brand:
    stmt = select(Brand).where(Brand.id == data["id"])
    result = await session.execute(stmt)
    brand = result.scalar_one_or_none()
    if brand:
        return brand
    brand = Brand(
        id=data["id"],
        active=data.get("active", True),
        modified_by=data.get("modified_by"),
        modified=parse_dt(data.get("modified")),
        created_by=data.get("created_by"),
        created=parse_dt(data.get("created")),
        deleted_by=data.get("deleted_by"),
        deleted=parse_dt(data.get("deleted")),
        code=data.get("code"),
        name=data.get("name"),
        store=data.get("store"),
        distributor_id=distributor.id,
    )
    session.add(brand)
    await session.flush()
    return brand


async def create_or_update_product(session: AsyncSession, data: Dict[str, Any], brand: Brand, distributor: Distributor) -> ProductModel:
    stmt = select(ProductModel).where(ProductModel.id == data["id"])
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    core_group = data.get("core_group")
    core_group_code = None
    if isinstance(core_group, dict):
        core_group_code = core_group.get("code")
    elif core_group:
        core_group_code = str(core_group)

    fields = dict(
        uuid=str(data.get("uuid", "") or data.get("id")),
        distributor_id=distributor.id,
        brand_id=brand.id,
        distributor_name=distributor.name,
        brand_name=brand.name,
        product_code=data.get("code"),
        product_secondary_code=data.get("secondary_code"),
        product_name=data.get("name"),
        description=data.get("description"),
        summary=data.get("summary"),
        shipping_class=None,
        category_name="",
        product_availability="In Stock",
        superceded_by=None,
        replaces=None,
        status="Active",
        online=data.get("online", False),
        ean=data.get("ean"),
        pack_size=data.get("pack_size") or 1,
        core_group=core_group_code,
        tax_exmt=data.get("tax_exmt", False),
        hyperlink=None,
        web_title=None,
        features_and_benefits_codes=None,
        badges_codes=None,
        stock_unmanaged=data.get("stock_unmanaged", False),
        active=data.get("active", True),
        purchaser=data.get("purchaser"),
        icon_owner=data.get("icon_owner"),
        is_gift_card=data.get("is_gift_card", False),
        gift_card_limit=parse_decimal(data.get("gift_card_limit")),
        has_promotions=data.get("has_promotions", False),
        store=data.get("store"),
        web_link=data.get("web_link"),
        edit_link=data.get("edit_link"),
        created_by=data.get("created_by"),
        modified_by=data.get("modified_by"),
        created_at=parse_dt(data.get("created")),
        modified_at=parse_dt(data.get("modified")),
        deleted_by=data.get("deleted_by"),
        deleted_at=parse_dt(data.get("deleted")),
    )

    if product:
        for k, v in fields.items():
            setattr(product, k, v)
    else:
        product = ProductModel(id=data["id"], **fields)
        session.add(product)
        await session.flush()

    return product


async def create_price_levels(session: AsyncSession, product: ProductModel, prices: Dict[str, Any]):
    for key, pdata in prices.items():
        level_code = pdata.get("price_level", {}).get("code", key)
        type_code = pdata.get("price_level", {}).get("price_type", {}).get("code")
        price = PriceLevel(
            product_id=product.id,
            price_level=level_code,
            type=type_code or "",
            value_excl=parse_decimal(pdata.get("value_stor")),
            value_incl=parse_decimal(pdata.get("value_stor_incl")),
            comments=pdata.get("comments"),
            active=pdata.get("active", True),
            external_id=pdata.get("id"),
            store=pdata.get("store"),
            value_stor=parse_decimal(pdata.get("value_stor")),
            value_stor_incl=parse_decimal(pdata.get("value_stor_incl")),
            value_hoff=parse_decimal(pdata.get("value_hoff")),
            value_hoff_incl=parse_decimal(pdata.get("value_hoff_incl")),
            valid_start=parse_dt(pdata.get("valid_start")),
            valid_end=parse_dt(pdata.get("valid_end")),
            claim_start=parse_dt(pdata.get("claim_start")),
            claim_end=parse_dt(pdata.get("claim_end")),
            bonus_status=pdata.get("bonus_status", {}).get("code"),
            initial_value_stor=parse_decimal(pdata.get("initial_value_stor")),
            initial_value_stor_incl=parse_decimal(pdata.get("initial_value_stor_incl")),
            initial_value_hoff=parse_decimal(pdata.get("initial_value_hoff")),
            initial_value_hoff_incl=parse_decimal(pdata.get("initial_value_hoff_incl")),
            has_overrides=pdata.get("has_overrides", False),
            current_override_price=parse_decimal(pdata.get("current_override_price")),
            created_by=pdata.get("created_by"),
            modified_by=pdata.get("modified_by"),
            created_at=parse_dt(pdata.get("created")),
            updated_at=parse_dt(pdata.get("modified")),
            deleted_by=pdata.get("deleted_by"),
            deleted_at=parse_dt(pdata.get("deleted")),
        )
        session.add(price)


async def create_my_price(session: AsyncSession, product: ProductModel, data: Dict[str, Any]):
    if not data:
        return
    my_price = MyPrice(
        product_id=product.id,
        active=data.get("active", True),
        go=parse_decimal(data.get("go")),
        go_special=parse_decimal(data.get("go_special")),
        rrp=parse_decimal(data.get("rrp")),
        rrp_special=parse_decimal(data.get("rrp_special")),
        trade=parse_decimal(data.get("trade")),
        off_invoice=parse_decimal(data.get("off_invoice")),
        invoice=parse_decimal(data.get("invoice")),
        vendor_percent=parse_decimal(data.get("vendor_percent")),
        vendor_dollar=parse_decimal(data.get("vendor_dollar")),
        bonus_percent=parse_decimal(data.get("bonus_percent")),
        bonus_dollar=parse_decimal(data.get("bonus_dollar")),
        brand_percent=parse_decimal(data.get("brand_percent")),
        hoff_percent=parse_decimal(data.get("hoff_percent")),
        hoff_dollar=parse_decimal(data.get("hoff_dollar")),
        net=parse_decimal(data.get("net")),
        sellthru_dollar=parse_decimal(data.get("sellthru_dollar")),
        nac=parse_decimal(data.get("nac")),
        off_invoice_hoff=parse_decimal(data.get("off_invoice_hoff")),
        invoice_hoff=parse_decimal(data.get("invoice_hoff")),
        vendor_percent_hoff=parse_decimal(data.get("vendor_percent_hoff")),
        vendor_dollar_hoff=parse_decimal(data.get("vendor_dollar_hoff")),
        bonus_percent_hoff=parse_decimal(data.get("bonus_percent_hoff")),
        bonus_dollar_hoff=parse_decimal(data.get("bonus_dollar_hoff")),
        brand_percent_hoff=parse_decimal(data.get("brand_percent_hoff")),
        net_hoff=parse_decimal(data.get("net_hoff")),
        sellthru_dollar_hoff=parse_decimal(data.get("sellthru_dollar_hoff")),
        nac_hoff=parse_decimal(data.get("nac_hoff")),
        created_at=parse_dt(data.get("created")),
        modified_at=parse_dt(data.get("modified")),
    )
    session.add(my_price)


async def import_products(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    async with get_async_session() as session:
        for pdata in products:
            distributor = await get_or_create_distributor(session, pdata["brand"]["distributor"])
            brand = await get_or_create_brand(session, pdata["brand"], distributor)
            product = await create_or_update_product(session, pdata, brand, distributor)
            await create_price_levels(session, product, pdata.get("all_prices", {}))
            await create_my_price(session, product, pdata.get("my_prices"))
        await session.commit()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Import products from JSON file")
    parser.add_argument("path", help="Path to JSON file")
    args = parser.parse_args()

    await init_db(drop_existing=False)
    await import_products(args.path)
    print("Import completed")


if __name__ == "__main__":
    asyncio.run(main())
