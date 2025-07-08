from pydantic import BaseModel, Field
from typing import Literal, Optional, Union, List, Dict
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID, uuid4


class ORMBase(BaseModel):
    model_config = {"from_attributes": True}

# Auth models
class Org(ORMBase):
    org_name: str
    org_id: int
    org_uuid: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

class Store(ORMBase):
    store_name: str
    store_id: int
    store_uuid: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    level: Optional[Literal['superadmin', 'admin', 'user']] = None
    org: Optional[Org] = None
    store: Optional[Store] = None
    created_at: datetime
    updated_at: datetime
    
class Token(ORMBase):
    access_token: str
    token_type: str

# Price Level models
class PriceLevel(ORMBase):
    id: Optional[int] = None
    price_level: str  # e.g., "MWP", "Trade", "GO", "RRP"
    type: str  # e.g., "Standard", "Promotional", "Bulk", etc.
    value_excl: Decimal  # Value excluding tax
    value_incl: Optional[Decimal] = None  # Value including tax
    comments: Optional[str] = None  # Additional comments about this price level
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class InsertPriceLevel(ORMBase):
    price_level: str
    type: str
    value_excl: Decimal
    value_incl: Optional[Decimal] = None
    comments: Optional[str] = None

# Product models
class InsertProduct(ORMBase):
    distributor_name: str
    brand_name: str
    product_code: str
    product_secondary_code: Optional[str] = None
    product_name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    shipping_class: Optional[str] = None
    category_name: str
    product_availability: str = 'In Stock'
    status: str = 'Active'
    online: bool = True
    superceded_by: Optional[str] = None
    ean: Optional[str] = None
    pack_size: int = 1
    price_levels: List[InsertPriceLevel] = []
    core_group: Optional[str] = None
    tax_exmt: bool = False
    hyperlink: Optional[str] = None
    web_title: Optional[str] = None
    features_and_benefits_codes: Optional[str] = None
    badges_codes: Optional[str] = None
    stock_unmanaged: bool = False

class Product(ORMBase):
    uuid: Optional[str] = None  # Optional UUID field for updates
    distributor_name: Optional[str] = None
    brand_name: Optional[str] = None
    product_code: Optional[str] = None
    product_secondary_code: Optional[str] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    shipping_class: Optional[str] = None
    category_name: Optional[str] = None
    product_availability: Optional[str] = None
    status: Optional[str] = None
    online: Optional[bool] = None
    superceded_by: Optional[str] = None
    ean: Optional[str] = None
    pack_size: Optional[int] = None
    price_levels: Optional[List[PriceLevel]] = None
    core_group: Optional[str] = None
    tax_exmt: Optional[bool] = None
    hyperlink: Optional[str] = None
    web_title: Optional[str] = None
    features_and_benefits_codes: Optional[str] = None
    badges_codes: Optional[str] = None
    stock_unmanaged: Optional[bool] = None

# Rebate models

class RebateTierCreate(ORMBase):
    rebate_agreement_uuid: Optional[str] = None
    from_quantity: Optional[float] = None
    to_quantity: Optional[float] = None  # None if open-ended
    from_amount: Optional[float] = None
    to_amount: Optional[float] = None  # None if open-ended
    rebate_value: float         # percentage or per-unit amount
    rebate_unit: Literal["percentage", "per_unit", "fixed"]

class RebateAgreementCreate(ORMBase):
    agreement_type: Literal["vendor", "customer"]
    distributor_id: int  # vendor ID or customer ID 
    description: str  # Changed from 'name' to match database schema
    start_date: date
    end_date: date
    calc_frequency: Literal["invoice", "daily", "monthly", "quarterly", "yearly"]  # Added 'daily', kept 'invoice'
    basis: Literal["quantity", "amount"] 
    rate_type: Literal["percentage", "per_unit", "fixed"]
    approval_required: bool = False
    products: List[int] = []           # product IDs this agreement applies to
    product_category_ids: List[int] = []  # alternatively or additionally, categories
    tiers: List[RebateTierCreate] = []  # tier definitions (if any)

