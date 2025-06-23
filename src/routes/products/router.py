from fastapi import APIRouter, HTTPException, Response
from typing import List
from ...models import Product, InsertProduct
from ...storage import storage
import logging

logger = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/products")

@router.get("", response_model=List[Product])
async def list_products():
    return await storage.get_products()

@router.get("/search", response_model=List[Product])
async def search_products(q: str):
    logger.info(f"Searching for product: {q}")
    if len(q) < 2:
        return []
    return await storage.search_products(q)

@router.get("/{product_code}", response_model=Product)
async def get_product(product_code: str):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("", response_model=Product, status_code=201)
async def create_product(data: InsertProduct):
    existing = await storage.get_product_by_code(data.product_code)
    if existing:
        raise HTTPException(status_code=400, detail="Product code already exists")
    return await storage.create_product(data)

@router.put("/{product_code}", response_model=Product)
async def update_product(product_code: int, data: Product):
    product = await storage.update_product(product_code, data.dict(exclude_unset=True))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.delete("/{product_code}", status_code=204)
async def delete_product(product_code: int):
    deleted = await storage.delete_product(product_code)
    if not deleted:        
        raise HTTPException(status_code=404, detail="Product not found")
    return Response(status_code=204)

@router.post("/bulk")
async def bulk_create(products: List[InsertProduct]):
    logger.info("Starting bulk product upload")
    results: List[Product] = []
    errors: List[str] = []
    for data in products:
        logger.info(f"Uploading {data.product_code}, product data {data}")
        try:
            if await storage.get_product_by_code(data.product_code):
                logger.info(f"Product code already exists {data.product_code}")
                #TODO add check if attributes are different then update 
                continue
            product = await storage.create_product(data)
            results.append(product)
        except Exception as e:
            logger.warning(f"Failed to create product with code {data.product_code} with error {e}")
            errors.append(data.product_code)
    return {
        "success": len(results),
        "errors": len(errors),
        "created": results,
        "failed": errors,
    }
