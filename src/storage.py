import asyncio
from typing import List, Optional, Literal
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload
from .database import get_async_session
from .db_models import ProductModel, User, PriceLevel, RebateAgreement, RebateAgreementProduct, RebateTier, RebateClaim, CTCCategory
from .models import (
    Product,
    InsertProduct,
    ProductAnalytics,
    OverallAnalytics,
    RebateAgreementCreate,
    RebateAgreementRead,
    RebateTierCreate,
)
import logging 
import uuid
import json
import pandas as pd
from decimal import Decimal

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
            price_levels_data = product_data.pop('price_levels', [])
            product_data['uuid'] = str(uuid.uuid4())
            
            # Create the product
            obj = ProductModel(**product_data)
            session.add(obj)
            await session.flush()  # Flush to get the product ID
            
            # Create price levels
            for price_level_data in price_levels_data:
                price_level = PriceLevel(
                    product_id=obj.id,
                    **price_level_data
                )
                session.add(price_level)
            
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
                # Calculate total revenue from price levels (using Trade price level if available)
                total_revenue = Decimal('0.0')
                for price_level in p.price_levels:
                    if price_level.price_level == "Trade":
                        total_revenue = price_level.value_excl
                        break
                
                analytics.append(
                    ProductAnalytics(
                        product_id=p.id,
                        product_name=p.product_name,
                        product_code=p.product_code,
                        brand_name=p.brand_name,
                        turnover_rate=0.0,  # TODO: Calculate from deals data
                        total_revenue=total_revenue,  # Calculate from price levels
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
            
            # Calculate total revenue from price levels
            total_revenue = Decimal('0.0')
            for p in products:
                for price_level in p.price_levels:
                    if price_level.price_level == "Trade":
                        total_revenue += price_level.value_excl
                        break
            
            return OverallAnalytics(
                average_turnover_rate=0.0,  # TODO: Calculate from deals data
                total_revenue=total_revenue,  # Calculate from price levels
                total_products=total_products,
                active_products=active_products,
                total_brands=total_brands,
                total_categories=total_categories,
                total_distributors=total_distributors,
            )

    # User operations
    async def get_user(self, keycloak_id: str) -> User:
        async with get_async_session() as session:
            result = await session.get(User, keycloak_id)
            return to_schema(result, User) if result else None
    
    async def create_user(self, data: User) -> User:
        async with get_async_session() as session:
            obj = User(**data.dict())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, User)

    # Rebate operations
    async def create_rebate_agreement(self, data: RebateAgreementCreate) -> RebateAgreementRead:
        """Create a new rebate agreement with validation and business rules."""
        async with get_async_session() as session:
            # Validate input
            if not data.products and not data.product_category_ids:
                raise ValueError("At least one product or product category must be specified")
            
            if data.start_date >= data.end_date:
                raise ValueError("Start date must be before end date")
            
            # Validate tier ranges if provided
            if data.tiers:
                self._validate_tier_ranges(data.tiers, data.basis)
            
            # Check for overlapping agreements (same distributor, products, and date range)
            await self._check_overlapping_agreements(session, data)
            
            # Create the rebate agreement
            agreement_data = data.dict()
            products = agreement_data.pop('products', [])
            product_category_ids = agreement_data.pop('product_category_ids', [])
            tiers = agreement_data.pop('tiers', [])
            
            # Generate UUID for agreement
            agreement_data['uuid'] = str(uuid.uuid4())
            agreement = RebateAgreement(**agreement_data)
            session.add(agreement)
            await session.flush()  # Get the agreement ID and UUID
            
            # Create product associations
            for product_id in products:
                product_assoc = RebateAgreementProduct(
                    rebate_agreement_id=agreement.id,
                    product_id=product_id
                )
                session.add(product_assoc)
            
            # Create category associations
            for category_id in product_category_ids:
                category_assoc = RebateAgreementProduct(
                    rebate_agreement_id=agreement.id,
                    category_id=category_id
                )
                session.add(category_assoc)
            
            # Create tiers with UUIDs and parent agreement UUID
            for tier_data in tiers:
                tier = self._create_tier_from_data(tier_data, agreement.id, agreement.uuid, data.basis)
                session.add(tier)
            
            await session.commit()
            await session.refresh(agreement)
            
            # Return the created agreement with all related data
            return await self._build_rebate_agreement_response(session, agreement)
    
    async def get_rebate_agreements(
        self, 
        agreement_type: Optional[str] = None,
        distributor_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[RebateAgreementRead]:
        """Get rebate agreements with optional filtering."""
        async with get_async_session() as session:
            stmt = select(RebateAgreement)
            
            if agreement_type:
                stmt = stmt.where(RebateAgreement.agreement_type == agreement_type)
            if distributor_id:
                stmt = stmt.where(RebateAgreement.party_id == distributor_id)
            if status:
                stmt = stmt.where(RebateAgreement.status == status)
            
            agreements = (await session.execute(stmt)).scalars().all()
            return [await self._build_rebate_agreement_response(session, agreement) for agreement in agreements]
    
    async def get_rebate_agreement(self, agreement_id: int) -> Optional[RebateAgreementRead]:
        """Get a specific rebate agreement by ID."""
        async with get_async_session() as session:
            agreement = await session.get(RebateAgreement, agreement_id)
            if not agreement:
                return None
            return await self._build_rebate_agreement_response(session, agreement)
    
    async def update_rebate_agreement(self, agreement_id: int, data: RebateAgreementCreate) -> Optional[RebateAgreementRead]:
        """Update an existing rebate agreement."""
        async with get_async_session() as session:
            agreement = await session.get(RebateAgreement, agreement_id)
            if not agreement:
                return None
            
            # Validate input
            if not data.products and not data.product_category_ids:
                raise ValueError("At least one product or product category must be specified")
            
            if data.start_date >= data.end_date:
                raise ValueError("Start date must be before end date")
            
            # Validate tier ranges if provided
            if data.tiers:
                self._validate_tier_ranges(data.tiers, data.basis)
            
            # Update agreement fields
            agreement_data = data.dict()
            products = agreement_data.pop('products', [])
            product_category_ids = agreement_data.pop('product_category_ids', [])
            tiers = agreement_data.pop('tiers', [])
            
            for key, value in agreement_data.items():
                setattr(agreement, key, value)
            
            # Clear existing associations and tiers
            await session.execute(
                text("DELETE FROM rebate_agreement_products WHERE rebate_agreement_id = :id"),
                {"id": agreement_id}
            )
            await session.execute(
                text("DELETE FROM rebate_tiers WHERE rebate_agreement_id = :id"),
                {"id": agreement_id}
            )
            
            # Create new product associations
            for product_id in products:
                product_assoc = RebateAgreementProduct(
                    rebate_agreement_id=agreement.id,
                    product_id=product_id
                )
                session.add(product_assoc)
            
            # Create new category associations
            for category_id in product_category_ids:
                category_assoc = RebateAgreementProduct(
                    rebate_agreement_id=agreement.id,
                    category_id=category_id
                )
                session.add(category_assoc)
            
            # Create new tiers with UUIDs and parent agreement UUID
            for tier_data in tiers:
                tier = self._create_tier_from_data(tier_data, agreement.id, agreement.uuid, data.basis)
                session.add(tier)
            
            await session.commit()
            await session.refresh(agreement)
            
            return await self._build_rebate_agreement_response(session, agreement)
    
    async def delete_rebate_agreement(self, agreement_id: int) -> bool:
        """Delete a rebate agreement."""
        async with get_async_session() as session:
            agreement = await session.get(RebateAgreement, agreement_id)
            if not agreement:
                return False
            await session.delete(agreement)
            await session.commit()
            return True
    
    def _validate_tier_ranges(self, tiers: List[RebateTierCreate], basis: str):
        """Validate that tier ranges don't overlap and are properly ordered."""
        if not tiers:
            return
        
        # Sort tiers by from_value
        sorted_tiers = sorted(tiers, key=lambda t: t.from_quantity or t.from_amount or 0)
        
        for i, tier in enumerate(sorted_tiers):
            # Check that from_value is less than to_value
            from_val = tier.from_quantity if basis == "quantity" else tier.from_amount
            to_val = tier.to_quantity if basis == "quantity" else tier.to_amount
            
            if from_val is not None and to_val is not None and from_val >= to_val:
                raise ValueError(f"Tier {i+1}: from_value must be less than to_value")
            
            # Check for overlaps with previous tier
            if i > 0:
                prev_tier = sorted_tiers[i-1]
                prev_to_val = prev_tier.to_quantity if basis == "quantity" else prev_tier.to_amount
                
                if prev_to_val is not None and from_val is not None and prev_to_val > from_val:
                    raise ValueError(f"Tier {i+1} overlaps with previous tier")
    
    def _create_tier_from_data(self, tier_data: RebateTierCreate, agreement_id: int, agreement_uuid: str, basis: str) -> RebateTier:
        """Create a RebateTier database object from tier data, including UUIDs."""
        tier_dict = tier_data.dict()
        tier_dict['uuid'] = str(uuid.uuid4())
        tier_dict['rebate_agreement_uuid'] = agreement_uuid
        # Map rebate_value and rebate_unit to database fields
        tier_dict['rebate_value'] = tier_dict.pop('rebate_value')
        tier_dict['rebate_unit'] = tier_dict.pop('rebate_unit')
        # Set the appropriate from/to fields based on basis
        if basis == "quantity":
            tier_dict['from_quantity'] = tier_dict.pop('from_quantity')
            tier_dict['to_quantity'] = tier_dict.pop('to_quantity')
            tier_dict['from_amount'] = None
            tier_dict['to_amount'] = None
        else:  # amount
            tier_dict['from_amount'] = tier_dict.pop('from_amount')
            tier_dict['to_amount'] = tier_dict.pop('to_amount')
            tier_dict['from_quantity'] = None
            tier_dict['to_quantity'] = None
        tier_dict['rebate_agreement_id'] = agreement_id
        return RebateTier(**tier_dict)
    
    async def _check_overlapping_agreements(self, session, data: RebateAgreementCreate):
        """Check for overlapping agreements for the same distributor and products."""
        # This is a simplified check - in a real implementation, you might want more sophisticated logic
        stmt = select(RebateAgreement).where(
            RebateAgreement.party_id == data.distributor_id,
            RebateAgreement.agreement_type == data.agreement_type,
            RebateAgreement.status == "active"
        )
        
        existing_agreements = (await session.execute(stmt)).scalars().all()
        
        for existing in existing_agreements:
            # Check if date ranges overlap
            if (data.start_date <= existing.end_date and data.end_date >= existing.start_date):
                # Check if products overlap
                existing_products = [p.product_id for p in existing.products if p.product_id]
                existing_categories = [p.category_id for p in existing.products if p.category_id]
                
                if (set(data.products) & set(existing_products) or 
                    set(data.product_category_ids) & set(existing_categories)):
                    raise ValueError(f"Overlapping agreement found: {existing.description}")
    
    async def _build_rebate_agreement_response(self, session, agreement: RebateAgreement) -> RebateAgreementRead:
        """Build a complete RebateAgreementRead response with all related data."""
        # Get product IDs
        product_ids = []
        category_ids = []
        for product_assoc in agreement.products:
            if product_assoc.product_id:
                product_ids.append(product_assoc.product_id)
            if product_assoc.category_id:
                category_ids.append(product_assoc.category_id)
        
        # Build tier responses
        tiers = []
        for tier in agreement.tiers:
            tier_response = RebateTierRead(
                id=tier.id,
                uuid=tier.uuid,
                agreement_id=tier.rebate_agreement_id,
                rebate_agreement_uuid=tier.rebate_agreement_uuid,
                rebate_value=float(tier.rebate_value),
                rebate_unit=tier.rebate_unit,
                from_quantity=float(tier.from_quantity) if tier.from_quantity else None,
                to_quantity=float(tier.to_quantity) if tier.to_quantity else None,
                from_amount=float(tier.from_amount) if tier.from_amount else None,
                to_amount=float(tier.to_amount) if tier.to_amount else None,
            )
            tiers.append(tier_response)
        
        return RebateAgreementRead(
            id=agreement.id,
            agreement_type=agreement.agreement_type,
            distributor_id=agreement.party_id,  # Map party_id back to distributor_id
            description=agreement.description,
            start_date=agreement.start_date,
            end_date=agreement.end_date,
            calc_frequency=agreement.calc_frequency,
            basis=agreement.basis,
            rate_type=agreement.rate_type,
            approval_required=agreement.approval_required,
            products=product_ids,
            product_category_ids=category_ids,
            tiers=tiers,
            status=agreement.status
        )

class CTCQueryHelper:
    """Helper class for querying CTC categories."""
    
    async def get_all_classes(self) -> List[CTCCategory]:
        """Get all product classes (level 1)."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.level == 1)
            )
            return result.scalars().all()
    
    async def get_types_by_class(self, class_id: int) -> List[CTCCategory]:
        """Get all product types for a given class."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(
                    CTCCategory.level == 2,
                    CTCCategory.parent_id == class_id
                )
            )
            return result.scalars().all()
    
    async def get_types_by_class_uuid(self, class_uuid: str) -> List[CTCCategory]:
        """Get all product types for a given class using UUID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(
                    CTCCategory.level == 2,
                    CTCCategory.parent_uuid == class_uuid
                )
            )
            return result.scalars().all()
    
    async def get_categories_by_type(self, type_id: int) -> List[CTCCategory]:
        """Get all product categories for a given type."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(
                    CTCCategory.level == 3,
                    CTCCategory.parent_id == type_id
                )
            )
            return result.scalars().all()
    
    async def get_categories_by_type_uuid(self, type_uuid: str) -> List[CTCCategory]:
        """Get all product categories for a given type using UUID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(
                    CTCCategory.level == 3,
                    CTCCategory.parent_uuid == type_uuid
                )
            )
            return result.scalars().all()
    
    async def get_full_hierarchy(self, class_id: Optional[int] = None) -> List[CTCCategory]:
        """Get the full hierarchy for a class or all classes."""
        async with get_async_session() as session:
            if class_id:
                # Get specific class with its full hierarchy
                result = await session.execute(
                    select(CTCCategory)
                    .where(CTCCategory.id == class_id, CTCCategory.level == 1)
                    .options(
                        joinedload(CTCCategory.children).joinedload(CTCCategory.children)
                    )
                )
                return result.scalar_one_or_none()
            else:
                # Get all classes with their hierarchies
                result = await session.execute(
                    select(CTCCategory)
                    .where(CTCCategory.level == 1)
                    .options(
                        joinedload(CTCCategory.children).joinedload(CTCCategory.children)
                    )
                )
                return result.scalars().all()
    
    async def get_full_hierarchy_by_uuid(self, class_uuid: str) -> Optional[CTCCategory]:
        """Get the full hierarchy for a class using UUID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory)
                .where(CTCCategory.uuid == class_uuid, CTCCategory.level == 1)
                .options(
                    joinedload(CTCCategory.children).joinedload(CTCCategory.children)
                )
            )
            return result.scalar_one_or_none()
    
    async def get_category_path(self, category_id: int) -> Optional[List[CTCCategory]]:
        """Get the full path from root to a specific category."""
        async with get_async_session() as session:
            # Get the category
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.id == category_id)
            )
            category = result.scalar_one_or_none()
            
            if not category:
                return None
            
            path = [category]
            current = category
            
            # Walk up the hierarchy
            while current.parent_id:
                result = await session.execute(
                    select(CTCCategory).where(CTCCategory.id == current.parent_id)
                )
                current = result.scalar_one_or_none()
                if current:
                    path.insert(0, current)
                else:
                    break
            
            return path
    
    async def get_category_path_by_uuid(self, category_uuid: str) -> Optional[List[CTCCategory]]:
        """Get the full path from root to a specific category using UUID."""
        async with get_async_session() as session:
            # Get the category
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.uuid == category_uuid)
            )
            category = result.scalar_one_or_none()
            
            if not category:
                return None
            
            path = [category]
            current = category
            
            # Walk up the hierarchy using UUIDs
            while current.parent_uuid:
                result = await session.execute(
                    select(CTCCategory).where(CTCCategory.uuid == current.parent_uuid)
                )
                current = result.scalar_one_or_none()
                if current:
                    path.insert(0, current)
                else:
                    break
            
            return path
    
    async def search_categories(self, search_term: str, level: Optional[int] = None) -> List[CTCCategory]:
        """Search categories by name or code."""
        async with get_async_session() as session:
            query = select(CTCCategory).where(
                (CTCCategory.name.ilike(f'%{search_term}%')) |
                (CTCCategory.code.ilike(f'%{search_term}%'))
            )
            
            if level:
                query = query.where(CTCCategory.level == level)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_products_by_category(self, category_id: int) -> List[ProductModel]:
        """Get all products associated with a specific category."""
        async with get_async_session() as session:
            result = await session.execute(
                select(ProductModel)
                .join(CTCCategory, ProductModel.id == CTCCategory.product_id)
                .where(CTCCategory.id == category_id)
            )
            return result.scalars().all()
    
    async def get_products_by_category_uuid(self, category_uuid: str) -> List[ProductModel]:
        """Get all products associated with a specific category using UUID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(ProductModel)
                .join(CTCCategory, ProductModel.id == CTCCategory.product_id)
                .where(CTCCategory.uuid == category_uuid)
            )
            return result.scalars().all()
    
    async def get_categories_by_product(self, product_id: int) -> List[CTCCategory]:
        """Get all categories associated with a specific product."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.product_id == product_id)
            )
            return result.scalars().all()
    
    async def get_statistics(self) -> dict:
        """Get statistics about the CTC categories."""
        async with get_async_session() as session:
            stats = {}
            
            # Count by level
            for level in [1, 2, 3]:
                result = await session.execute(
                    select(CTCCategory).where(CTCCategory.level == level)
                )
                count = len(result.scalars().all())
                stats[f'level_{level}_count'] = count
            
            # Count active vs inactive
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.active == True)
            )
            active_count = len(result.scalars().all())
            
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.active == False)
            )
            inactive_count = len(result.scalars().all())
            
            stats['active_count'] = active_count
            stats['inactive_count'] = inactive_count
            
            # Count categories with products
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.product_id.isnot(None))
            )
            categories_with_products = len(result.scalars().all())
            stats['categories_with_products'] = categories_with_products
            
            return stats
    
    async def get_category_by_code(self, code: str) -> Optional[CTCCategory]:
        """Get a category by its code."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.code == code)
            )
            return result.scalar_one_or_none()
    
    async def get_category_by_id(self, category_id: int) -> Optional[CTCCategory]:
        """Get a category by its ID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.id == category_id)
            )
            return result.scalar_one_or_none()
    
    async def get_category_by_uuid(self, category_uuid: str) -> Optional[CTCCategory]:
        """Get a category by its UUID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.uuid == category_uuid)
            )
            return result.scalar_one_or_none()
    
    async def get_children(self, parent_id: int) -> List[CTCCategory]:
        """Get all direct children of a category."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.parent_id == parent_id)
            )
            return result.scalars().all()
    
    async def get_children_by_uuid(self, parent_uuid: str) -> List[CTCCategory]:
        """Get all direct children of a category using UUID."""
        async with get_async_session() as session:
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.parent_uuid == parent_uuid)
            )
            return result.scalars().all()
    
    async def get_parent(self, category_id: int) -> Optional[CTCCategory]:
        """Get the parent of a category."""
        async with get_async_session() as session:
            # First get the category to find its parent_id
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.id == category_id)
            )
            category = result.scalar_one_or_none()
            
            if not category or not category.parent_id:
                return None
            
            # Get the parent
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.id == category.parent_id)
            )
            return result.scalar_one_or_none()
    
    async def get_parent_by_uuid(self, category_uuid: str) -> Optional[CTCCategory]:
        """Get the parent of a category using UUID."""
        async with get_async_session() as session:
            # First get the category to find its parent_uuid
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.uuid == category_uuid)
            )
            category = result.scalar_one_or_none()
            
            if not category or not category.parent_uuid:
                return None
            
            # Get the parent
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.uuid == category.parent_uuid)
            )
            return result.scalar_one_or_none()
    
    async def get_siblings(self, category_id: int) -> List[CTCCategory]:
        """Get all siblings of a category (same parent)."""
        async with get_async_session() as session:
            # First get the category to find its parent_id
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.id == category_id)
            )
            category = result.scalar_one_or_none()
            
            if not category or not category.parent_id:
                return []
            
            # Get all siblings
            result = await session.execute(
                select(CTCCategory).where(
                    CTCCategory.parent_id == category.parent_id,
                    CTCCategory.id != category_id
                )
            )
            return result.scalars().all()
    
    async def get_siblings_by_uuid(self, category_uuid: str) -> List[CTCCategory]:
        """Get all siblings of a category using UUID."""
        async with get_async_session() as session:
            # First get the category to find its parent_uuid
            result = await session.execute(
                select(CTCCategory).where(CTCCategory.uuid == category_uuid)
            )
            category = result.scalar_one_or_none()
            
            if not category or not category.parent_uuid:
                return []
            
            # Get all siblings
            result = await session.execute(
                select(CTCCategory).where(
                    CTCCategory.parent_uuid == category.parent_uuid,
                    CTCCategory.uuid != category_uuid
                )
            )
            return result.scalars().all()

storage = SQLStorage()
