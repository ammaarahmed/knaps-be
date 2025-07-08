from fastapi import APIRouter, HTTPException, Response
from typing import List
from ...models import Product, InsertProduct, ProductCTCCategoryRead, ProductCTCHierarchy
from ...storage import storage
from ...ctc_storage import CTCStorage
from ...models import AssignProductToCategoryRequest
import logging

logger = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/products")

ctc_storage = CTCStorage()

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

@router.get("/{product_code}/ctc-hierarchy", response_model=ProductCTCHierarchy)
async def get_product_ctc_hierarchy(product_code: str):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Get the first CTC category for this product (if any)
    ctc_categories = await ctc_storage.get_categories_by_product(product.id)
    if not ctc_categories:
        raise HTTPException(status_code=404, detail="No CTC category assigned to this product")
    category = ctc_categories[0]
    # Get type and class
    type_ = await ctc_storage.get_type_by_id(category.type_id)
    class_ = await ctc_storage.get_class_by_id(type_.class_id)
    return ProductCTCHierarchy(
        class_id=class_.id,
        class_code=class_.code,
        class_name=class_.name,
        type_id=type_.id,
        type_code=type_.code,
        type_name=type_.name,
        category_id=category.id,
        category_code=category.code,
        category_name=category.name
    )

@router.get("/{product_code}/ctc-categories", response_model=List[ProductCTCCategoryRead])
async def get_product_ctc_categories(product_code: str):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    ctc_categories = await ctc_storage.get_categories_by_product(product.id)
    result = []
    for category in ctc_categories:
        type_ = await ctc_storage.get_type_by_id(category.type_id)
        class_ = await ctc_storage.get_class_by_id(type_.class_id)
        result.append(ProductCTCCategoryRead(
            id=category.id,
            uuid=category.uuid,
            code=category.code,
            name=category.name,
            type_id=type_.id,
            type_code=type_.code,
            type_name=type_.name,
            class_id=class_.id,
            class_code=class_.code,
            class_name=class_.name
        ))
    return result

@router.post("/{product_code}/ctc-categories/{category_id}")
async def assign_product_to_ctc_category(product_code: str, category_id: int):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    success = await ctc_storage.assign_product_to_category(category_id, product.id)
    if not success:
        raise HTTPException(status_code=400, detail="Assignment failed (category or product not found)")
    return {"message": "Product assigned to CTC category"}

@router.delete("/{product_code}/ctc-categories/{category_id}")
async def unassign_product_from_ctc_category(product_code: str, category_id: int):
    product = await storage.get_product_by_code(product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Only unassign if this product is assigned to this category
    ctc_categories = await ctc_storage.get_categories_by_product(product.id)
    if not any(cat.id == category_id for cat in ctc_categories):
        raise HTTPException(status_code=404, detail="Product is not assigned to this CTC category")
    # Unassign by setting product_id to None
    await ctc_storage.remove_product_from_category(category_id)
    return {"message": "Product unassigned from CTC category"}

@router.get("/ctc/categories/{category_id}/products")
async def get_products_by_ctc_category(category_id: int):
    products = await ctc_storage.get_products_by_category(category_id)
    return products
