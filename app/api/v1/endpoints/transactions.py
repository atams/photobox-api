"""
Transaction Endpoints - API routes for transactions
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from atams.db import get_db
from app.core.config import settings
from app.services.transaction_service import TransactionService
from app.schemas.transaction import (
    TransactionCreate,
    TransactionCreateResponse,
    TransactionDetailResponse,
    TransactionByExternalIdResponse
)

router = APIRouter()

# Initialize with Xendit API key from settings
# Note: You need to add XENDIT_API_KEY to your settings
transaction_service = TransactionService(xendit_api_key=getattr(settings, "XENDIT_API_KEY", ""))


@router.post("", response_model=TransactionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction and generate QRIS

    - **location_id**: Location ID (required, must be active)
    - **price_id**: Price ID (required, must be active with available quota)

    **Notes:**
    - Amount is determined by the price_id
    - External ID is auto-generated with format: TRX-{location_id}-{timestamp}-{random}
    - Price quota is validated before transaction creation
    """
    # Get webhook URL from settings (required by Xendit)
    webhook_url = getattr(settings, "XENDIT_WEBHOOK_URL", "")
    if not webhook_url or not webhook_url.strip():
        raise Exception("XENDIT_WEBHOOK_URL is not configured in settings")
    return await transaction_service.create_transaction(db, data, webhook_url)


@router.get("/external/{external_id}", response_model=TransactionByExternalIdResponse, status_code=status.HTTP_200_OK)
async def get_transaction_by_external_id(
    external_id: str,
    db: Session = Depends(get_db)
):
    """
    Get transaction by external ID

    - **external_id**: External transaction ID

    **TASK C: Frontend Polling Endpoint**

    This endpoint is specifically designed to be polled by the frontend/kiosk application
    to check payment status in real-time.

    **Recommended Polling Strategy:**
    - Poll this endpoint every 3 seconds after QRIS is generated
    - Continue polling while status is "PENDING"
    - Stop polling when status changes to "COMPLETED", "FAILED", or "EXPIRED"
    - Stop polling after QRIS expiration time (15 minutes)

    **Response includes:**
    - Transaction status: PENDING, COMPLETED, FAILED, EXPIRED
    - QRIS string for display
    - Payment details when completed

    **Performance Note:**
    This endpoint is optimized for frequent polling with minimal database queries.
    """
    return await transaction_service.get_transaction_by_external_id(db, external_id)


@router.get("/{id}", response_model=TransactionDetailResponse, status_code=status.HTTP_200_OK)
async def get_transaction_detail(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Get transaction detail by ID

    - **id**: Transaction ID
    """
    return await transaction_service.get_transaction_detail(db, id)


@router.get("", status_code=status.HTTP_200_OK)
async def get_transactions(
    location_ids: Optional[List[int]] = Query(None, description="Filter by location IDs"),
    status: Optional[List[str]] = Query(None, description="Filter by status (PENDING, COMPLETED, FAILED, EXPIRED)"),
    date_from: date = Query(..., description="Start date (required)"),
    date_to: date = Query(..., description="End date (required)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (1-100)"),
    search: Optional[str] = Query(None, description="Search text"),
    sort_by: str = Query("created_at", description="Sort column"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of transactions

    **Query Parameters:**
    - **location_ids**: Filter by location IDs (empty = all locations)
    - **status**: Filter by status values (PENDING, COMPLETED, FAILED, EXPIRED) (empty = all)
    - **date_from**: Start date (required)
    - **date_to**: End date (required, max range: 365 days)
    - **page**: Page number (minimum 1)
    - **limit**: Items per page (1-100)
    - **search**: Search in external_id, xendit_id, or location name
    - **sort_by**: Column to sort by (created_at, status, paid_at, external_id)
    - **sort_order**: Sort order (asc/desc)
    """
    return await transaction_service.get_transaction_list(
        db=db,
        location_ids=location_ids,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
