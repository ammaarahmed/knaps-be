import asyncio
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime
import uuid
import logging

from .database import get_async_session
from .db_models import (
    CTCClass, CTCType, CTCCategory, CTCAttributeGroup, CTCDataType, 
    CTCUnitOfMeasure, CTCAttribute, CategoryAttribute, ProductModel
)

logger = logging.getLogger(__name__)


def to_schema(obj, schema_cls):
    """Convert SQLAlchemy object to Pydantic schema"""
    if hasattr(schema_cls, "model_validate"):
        return schema_cls.model_validate(obj, from_attributes=True)
    return schema_cls.from_orm(obj)


class CTCStorage:
    """CRUD operations for CTC (Category, Type, Class) data"""
    
    # ==================== CTC Classes (Level 1) ====================
    
    async def get_all_classes(self, active_only: bool = True) -> List[CTCClass]:
        """Get all CTC classes"""
        async with get_async_session() as session:
            stmt = select(CTCClass)
            if active_only:
                stmt = stmt.where(CTCClass.active == True)
            stmt = stmt.order_by(CTCClass.name)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_class_by_id(self, class_id: int) -> Optional[CTCClass]:
        """Get CTC class by ID"""
        async with get_async_session() as session:
            stmt = select(CTCClass).where(CTCClass.id == class_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_class_by_uuid(self, class_uuid: str) -> Optional[CTCClass]:
        """Get CTC class by UUID"""
        async with get_async_session() as session:
            stmt = select(CTCClass).where(CTCClass.uuid == class_uuid)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_class_by_code(self, code: str) -> Optional[CTCClass]:
        """Get CTC class by code"""
        async with get_async_session() as session:
            stmt = select(CTCClass).where(CTCClass.code == code)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_class(self, data: Dict[str, Any]) -> CTCClass:
        """Create a new CTC class"""
        async with get_async_session() as session:
            class_data = data.copy()
            class_data['uuid'] = str(uuid.uuid4())
            class_data['created'] = datetime.utcnow()
            class_data['modified'] = datetime.utcnow()
            
            new_class = CTCClass(**class_data)
            session.add(new_class)
            await session.commit()
            await session.refresh(new_class)
            return new_class
    
    async def update_class(self, class_id: int, data: Dict[str, Any]) -> Optional[CTCClass]:
        """Update an existing CTC class"""
        async with get_async_session() as session:
            class_obj = await session.get(CTCClass, class_id)
            if not class_obj:
                return None
            
            # Update fields
            for key, value in data.items():
                if hasattr(class_obj, key):
                    setattr(class_obj, key, value)
            
            class_obj.modified = datetime.utcnow()
            await session.commit()
            await session.refresh(class_obj)
            return class_obj
    
    async def delete_class(self, class_id: int, soft_delete: bool = True) -> bool:
        """Delete a CTC class (soft delete by default)"""
        async with get_async_session() as session:
            class_obj = await session.get(CTCClass, class_id)
            if not class_obj:
                return False
            
            if soft_delete:
                class_obj.active = False
                class_obj.deleted = datetime.utcnow()
                class_obj.deleted_by = "system"  # TODO: Get from auth context
            else:
                await session.delete(class_obj)
            
            await session.commit()
            return True
    
    # ==================== CTC Types (Level 2) ====================
    
    async def get_types_by_class(self, class_id: int, active_only: bool = True) -> List[CTCType]:
        """Get all types for a specific class"""
        async with get_async_session() as session:
            stmt = select(CTCType).where(CTCType.class_id == class_id)
            if active_only:
                stmt = stmt.where(CTCType.active == True)
            stmt = stmt.order_by(CTCType.name)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_types_by_class_uuid(self, class_uuid: str, active_only: bool = True) -> List[CTCType]:
        """Get all types for a specific class by UUID"""
        async with get_async_session() as session:
            # First get the class by UUID
            class_stmt = select(CTCClass).where(CTCClass.uuid == class_uuid)
            class_result = await session.execute(class_stmt)
            class_obj = class_result.scalar_one_or_none()
            
            if not class_obj:
                return []
            
            # Then get types for that class
            stmt = select(CTCType).where(CTCType.class_id == class_obj.id)
            if active_only:
                stmt = stmt.where(CTCType.active == True)
            stmt = stmt.order_by(CTCType.name)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_type_by_id(self, type_id: int) -> Optional[CTCType]:
        """Get CTC type by ID"""
        async with get_async_session() as session:
            stmt = select(CTCType).where(CTCType.id == type_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_type_by_uuid(self, type_uuid: str) -> Optional[CTCType]:
        """Get CTC type by UUID"""
        async with get_async_session() as session:
            stmt = select(CTCType).where(CTCType.uuid == type_uuid)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_type(self, data: Dict[str, Any]) -> CTCType:
        """Create a new CTC type"""
        async with get_async_session() as session:
            type_data = data.copy()
            type_data['uuid'] = str(uuid.uuid4())
            type_data['created'] = datetime.utcnow()
            type_data['modified'] = datetime.utcnow()
            
            new_type = CTCType(**type_data)
            session.add(new_type)
            await session.commit()
            await session.refresh(new_type)
            return new_type
    
    async def update_type(self, type_id: int, data: Dict[str, Any]) -> Optional[CTCType]:
        """Update an existing CTC type"""
        async with get_async_session() as session:
            type_obj = await session.get(CTCType, type_id)
            if not type_obj:
                return None
            
            for key, value in data.items():
                if hasattr(type_obj, key):
                    setattr(type_obj, key, value)
            
            type_obj.modified = datetime.utcnow()
            await session.commit()
            await session.refresh(type_obj)
            return type_obj
    
    async def delete_type(self, type_id: int, soft_delete: bool = True) -> bool:
        """Delete a CTC type"""
        async with get_async_session() as session:
            type_obj = await session.get(CTCType, type_id)
            if not type_obj:
                return False
            
            if soft_delete:
                type_obj.active = False
                type_obj.deleted = datetime.utcnow()
                type_obj.deleted_by = "system"
            else:
                await session.delete(type_obj)
            
            await session.commit()
            return True
    
    # ==================== CTC Categories (Level 3) ====================
    
    async def get_categories_by_type(self, type_id: int, active_only: bool = True) -> List[CTCCategory]:
        """Get all categories for a specific type"""
        async with get_async_session() as session:
            stmt = select(CTCCategory).where(CTCCategory.type_id == type_id)
            if active_only:
                stmt = stmt.where(CTCCategory.active == True)
            stmt = stmt.order_by(CTCCategory.name)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_categories_by_type_uuid(self, type_uuid: str, active_only: bool = True) -> List[CTCCategory]:
        """Get all categories for a specific type by UUID"""
        async with get_async_session() as session:
            # First get the type by UUID
            type_stmt = select(CTCType).where(CTCType.uuid == type_uuid)
            type_result = await session.execute(type_stmt)
            type_obj = type_result.scalar_one_or_none()
            
            if not type_obj:
                return []
            
            # Then get categories for that type
            stmt = select(CTCCategory).where(CTCCategory.type_id == type_obj.id)
            if active_only:
                stmt = stmt.where(CTCCategory.active == True)
            stmt = stmt.order_by(CTCCategory.name)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_category_by_id(self, category_id: int) -> Optional[CTCCategory]:
        """Get CTC category by ID"""
        async with get_async_session() as session:
            stmt = select(CTCCategory).where(CTCCategory.id == category_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_category_by_uuid(self, category_uuid: str) -> Optional[CTCCategory]:
        """Get CTC category by UUID"""
        async with get_async_session() as session:
            stmt = select(CTCCategory).where(CTCCategory.uuid == category_uuid)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_category_by_code(self, code: str) -> Optional[CTCCategory]:
        """Get CTC category by code"""
        async with get_async_session() as session:
            stmt = select(CTCCategory).where(CTCCategory.code == code)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_category(self, data: Dict[str, Any]) -> CTCCategory:
        """Create a new CTC category"""
        async with get_async_session() as session:
            category_data = data.copy()
            category_data['uuid'] = str(uuid.uuid4())
            category_data['created'] = datetime.utcnow()
            category_data['modified'] = datetime.utcnow()
            
            new_category = CTCCategory(**category_data)
            session.add(new_category)
            await session.commit()
            await session.refresh(new_category)
            return new_category
    
    async def update_category(self, category_id: int, data: Dict[str, Any]) -> Optional[CTCCategory]:
        """Update an existing CTC category"""
        async with get_async_session() as session:
            category_obj = await session.get(CTCCategory, category_id)
            if not category_obj:
                return None
            
            for key, value in data.items():
                if hasattr(category_obj, key):
                    setattr(category_obj, key, value)
            
            category_obj.modified = datetime.utcnow()
            await session.commit()
            await session.refresh(category_obj)
            return category_obj
    
    async def delete_category(self, category_id: int, soft_delete: bool = True) -> bool:
        """Delete a CTC category"""
        async with get_async_session() as session:
            category_obj = await session.get(CTCCategory, category_id)
            if not category_obj:
                return False
            
            if soft_delete:
                category_obj.active = False
                category_obj.deleted = datetime.utcnow()
                category_obj.deleted_by = "system"
            else:
                await session.delete(category_obj)
            
            await session.commit()
            return True
    
    # ==================== CTC Attributes ====================
    
    async def get_attributes_by_category(self, category_id: int, active_only: bool = True) -> List[CTCAttribute]:
        """Get all attributes for a specific category"""
        async with get_async_session() as session:
            stmt = select(CTCAttribute).where(CTCAttribute.category_id == category_id)
            if active_only:
                stmt = stmt.where(CTCAttribute.active == True)
            stmt = stmt.order_by(CTCAttribute.rank, CTCAttribute.name)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_attribute_by_id(self, attribute_id: int) -> Optional[CTCAttribute]:
        """Get CTC attribute by ID"""
        async with get_async_session() as session:
            stmt = select(CTCAttribute).where(CTCAttribute.id == attribute_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_attribute_by_uuid(self, attribute_uuid: str) -> Optional[CTCAttribute]:
        """Get CTC attribute by UUID"""
        async with get_async_session() as session:
            stmt = select(CTCAttribute).where(CTCAttribute.uuid == attribute_uuid)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_attribute(self, data: Dict[str, Any]) -> CTCAttribute:
        """Create a new CTC attribute"""
        async with get_async_session() as session:
            attribute_data = data.copy()
            attribute_data['uuid'] = str(uuid.uuid4())
            attribute_data['created'] = datetime.utcnow()
            attribute_data['modified'] = datetime.utcnow()
            
            new_attribute = CTCAttribute(**attribute_data)
            session.add(new_attribute)
            await session.commit()
            await session.refresh(new_attribute)
            return new_attribute
    
    async def update_attribute(self, attribute_id: int, data: Dict[str, Any]) -> Optional[CTCAttribute]:
        """Update an existing CTC attribute"""
        async with get_async_session() as session:
            attribute_obj = await session.get(CTCAttribute, attribute_id)
            if not attribute_obj:
                return None
            
            for key, value in data.items():
                if hasattr(attribute_obj, key):
                    setattr(attribute_obj, key, value)
            
            attribute_obj.modified = datetime.utcnow()
            await session.commit()
            await session.refresh(attribute_obj)
            return attribute_obj
    
    async def delete_attribute(self, attribute_id: int, soft_delete: bool = True) -> bool:
        """Delete a CTC attribute"""
        async with get_async_session() as session:
            attribute_obj = await session.get(CTCAttribute, attribute_id)
            if not attribute_obj:
                return False
            
            if soft_delete:
                attribute_obj.active = False
                attribute_obj.deleted = datetime.utcnow()
                attribute_obj.deleted_by = "system"
            else:
                await session.delete(attribute_obj)
            
            await session.commit()
            return True
    
    # ==================== CTC Attribute Groups ====================
    
    async def get_all_attribute_groups(self, active_only: bool = True) -> List[CTCAttributeGroup]:
        """Get all attribute groups"""
        async with get_async_session() as session:
            stmt = select(CTCAttributeGroup)
            if active_only:
                stmt = stmt.where(CTCAttributeGroup.active == True)
            stmt = stmt.order_by(CTCAttributeGroup.name)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_attribute_group_by_id(self, group_id: int) -> Optional[CTCAttributeGroup]:
        """Get attribute group by ID"""
        async with get_async_session() as session:
            stmt = select(CTCAttributeGroup).where(CTCAttributeGroup.id == group_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_attribute_group(self, data: Dict[str, Any]) -> CTCAttributeGroup:
        """Create a new attribute group"""
        async with get_async_session() as session:
            group_data = data.copy()
            group_data['uuid'] = str(uuid.uuid4())
            group_data['created'] = datetime.utcnow()
            group_data['modified'] = datetime.utcnow()
            
            new_group = CTCAttributeGroup(**group_data)
            session.add(new_group)
            await session.commit()
            await session.refresh(new_group)
            return new_group
    
    # ==================== CTC Data Types ====================
    
    async def get_all_data_types(self, active_only: bool = True) -> List[CTCDataType]:
        """Get all data types"""
        async with get_async_session() as session:
            stmt = select(CTCDataType)
            if active_only:
                stmt = stmt.where(CTCDataType.active == True)
            stmt = stmt.order_by(CTCDataType.name)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_data_type_by_id(self, data_type_id: int) -> Optional[CTCDataType]:
        """Get data type by ID"""
        async with get_async_session() as session:
            stmt = select(CTCDataType).where(CTCDataType.id == data_type_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_data_type(self, data: Dict[str, Any]) -> CTCDataType:
        """Create a new data type"""
        async with get_async_session() as session:
            data_type_data = data.copy()
            data_type_data['uuid'] = str(uuid.uuid4())
            data_type_data['created'] = datetime.utcnow()
            data_type_data['modified'] = datetime.utcnow()
            
            new_data_type = CTCDataType(**data_type_data)
            session.add(new_data_type)
            await session.commit()
            await session.refresh(new_data_type)
            return new_data_type
    
    # ==================== CTC Units of Measure ====================
    
    async def get_all_units_of_measure(self, active_only: bool = True) -> List[CTCUnitOfMeasure]:
        """Get all units of measure"""
        async with get_async_session() as session:
            stmt = select(CTCUnitOfMeasure)
            if active_only:
                stmt = stmt.where(CTCUnitOfMeasure.active == True)
            stmt = stmt.order_by(CTCUnitOfMeasure.name)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_unit_of_measure_by_id(self, uom_id: int) -> Optional[CTCUnitOfMeasure]:
        """Get unit of measure by ID"""
        async with get_async_session() as session:
            stmt = select(CTCUnitOfMeasure).where(CTCUnitOfMeasure.id == uom_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_unit_of_measure(self, data: Dict[str, Any]) -> CTCUnitOfMeasure:
        """Create a new unit of measure"""
        async with get_async_session() as session:
            uom_data = data.copy()
            uom_data['uuid'] = str(uuid.uuid4())
            uom_data['created'] = datetime.utcnow()
            uom_data['modified'] = datetime.utcnow()
            
            new_uom = CTCUnitOfMeasure(**uom_data)
            session.add(new_uom)
            await session.commit()
            await session.refresh(new_uom)
            return new_uom
    
    # ==================== Advanced Queries ====================
    
    async def get_full_hierarchy(self, class_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get the full CTC hierarchy with all levels"""
        async with get_async_session() as session:
            if class_id:
                # Get specific class with its types and categories
                stmt = (
                    select(CTCClass)
                    .options(
                        selectinload(CTCClass.types).selectinload(CTCType.categories)
                    )
                    .where(CTCClass.id == class_id)
                )
            else:
                # Get all classes with their types and categories
                stmt = (
                    select(CTCClass)
                    .options(
                        selectinload(CTCClass.types).selectinload(CTCType.categories)
                    )
                    .order_by(CTCClass.name)
                )
            
            result = await session.execute(stmt)
            classes = result.scalars().all()
            
            hierarchy = []
            for class_obj in classes:
                class_data = {
                    'id': class_obj.id,
                    'uuid': class_obj.uuid,
                    'code': class_obj.code,
                    'name': class_obj.name,
                    'active': class_obj.active,
                    'types': []
                }
                
                for type_obj in class_obj.types:
                    type_data = {
                        'id': type_obj.id,
                        'uuid': type_obj.uuid,
                        'code': type_obj.code,
                        'name': type_obj.name,
                        'active': type_obj.active,
                        'categories': []
                    }
                    
                    for category_obj in type_obj.categories:
                        category_data = {
                            'id': category_obj.id,
                            'uuid': category_obj.uuid,
                            'code': category_obj.code,
                            'name': category_obj.name,
                            'active': category_obj.active,
                            'product_id': category_obj.product_id
                        }
                        type_data['categories'].append(category_data)
                    
                    class_data['types'].append(type_data)
                
                hierarchy.append(class_data)
            
            return hierarchy
    
    async def search_ctc(self, search_term: str, level: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search CTC data across all levels"""
        async with get_async_session() as session:
            search_pattern = f"%{search_term.lower()}%"
            results = []
            
            # Search classes
            if level is None or level == 1:
                stmt = (
                    select(CTCClass)
                    .where(
                        or_(
                            CTCClass.name.ilike(search_pattern),
                            CTCClass.code.ilike(search_pattern)
                        )
                    )
                    .order_by(CTCClass.name)
                )
                class_results = await session.execute(stmt)
                for class_obj in class_results.scalars().all():
                    results.append({
                        'level': 1,
                        'type': 'class',
                        'id': class_obj.id,
                        'uuid': class_obj.uuid,
                        'code': class_obj.code,
                        'name': class_obj.name,
                        'active': class_obj.active
                    })
            
            # Search types
            if level is None or level == 2:
                stmt = (
                    select(CTCType)
                    .where(
                        or_(
                            CTCType.name.ilike(search_pattern),
                            CTCType.code.ilike(search_pattern)
                        )
                    )
                    .order_by(CTCType.name)
                )
                type_results = await session.execute(stmt)
                for type_obj in type_results.scalars().all():
                    results.append({
                        'level': 2,
                        'type': 'type',
                        'id': type_obj.id,
                        'uuid': type_obj.uuid,
                        'code': type_obj.code,
                        'name': type_obj.name,
                        'active': type_obj.active,
                        'class_id': type_obj.class_id
                    })
            
            # Search categories
            if level is None or level == 3:
                stmt = (
                    select(CTCCategory)
                    .where(
                        or_(
                            CTCCategory.name.ilike(search_pattern),
                            CTCCategory.code.ilike(search_pattern)
                        )
                    )
                    .order_by(CTCCategory.name)
                )
                category_results = await session.execute(stmt)
                for category_obj in category_results.scalars().all():
                    results.append({
                        'level': 3,
                        'type': 'category',
                        'id': category_obj.id,
                        'uuid': category_obj.uuid,
                        'code': category_obj.code,
                        'name': category_obj.name,
                        'active': category_obj.active,
                        'type_id': category_obj.type_id,
                        'product_id': category_obj.product_id
                    })
            
            return results
    
    async def get_category_with_attributes(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get a category with all its attributes and related data"""
        async with get_async_session() as session:
            stmt = (
                select(CTCCategory)
                .options(
                    selectinload(CTCCategory.ctc_attributes).selectinload(CTCAttribute.attribute_group),
                    selectinload(CTCCategory.ctc_attributes).selectinload(CTCAttribute.data_type),
                    selectinload(CTCCategory.ctc_attributes).selectinload(CTCAttribute.uom),
                    selectinload(CTCCategory.attributes)
                )
                .where(CTCCategory.id == category_id)
            )
            
            result = await session.execute(stmt)
            category = result.scalar_one_or_none()
            
            if not category:
                return None
            
            # Build the response
            category_data = {
                'id': category.id,
                'uuid': category.uuid,
                'code': category.code,
                'name': category.name,
                'active': category.active,
                'type_id': category.type_id,
                'product_id': category.product_id,
                'ctc_attributes': [],
                'simple_attributes': []
            }
            
            # Add CTC attributes
            for attr in category.ctc_attributes:
                attr_data = {
                    'id': attr.id,
                    'uuid': attr.uuid,
                    'name': attr.name,
                    'rank': attr.rank,
                    'as_filter': attr.as_filter,
                    'active': attr.active,
                    'attribute_group': {
                        'id': attr.attribute_group.id,
                        'name': attr.attribute_group.name,
                        'code': attr.attribute_group.code
                    },
                    'data_type': {
                        'id': attr.data_type.id,
                        'name': attr.data_type.name,
                        'code': attr.data_type.code
                    }
                }
                
                if attr.uom:
                    attr_data['unit_of_measure'] = {
                        'id': attr.uom.id,
                        'name': attr.uom.name,
                        'code': attr.uom.code
                    }
                
                category_data['ctc_attributes'].append(attr_data)
            
            # Add simple attributes
            for attr in category.attributes:
                category_data['simple_attributes'].append({
                    'id': attr.id,
                    'name': attr.name,
                    'value': attr.value
                })
            
            return category_data
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get CTC statistics"""
        async with get_async_session() as session:
            # Count classes
            class_count = await session.scalar(select(func.count(CTCClass.id)))
            active_class_count = await session.scalar(
                select(func.count(CTCClass.id)).where(CTCClass.active == True)
            )
            
            # Count types
            type_count = await session.scalar(select(func.count(CTCType.id)))
            active_type_count = await session.scalar(
                select(func.count(CTCType.id)).where(CTCType.active == True)
            )
            
            # Count categories
            category_count = await session.scalar(select(func.count(CTCCategory.id)))
            active_category_count = await session.scalar(
                select(func.count(CTCCategory.id)).where(CTCCategory.active == True)
            )
            
            # Count attributes
            attribute_count = await session.scalar(select(func.count(CTCAttribute.id)))
            active_attribute_count = await session.scalar(
                select(func.count(CTCAttribute.id)).where(CTCAttribute.active == True)
            )
            
            # Count categories with products
            categories_with_products = await session.scalar(
                select(func.count(CTCCategory.id)).where(CTCCategory.product_id.isnot(None))
            )
            
            return {
                'classes': {
                    'total': class_count,
                    'active': active_class_count
                },
                'types': {
                    'total': type_count,
                    'active': active_type_count
                },
                'categories': {
                    'total': category_count,
                    'active': active_category_count,
                    'with_products': categories_with_products
                },
                'attributes': {
                    'total': attribute_count,
                    'active': active_attribute_count
                }
            }
    
    # ==================== Product-Category Relationships ====================
    
    async def assign_product_to_category(self, category_id: int, product_id: int) -> bool:
        """Assign a product to a category"""
        async with get_async_session() as session:
            category = await session.get(CTCCategory, category_id)
            if not category:
                return False
            
            product = await session.get(ProductModel, product_id)
            if not product:
                return False
            
            category.product_id = product_id
            category.modified = datetime.utcnow()
            category.modified_by = "system"  # TODO: Get from auth context
            
            await session.commit()
            return True
    
    async def remove_product_from_category(self, category_id: int) -> bool:
        """Remove product assignment from a category"""
        async with get_async_session() as session:
            category = await session.get(CTCCategory, category_id)
            if not category:
                return False
            
            category.product_id = None
            category.modified = datetime.utcnow()
            category.modified_by = "system"
            
            await session.commit()
            return True
    
    async def get_products_by_category(self, category_id: int) -> List[ProductModel]:
        """Get all products assigned to a category"""
        async with get_async_session() as session:
            stmt = (
                select(ProductModel)
                .join(CTCCategory, ProductModel.id == CTCCategory.product_id)
                .where(CTCCategory.id == category_id)
            )
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_categories_by_product(self, product_id: int) -> List[CTCCategory]:
        """Get all categories assigned to a product"""
        async with get_async_session() as session:
            stmt = (
                select(CTCCategory)
                .where(CTCCategory.product_id == product_id)
            )
            
            result = await session.execute(stmt)
            return result.scalars().all() 