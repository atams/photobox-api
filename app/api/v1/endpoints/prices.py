"""
Price Endpoints - API routes for prices
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from atams.db import get_db
from app.services.price_service import PriceService
from app.schemas.price import PriceCreate, PriceResponse, PriceListItem
from typing import List

router = APIRouter()
price_service = PriceService()


@router.get("", response_model=List[PriceListItem], status_code=status.HTTP_200_OK)
async def get_prices(
    db: Session = Depends(get_db)
):
    """
    Get all prices with detailed information

    Returns list of all prices ordered by created_at (newest first) with:
    - Full price details
    - Remaining quota calculation (quota - used transactions)
    - Active/inactive status
    """
    return await price_service.get_price_list(db)


@router.post("", response_model=PriceResponse, status_code=status.HTTP_201_CREATED)
async def create_price(
    data: PriceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new price

    - **price**: Price amount in IDR (required, > 0)
    - **description**: Price description (optional, max 255 chars)
    - **quota**: Maximum transaction quota (optional, > 0 or null = unlimited)
    """
    return await price_service.create_price(db, data)


@router.patch("/{price_id}/deactivate", response_model=PriceResponse, status_code=status.HTTP_200_OK)
async def deactivate_price(
    price_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Deactivate a price (soft delete)

    - **price_id**: Price UUID

    **Note:** This is a soft delete. Price will be marked as inactive and cannot be used for new transactions.
    """
    return await price_service.deactivate_price(db, price_id)


@router.patch("/{price_id}/activate", response_model=PriceResponse, status_code=status.HTTP_200_OK)
async def activate_price(
    price_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Activate a price

    - **price_id**: Price UUID

    **Note:** Price will be marked as active and can be used for new transactions.
    """
    return await price_service.activate_price(db, price_id)
