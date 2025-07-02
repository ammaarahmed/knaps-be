from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from ...models import RebateAgreementCreate, RebateAgreementRead
from ...storage import storage
import logging

logger = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/rebates")

@router.post("/agreements", response_model=RebateAgreementRead, status_code=201)
async def create_rebate_agreement(data: RebateAgreementCreate):
    """
    Create a new rebate agreement (vendor or customer rebate program).
    
    This endpoint validates the input and creates a new rebate agreement with:
    - Agreement terms and tier structures
    - Product and category associations
    - Validation for overlapping ranges and business rules
    
    Returns the newly created agreement data.
    """
    try:
        return await storage.create_rebate_agreement(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating rebate agreement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/agreements", response_model=List[RebateAgreementRead])
async def list_rebate_agreements(
    agreement_type: Optional[str] = None,
    distributor_id: Optional[int] = None,
    status: Optional[str] = None
):
    """List rebate agreements with optional filtering."""
    return await storage.get_rebate_agreements(agreement_type, distributor_id, status)

@router.get("/agreements/{agreement_id}", response_model=RebateAgreementRead)
async def get_rebate_agreement(agreement_id: int):
    """Get a specific rebate agreement by ID."""
    agreement = await storage.get_rebate_agreement(agreement_id)
    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rebate agreement not found"
        )
    return agreement

@router.put("/agreements/{agreement_id}", response_model=RebateAgreementRead)
async def update_rebate_agreement(agreement_id: int, data: RebateAgreementCreate):
    """Update an existing rebate agreement."""
    try:
        agreement = await storage.update_rebate_agreement(agreement_id, data)
        if not agreement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rebate agreement not found"
            )
        return agreement
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/agreements/{agreement_id}", status_code=204)
async def delete_rebate_agreement(agreement_id: int):
    """Delete a rebate agreement."""
    success = await storage.delete_rebate_agreement(agreement_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rebate agreement not found"
        ) 