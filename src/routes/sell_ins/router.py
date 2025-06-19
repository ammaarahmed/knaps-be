from fastapi import APIRouter
from typing import List, Optional
from ...models import SellIn, InsertSellIn
from ...storage import storage

router = APIRouter(prefix="/sell-ins")

@router.get("", response_model=List[SellIn])
async def list_sell_ins(product_id: Optional[int] = None, month: Optional[str] = None):
    return await storage.get_sell_ins(product_id, month)

@router.post("", response_model=SellIn, status_code=201)
async def create_sell_in(data: InsertSellIn):
    return await storage.create_sell_in(data)
