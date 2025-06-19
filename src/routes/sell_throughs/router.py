from fastapi import APIRouter
from typing import List, Optional
from ...models import SellThrough, InsertSellThrough
from ...storage import storage

router = APIRouter(prefix="/sell-throughs")

@router.get("", response_model=List[SellThrough])
async def list_sell_throughs(product_id: Optional[int] = None, month: Optional[str] = None):
    return await storage.get_sell_throughs(product_id, month)

@router.post("", response_model=SellThrough, status_code=201)
async def create_sell_through(data: InsertSellThrough):
    return await storage.create_sell_through(data)