class RebateTierRead(ORMBase):
    id: int
    uuid: str
    agreement_id: int
    rebate_agreement_uuid: str
    from_quantity: Optional[float] = None
    to_quantity: Optional[float] = None  # None if open-ended
    from_amount: Optional[float] = None
    to_amount: Optional[float] = None  # None if open-ended
    rebate_value: float         # percentage or per-unit amount
    rebate_unit: Literal["percentage", "per_unit", "fixed"]

class RebateAgreementRead(ORMBase):
    id: int
    uuid: str
    agreement_type: str 
    distributor_id: int 
    description: str  # Changed from 'name' to match database schema
    start_date: date 
    end_date: date 
    calc_frequency: str 
    basis: str 
    rate_type: str 
    approval_required: bool 
    products: List[int] 
    product_category_ids: List[int] 
    tiers: List[RebateTierRead] 
    status: str


# Analytics types
class ProductAnalytics(ORMBase):
    product_id: int
    product_name: str
    product_code: str
    brand_name: str
    turnover_rate: float
    total_revenue: Decimal
    current_stock: int

class OverallAnalytics(ORMBase):
    average_turnover_rate: float
    total_revenue: Decimal
    total_products: int
    active_products: int
    total_brands: int
    total_categories: int
    total_distributors: int

# Distributor models
class DistributorCreate(ORMBase):
    """Model for creating a new distributor"""
    code: str
    name: str
    store: str
    edi: bool = False
    auto_claim_over_charge: bool = False
    is_central: bool = True
    icon_owner: Optional[str] = None
    gln: Optional[str] = None
    business_number: Optional[str] = None
    accounting_date: Optional[int] = None
    web_portal_url: Optional[str] = None
    pp_claim_from: Optional[str] = None
    fis_minimum_order: Optional[str] = None
    default_extended_credits_code: Optional[str] = None
    default_extended_credits_name: Optional[str] = None
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"

class DistributorRead(ORMBase):
    """Model for reading distributor data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    edi: bool
    auto_claim_over_charge: bool
    is_central: bool
    icon_owner: Optional[str] = None
    gln: Optional[str] = None
    business_number: Optional[str] = None
    accounting_date: Optional[int] = None
    web_portal_url: Optional[str] = None
    pp_claim_from: Optional[str] = None
    fis_minimum_order: Optional[str] = None
    default_extended_credits_code: Optional[str] = None
    default_extended_credits_name: Optional[str] = None
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None

class DistributorUpdate(ORMBase):
    """Model for updating distributor data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    edi: Optional[bool] = None
    auto_claim_over_charge: Optional[bool] = None
    is_central: Optional[bool] = None
    icon_owner: Optional[str] = None
    gln: Optional[str] = None
    business_number: Optional[str] = None
    accounting_date: Optional[int] = None
    web_portal_url: Optional[str] = None
    pp_claim_from: Optional[str] = None
    fis_minimum_order: Optional[str] = None
    default_extended_credits_code: Optional[str] = None
    default_extended_credits_name: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"

# Brand models
class BrandCreate(ORMBase):
    """Model for creating a new brand"""
    code: str
    name: str
    store: str
    distributor_id: int
    is_hof_pref: bool = True
    comments: Optional[str] = None
    narta_rept: bool = True
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"

class BrandRead(ORMBase):
    """Model for reading brand data"""
    id: int
    uuid: str
    code: str
    name: str
    store: str
    distributor_id: int
    is_hof_pref: bool
    comments: Optional[str] = None
    narta_rept: bool
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None

