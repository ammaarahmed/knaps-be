from fastapi import APIRouter
from typing import List, Optional
from ...models import ProductAnalytics, OverallAnalytics
from ...storage import storage

router = APIRouter(prefix="/analytics")

@router.get("/products", response_model=List[ProductAnalytics])
async def product_analytics(product_id: Optional[str] = None, month: Optional[str] = None):
    return await storage.get_product_analytics(product_id, month)

@router.get("/overall", response_model=OverallAnalytics)
async def overall_analytics(month: Optional[str] = None):
    return await storage.get_overall_analytics(month)
