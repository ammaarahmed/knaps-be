import asyncio
from typing import List, Optional, Literal, Dict, Any, Union, Tuple
from sqlalchemy import select, text, and_, or_, func, desc, asc
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime
from .database import get_async_session
from .db_models import (
    ProductModel, User, PriceLevel, RebateAgreement, RebateAgreementProduct, 
    RebateTier, RebateClaim,
    # New CTC models
    CTCClass, CTCType, CTCCategory, CTCAttributeGroup, CTCDataType, 
    CTCUnitOfMeasure, CTCAttribute, CategoryAttribute,
    # Distributor and Brand models
    Distributor, Brand
)
from .models import (
    Product,
    InsertProduct,
    ProductAnalytics,
    OverallAnalytics,
    RebateAgreementCreate,
    RebateAgreementRead,
    RebateTierCreate,
    DistributorCreate,
    DistributorRead,
    DistributorUpdate,
    BrandCreate,
    BrandRead,
    BrandUpdate,
    ProductCreateResult,
    FuzzyMatchInfo,
    BulkProductCreateResult,
)
import logging 
import uuid
import json
import pandas as pd
from decimal import Decimal
from difflib import SequenceMatcher
import re

logger = logging.getLogger('uvicorn.error')

def to_schema(self, obj, schema):
        return schema(**obj.model_dump())

def normalize_name(name: str) -> str:
    """Normalize a name for comparison by removing extra spaces and converting to lowercase"""
    if not name:
        return ""
    # Remove extra whitespace and convert to lowercase
    return re.sub(r'\s+', ' ', name.strip().lower())


