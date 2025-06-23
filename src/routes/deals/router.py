from fastapi import APIRouter
from typing import List, Optional
from ...models import BaseDeal
from ...storage import storage

router = APIRouter(prefix="/deals")

@router.get("", response_model=List[BaseDeal])
async def list_deals(product_uuid: Optional[str] = None, product_code: Optional[str] = None, month: Optional[str] = None):
    return await storage.get_deals(product_uuid, product_code, month)

@router.post("", response_model=BaseDeal, status_code=201)
async def create_deal(data: BaseDeal):
    return await storage.create_deal(data)

@router.get("/{uuid}", response_model=BaseDeal)
async def get_deal(uuid: int):
    return await storage.get_deal(uuid)

@router.put("/{uuid}", response_model=BaseDeal)
async def update_deal(uuid: str, data: BaseDeal):
    return await storage.update_deal(uuid, data)

@router.delete("/{uuid}", status_code=204)
async def delete_deal(uuid: str):
    return await storage.delete_deal(uuid)

@router.post("/bulk", response_model=List[BaseDeal], status_code=201)
async def create_deals(data: List[BaseDeal]):
    return await storage.create_deals(data)