class BrandUpdate(ORMBase):
    """Model for updating brand data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    distributor_id: Optional[int] = None
    is_hof_pref: Optional[bool] = None
    comments: Optional[str] = None
    narta_rept: Optional[bool] = None
    active: Optional[bool] = None
    modified_by: str = "system"

class CategoryAttributeSchema(ORMBase):
    id: Optional[int]
    name: str
    unit: Optional[str] = None
    value: str


class ProductCategorySchema(ORMBase):
    id: int
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str]
    deleted: Optional[datetime]
    code: str
    name: str
    store: str
    product_type_id: int
    attributes: List[CategoryAttributeSchema] = []

    class Config:
        orm_mode = True


class ProductTypeSchema(ORMBase):
    id: int
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str]
    deleted: Optional[datetime]
    code: str
    name: str
    store: str
    product_class_id: int
    categories: List[ProductCategorySchema] = []


class ProductClassSchema(ORMBase):
    id: int
    active: bool
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str]
    deleted: Optional[datetime]
    code: str
    name: str
    store: str
    types: List[ProductTypeSchema] = []


# CTC Models
class CTCBase(ORMBase):
    """Base model for CTC entities"""
    id: Optional[int] = None
    uuid: Optional[str] = None
    active: bool = True
    modified_by: str
    modified: datetime
    created_by: str
    created: datetime
    deleted_by: Optional[str] = None
    deleted: Optional[datetime] = None
    code: str
    name: str
    store: str


class CTCClassCreate(ORMBase):
    """Model for creating a new CTC class"""
    code: str
    name: str
    store: str
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCClassRead(CTCBase):
    """Model for reading CTC class data"""
    pass


class CTCClassUpdate(ORMBase):
    """Model for updating CTC class data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCTypeCreate(ORMBase):
    """Model for creating a new CTC type"""
    code: str
    name: str
    store: str
    class_id: int
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCTypeRead(CTCBase):
    """Model for reading CTC type data"""
    class_id: int


class CTCTypeUpdate(ORMBase):
    """Model for updating CTC type data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    class_id: Optional[int] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCCategoryCreate(ORMBase):
    """Model for creating a new CTC category"""
    code: str
    name: str
    store: str
    type_id: int
    product_id: Optional[int] = None
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCCategoryRead(CTCBase):
    """Model for reading CTC category data"""
    type_id: int
    product_id: Optional[int] = None


class CTCCategoryUpdate(ORMBase):
    """Model for updating CTC category data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    type_id: Optional[int] = None
    product_id: Optional[int] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCAttributeGroupCreate(ORMBase):
    """Model for creating a new CTC attribute group"""
    code: str
    name: str
    store: str
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCAttributeGroupRead(CTCBase):
    """Model for reading CTC attribute group data"""
    pass


class CTCAttributeGroupUpdate(ORMBase):
    """Model for updating CTC attribute group data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCDataTypeCreate(ORMBase):
    """Model for creating a new CTC data type"""
    code: str
    name: str
    store: str
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCDataTypeRead(CTCBase):
    """Model for reading CTC data type data"""
    pass


class CTCDataTypeUpdate(ORMBase):
    """Model for updating CTC data type data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCUnitOfMeasureCreate(ORMBase):
    """Model for creating a new CTC unit of measure"""
    code: str
    name: str
    store: str
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCUnitOfMeasureRead(CTCBase):
    """Model for reading CTC unit of measure data"""
    pass


class CTCUnitOfMeasureUpdate(ORMBase):
    """Model for updating CTC unit of measure data"""
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CTCAttributeCreate(ORMBase):
    """Model for creating a new CTC attribute"""
    name: str
    store: str
    category_id: int
    attribute_group_id: int
    data_type_id: int
    uom_id: Optional[int] = None
    rank: int = 0
    as_filter: bool = False
    active: bool = True
    modified_by: str = "system"
    created_by: str = "system"


class CTCAttributeRead(CTCBase):
    """Model for reading CTC attribute data"""
    category_id: int
    attribute_group_id: int
    data_type_id: int
    uom_id: Optional[int] = None
    rank: int
    as_filter: bool
    scraped_at: Optional[datetime] = None


class CTCAttributeUpdate(ORMBase):
    """Model for updating CTC attribute data"""
    name: Optional[str] = None
    store: Optional[str] = None
    category_id: Optional[int] = None
    attribute_group_id: Optional[int] = None
    data_type_id: Optional[int] = None
    uom_id: Optional[int] = None
    rank: Optional[int] = None
    as_filter: Optional[bool] = None
    active: Optional[bool] = None
    modified_by: str = "system"