def calculate_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two names using SequenceMatcher"""
    if not name1 or not name2:
        return 0.0
    
    # Normalize both names
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    # Use SequenceMatcher for similarity calculation
    return SequenceMatcher(None, norm1, norm2).ratio()


def find_best_match(input_name: str, candidates: List[Tuple[str, Any]], threshold: float = 0.8) -> Tuple[Optional[Any], float, List[str]]:
    """
    Find the best match for an input name among candidates.
    
    Args:
        input_name: The name to match
        candidates: List of tuples (name, object) to search through
        threshold: Minimum similarity score to consider a match (0.0 to 1.0)
    
    Returns:
        Tuple of (best_match_object, similarity_score, suggestions)
    """
    if not candidates:
        return None, 0.0, []
    
    # Calculate similarity for all candidates
    similarities = []
    for candidate_name, candidate_obj in candidates:
        similarity = calculate_similarity(input_name, candidate_name)
        similarities.append((similarity, candidate_name, candidate_obj))
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[0], reverse=True)
    
    best_similarity, best_name, best_obj = similarities[0]
    
    # If best match is above threshold, return it
    if best_similarity >= threshold:
        # Generate suggestions (other close matches)
        suggestions = [name for sim, name, _ in similarities[1:4] if sim >= 0.6]
        return best_obj, best_similarity, suggestions
    
    # If no good match, return suggestions
    suggestions = [name for sim, name, _ in similarities[:3] if sim >= 0.3]
    return None, best_similarity, suggestions





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

    async def get_brand_by_name(self, name: str) -> Optional[BrandRead]:
        """Find brand by exact name match (case-insensitive)"""
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.name.ilike(name))
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, BrandRead) if row else None

    async def get_distributor_by_name(self, name: str) -> Optional[DistributorRead]:
        """Find distributor by exact name match (case-insensitive)"""
        async with get_async_session() as session:
            stmt = select(Distributor).where(Distributor.name.ilike(name))
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DistributorRead) if row else None

    async def find_brand_with_fuzzy_matching(self, brand_name: str, threshold: float = 0.8) -> Tuple[Optional[BrandRead], float, List[str]]:
        """
        Find brand using fuzzy matching with suggestions.
        
        Returns:
            Tuple of (brand_object, similarity_score, suggestions)
        """
        async with get_async_session() as session:
            # Get all brands
            stmt = select(Brand)
            result = await session.execute(stmt)
            brands = result.scalars().all()
            
            # Convert to list of (name, brand_object) tuples
            candidates = [(brand.name, brand) for brand in brands]
            
            # Find best match
            best_match, similarity, suggestions = find_best_match(brand_name, candidates, threshold)
            
            if best_match:
                return to_schema(best_match, BrandRead), similarity, suggestions
            else:
                return None, similarity, suggestions

    async def find_distributor_with_fuzzy_matching(self, distributor_name: str, threshold: float = 0.8) -> Tuple[Optional[DistributorRead], float, List[str]]:
        """
        Find distributor using fuzzy matching with suggestions.
        
        Returns:
            Tuple of (distributor_object, similarity_score, suggestions)
        """
        async with get_async_session() as session:
            # Get all distributors
            stmt = select(Distributor)
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            
            # Convert to list of (name, distributor_object) tuples
            candidates = [(distributor.name, distributor) for distributor in distributors]
            
            # Find best match
            best_match, similarity, suggestions = find_best_match(distributor_name, candidates, threshold)
            
            if best_match:
                return to_schema(best_match, DistributorRead), similarity, suggestions
            else:
                return None, similarity, suggestions

    async def get_brand_by_name(self, name: str) -> Optional[BrandRead]:
        """Find brand by exact name match (case-insensitive)"""
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.name.ilike(name))
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, BrandRead) if row else None

    async def get_distributor_by_name(self, name: str) -> Optional[DistributorRead]:
        """Find distributor by exact name match (case-insensitive)"""
        async with get_async_session() as session:
            stmt = select(Distributor).where(Distributor.name.ilike(name))
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DistributorRead) if row else None

    async def find_brand_with_fuzzy_matching(self, brand_name: str, threshold: float = 0.8) -> Tuple[Optional[BrandRead], float, List[str]]:
        """
        Find brand using fuzzy matching with suggestions.
        
        Returns:
            Tuple of (brand_object, similarity_score, suggestions)
        """
        async with get_async_session() as session:
            # Get all brands
            stmt = select(Brand)
            result = await session.execute(stmt)
            brands = result.scalars().all()
            
            # Convert to list of (name, brand_object) tuples
            candidates = [(brand.name, brand) for brand in brands]
            
            # Find best match
            best_match, similarity, suggestions = find_best_match(brand_name, candidates, threshold)
            
            if best_match:
                return to_schema(best_match, BrandRead), similarity, suggestions
            else:
                return None, similarity, suggestions

    async def find_distributor_with_fuzzy_matching(self, distributor_name: str, threshold: float = 0.8) -> Tuple[Optional[DistributorRead], float, List[str]]:
        """
        Find distributor using fuzzy matching with suggestions.
        
        Returns:
            Tuple of (distributor_object, similarity_score, suggestions)
        """
        async with get_async_session() as session:
            # Get all distributors
            stmt = select(Distributor)
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            
            # Convert to list of (name, distributor_object) tuples
            candidates = [(distributor.name, distributor) for distributor in distributors]
            
            # Find best match
            best_match, similarity, suggestions = find_best_match(distributor_name, candidates, threshold)
            
            if best_match:
                return to_schema(best_match, DistributorRead), similarity, suggestions
            else:
                return None, similarity, suggestions

    async def create_product(self, data: InsertProduct) -> ProductCreateResult:
        fuzzy_matches = []
        async with get_async_session() as session:
            # Distributor matching
            stmt = select(Distributor)
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            distributor = None
            normalized_input = normalize_name(data.distributor_name)
            for d in distributors:
                if normalize_name(d.name) == normalized_input:
                    distributor = d
                    break
            if not distributor:
                # Fuzzy match
                candidates = [(d.name, d) for d in distributors]
                best, sim, _ = find_best_match(data.distributor_name, candidates, 0.8)
                if best:
                    logger.warning(f"Fuzzy match for distributor: '{data.distributor_name}' -> '{best.name}' (sim={sim:.2f})")
                    distributor = best
                    fuzzy_matches.append(FuzzyMatchInfo(
                        is_fuzzy=True, field='distributor',
                        input_value=data.distributor_name,
                        matched_value=best.name, similarity=sim
                    ))
                else:
                    return ProductCreateResult(product=None, fuzzy_matches=[], error=f"Distributor '{data.distributor_name}' not found")

            # Brand matching
            stmt = select(Brand)
            result = await session.execute(stmt)
            brands = result.scalars().all()
            brand = None
            normalized_input = normalize_name(data.brand_name)
            for b in brands:
                if normalize_name(b.name) == normalized_input:
                    brand = b
                    break
            if not brand:
                candidates = [(b.name, b) for b in brands]
                best, sim, _ = find_best_match(data.brand_name, candidates, 0.8)
                if best:
                    logger.warning(f"Fuzzy match for brand: '{data.brand_name}' -> '{best.name}' (sim={sim:.2f})")
                    brand = best
                    fuzzy_matches.append(FuzzyMatchInfo(
                        is_fuzzy=True, field='brand',
                        input_value=data.brand_name,
                        matched_value=best.name, similarity=sim
                    ))
                else:
                    return ProductCreateResult(product=None, fuzzy_matches=fuzzy_matches, error=f"Brand '{data.brand_name}' not found")

            # Verify brand belongs to distributor
            if brand.distributor_id != distributor.id:
                return ProductCreateResult(product=None, fuzzy_matches=fuzzy_matches, error=f"Brand '{data.brand_name}' does not belong to distributor '{data.distributor_name}'")

            product_data = data.model_dump()
            price_levels_data = product_data.pop('price_levels', [])
            product_data['uuid'] = str(uuid.uuid4())
            product_data['distributor_id'] = distributor.id
            product_data['brand_id'] = brand.id
            product_data.pop('distributor_name', None)
            product_data.pop('brand_name', None)
            obj = ProductModel(**product_data)
            session.add(obj)
            await session.flush()
            for price_level_data in price_levels_data:
                price_level = PriceLevel(product_id=obj.id, **price_level_data)
                session.add(price_level)
            await session.commit()
            await session.refresh(obj)
            return ProductCreateResult(product=to_schema(obj, Product), fuzzy_matches=fuzzy_matches)

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
    


    # Distributor operations
    async def get_distributors(self) -> List[DistributorRead]:
        async with get_async_session() as session:
            result = await session.execute(select(Distributor))
            return [to_schema(row, DistributorRead) for row in result.scalars().all()]

    async def get_distributor(self, distributor_id: int) -> Optional[DistributorRead]:
        async with get_async_session() as session:
            result = await session.get(Distributor, distributor_id)
            return to_schema(result, DistributorRead) if result else None

    async def get_distributor_by_uuid(self, uuid: str) -> Optional[DistributorRead]:
        async with get_async_session() as session:
            stmt = select(Distributor).where(Distributor.uuid == uuid)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DistributorRead) if row else None

    async def get_distributor_by_code(self, code: str) -> Optional[DistributorRead]:
        async with get_async_session() as session:
            stmt = select(Distributor).where(Distributor.code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, DistributorRead) if row else None

    async def create_distributor(self, data: DistributorCreate) -> DistributorRead:
        async with get_async_session() as session:
            distributor_data = data.model_dump()
            distributor_data['uuid'] = str(uuid.uuid4())
            distributor_data['modified'] = datetime.utcnow()
            distributor_data['created'] = datetime.utcnow()
            
            obj = Distributor(**distributor_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, DistributorRead)

    async def update_distributor(self, distributor_id: int, data: DistributorUpdate) -> Optional[DistributorRead]:
        async with get_async_session() as session:
            obj = await session.get(Distributor, distributor_id)
            if not obj:
                return None
            
            update_data = data.model_dump(exclude_unset=True)
            update_data['modified'] = datetime.utcnow()
            
            for k, v in update_data.items():
                setattr(obj, k, v)
            
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, DistributorRead)

    async def delete_distributor(self, distributor_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(Distributor, distributor_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    async def search_distributors(self, query: str) -> List[DistributorRead]:
        """Search distributors by name, code, or store"""
        q = f"%{query.lower()}%"
        async with get_async_session() as session:
            stmt = select(Distributor).where(
                (Distributor.name.ilike(q))
                | (Distributor.code.ilike(q))
                | (Distributor.store.ilike(q))
            )
            result = await session.execute(stmt)
            return [to_schema(row, DistributorRead) for row in result.scalars().all()]

    # Brand operations
    async def get_brands(self) -> List[BrandRead]:
        async with get_async_session() as session:
            result = await session.execute(select(Brand))
            return [to_schema(row, BrandRead) for row in result.scalars().all()]

    async def get_brand(self, brand_id: int) -> Optional[BrandRead]:
        async with get_async_session() as session:
            result = await session.get(Brand, brand_id)
            return to_schema(result, BrandRead) if result else None

    async def get_brand_by_uuid(self, uuid: str) -> Optional[BrandRead]:
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.uuid == uuid)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, BrandRead) if row else None

    async def get_brand_by_code(self, code: str) -> Optional[BrandRead]:
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.code == code)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return to_schema(row, BrandRead) if row else None

    async def get_brands_by_distributor(self, distributor_id: int) -> List[BrandRead]:
        async with get_async_session() as session:
            stmt = select(Brand).where(Brand.distributor_id == distributor_id)
            result = await session.execute(stmt)
            return [to_schema(row, BrandRead) for row in result.scalars().all()]

    async def create_brand(self, data: BrandCreate) -> BrandRead:
        async with get_async_session() as session:
            brand_data = data.model_dump()
            brand_data['uuid'] = str(uuid.uuid4())
            brand_data['modified'] = datetime.utcnow()
            brand_data['created'] = datetime.utcnow()
            
            obj = Brand(**brand_data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, BrandRead)

    async def update_brand(self, brand_id: int, data: BrandUpdate) -> Optional[BrandRead]:
        async with get_async_session() as session:
            obj = await session.get(Brand, brand_id)
            if not obj:
                return None
            
            update_data = data.model_dump(exclude_unset=True)
            update_data['modified'] = datetime.utcnow()
            
            for k, v in update_data.items():
                setattr(obj, k, v)
            
            await session.commit()
            await session.refresh(obj)
            return to_schema(obj, BrandRead)

    async def delete_brand(self, brand_id: int) -> bool:
        async with get_async_session() as session:
            obj = await session.get(Brand, brand_id)
            if not obj:
                return False
            await session.delete(obj)
            await session.commit()
            return True

    async def search_brands(self, query: str) -> List[BrandRead]:
        """Search brands by name, code, or store"""
        q = f"%{query.lower()}%"
        async with get_async_session() as session:
            stmt = select(Brand).where(
                (Brand.name.ilike(q))
                | (Brand.code.ilike(q))
                | (Brand.store.ilike(q))
            )
            result = await session.execute(stmt)
            return [to_schema(row, BrandRead) for row in result.scalars().all()]

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
            obj = User(**data.model_dump())
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
            agreement_data = data.model_dump()
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
            agreement_data = data.model_dump()
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
        tier_dict = tier_data.model_dump()
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

    async def bulk_create_products(self, products: List[InsertProduct]) -> BulkProductCreateResult:
        # Use pandas for fast filtering
        import numpy as np
        import pandas as pd
        df = pd.DataFrame([p.model_dump() for p in products])
        # Preload all brands and distributors
        async with get_async_session() as session:
            stmt = select(Distributor)
            result = await session.execute(stmt)
            distributors = result.scalars().all()
            stmt = select(Brand)
            result = await session.execute(stmt)
            brands = result.scalars().all()
        # Build lookup tables
        distributor_lookup = {normalize_name(d.name): d for d in distributors}
        brand_lookup = {normalize_name(b.name): b for b in brands}
        # Fast vectorized normalization
        df['normalized_distributor'] = df['distributor_name'].apply(normalize_name)
        df['normalized_brand'] = df['brand_name'].apply(normalize_name)
        # Find exact matches
        df['distributor_obj'] = df['normalized_distributor'].map(distributor_lookup)
        df['brand_obj'] = df['normalized_brand'].map(brand_lookup)
        created = []
        failed = []
        for idx, row in df.iterrows():
            data = InsertProduct(**{k: row[k] for k in InsertProduct.model_fields.keys() if k in row})
            fuzzy_matches = []
            distributor = row['distributor_obj']
            brand = row['brand_obj']
            # Fallback to fuzzy if not found
            if distributor is None:
                candidates = [(d.name, d) for d in distributors]
                best, sim, _ = find_best_match(row['distributor_name'], candidates, 0.8)
                if best:
                    logger.warning(f"Fuzzy match for distributor: '{row['distributor_name']}' -> '{best.name}' (sim={sim:.2f})")
                    distributor = best
                    fuzzy_matches.append(FuzzyMatchInfo(
                        is_fuzzy=True, field='distributor',
                        input_value=row['distributor_name'],
                        matched_value=best.name, similarity=sim
                    ))
                else:
                    failed.append(ProductCreateResult(product=None, fuzzy_matches=[], error=f"Distributor '{row['distributor_name']}' not found"))
                    continue
            if brand is None:
                candidates = [(b.name, b) for b in brands]
                best, sim, _ = find_best_match(row['brand_name'], candidates, 0.8)
                if best:
                    logger.warning(f"Fuzzy match for brand: '{row['brand_name']}' -> '{best.name}' (sim={sim:.2f})")
                    brand = best
                    fuzzy_matches.append(FuzzyMatchInfo(
                        is_fuzzy=True, field='brand',
                        input_value=row['brand_name'],
                        matched_value=best.name, similarity=sim
                    ))
                else:
                    failed.append(ProductCreateResult(product=None, fuzzy_matches=fuzzy_matches, error=f"Brand '{row['brand_name']}' not found"))
                    continue
            if brand.distributor_id != distributor.id:
                failed.append(ProductCreateResult(product=None, fuzzy_matches=fuzzy_matches, error=f"Brand '{row['brand_name']}' does not belong to distributor '{row['distributor_name']}'"))
                continue
            # Create product
            product_data = data.model_dump()
            price_levels_data = product_data.pop('price_levels', [])
            product_data['uuid'] = str(uuid.uuid4())
            product_data['distributor_id'] = distributor.id
            product_data['brand_id'] = brand.id
            product_data.pop('distributor_name', None)
            product_data.pop('brand_name', None)
            obj = ProductModel(**product_data)
            async with get_async_session() as session:
                session.add(obj)
                await session.flush()
                for price_level_data in price_levels_data:
                    price_level = PriceLevel(product_id=obj.id, **price_level_data)
                    session.add(price_level)
                await session.commit()
                await session.refresh(obj)
            created.append(ProductCreateResult(product=to_schema(obj, Product), fuzzy_matches=fuzzy_matches))
        return BulkProductCreateResult(created=created, failed=failed)


storage = SQLStorage()