class CategoryAttributeCreate(ORMBase):
    """Model for creating a new category attribute"""
    category_id: int
    name: str
    value: str


class CategoryAttributeRead(ORMBase):
    """Model for reading category attribute data"""
    category_id: int
    name: str
    value: str


class CategoryAttributeUpdate(ORMBase):
    """Model for updating category attribute data"""
    name: Optional[str] = None
    value: Optional[str] = None


# CTC Hierarchy Models
class CTCCategoryHierarchy(ORMBase):
    """Model for CTC category in hierarchy"""
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    product_id: Optional[int] = None


class CTCTypeHierarchy(ORMBase):
    """Model for CTC type in hierarchy"""
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    categories: List[CTCCategoryHierarchy] = []


class CTCClassHierarchy(ORMBase):
    """Model for CTC class in hierarchy"""
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    types: List[CTCTypeHierarchy] = []


# CTC Search Models
class CTCSearchResult(ORMBase):
    """Model for CTC search results"""
    level: int
    type: str  # 'class', 'type', or 'category'
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    class_id: Optional[int] = None
    type_id: Optional[int] = None
    product_id: Optional[int] = None


# CTC Statistics Models
class CTCStatistics(ORMBase):
    """Model for CTC statistics"""
    classes: Dict[str, int]
    types: Dict[str, int]
    categories: Dict[str, int]
    attributes: Dict[str, int]


# CTC Attribute Detail Models
class CTCAttributeGroupDetail(ORMBase):
    """Model for attribute group details"""
    id: int
    name: str
    code: str


class CTCDataTypeDetail(ORMBase):
    """Model for data type details"""
    id: int
    name: str
    code: str


class CTCUnitOfMeasureDetail(ORMBase):
    """Model for unit of measure details"""
    id: int
    name: str
    code: str


class CTCAttributeDetail(ORMBase):
    """Model for CTC attribute details"""
    id: int
    uuid: str
    name: str
    rank: int
    as_filter: bool
    active: bool
    attribute_group: CTCAttributeGroupDetail
    data_type: CTCDataTypeDetail
    unit_of_measure: Optional[CTCUnitOfMeasureDetail] = None


class SimpleAttributeDetail(ORMBase):
    """Model for simple attribute details"""
    id: int
    name: str
    value: str


class CTCCategoryWithAttributes(ORMBase):
    """Model for category with all its attributes"""
    id: int
    uuid: str
    code: str
    name: str
    active: bool
    type_id: int
    product_id: Optional[int] = None
    ctc_attributes: List[CTCAttributeDetail] = []
    simple_attributes: List[SimpleAttributeDetail] = []


class ProductCTCCategoryRead(ORMBase):
    id: int
    uuid: str
    code: str
    name: str
    type_id: int
    type_code: str
    type_name: str
    class_id: int
    class_code: str
    class_name: str


class ProductCTCHierarchy(ORMBase):
    class_id: int
    class_code: str
    class_name: str
    type_id: int
    type_code: str
    type_name: str
    category_id: int
    category_code: str
    category_name: str


class AssignProductToCategoryRequest(ORMBase):
    category_id: int


# CTC Consolidated Hierarchy Response Models
class ConsolidatedHierarchyResponse(ORMBase):
    """Model for consolidated hierarchy endpoint response"""
    level: str  # "classes", "types", or "categories"
    parent_class_uuid: Optional[str] = None
    parent_type_uuid: Optional[str] = None
    data: List[Union[CTCClassRead, CTCTypeRead, CTCCategoryRead]]


class FuzzyMatchInfo(ORMBase):
    is_fuzzy: bool
    field: str  # 'brand' or 'distributor'
    input_value: str
    matched_value: str
    similarity: float

class ProductCreateResult(ORMBase):
    product: Optional[Product] = None
    fuzzy_matches: List[FuzzyMatchInfo] = []
    error: Optional[str] = None

class BulkProductCreateResult(ORMBase):
    created: List[ProductCreateResult] = []
    failed: List[ProductCreateResult] = []

