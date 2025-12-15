"""
Transaction Service - Business logic for transactions
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from decimal import Decimal
from math import ceil
import secrets

from atams.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
    UnprocessableEntityException
)
from atams.logging import get_logger

from app.repositories.transaction_repository import TransactionRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.price_repository import PriceRepository
from app.services.xendit_service import XenditService
from app.services.price_service import PriceService
from app.schemas.transaction import (
    TransactionCreate,
    TransactionCreateResponse,
    TransactionDetailResponse,
    TransactionByExternalIdResponse,
    TransactionListItem,
    LocationInfo,
    LocationDetail,
    PriceInfo,
    PriceDetail,
    XenditWebhookPayload
)

logger = get_logger(__name__)


class TransactionService:
    """Service for transaction business logic"""

    def __init__(self, xendit_api_key: str):
        self.repository = TransactionRepository()
        self.location_repository = LocationRepository()
        self.price_repository = PriceRepository()
        self.price_service = PriceService()
        self.xendit_service = XenditService(api_key=xendit_api_key)

    def _generate_external_id(self, location_id: int) -> str:
        """
        Generate unique external ID with format: TRX-{location_id}-{timestamp}-{random}

        Args:
            location_id: Location ID

        Returns:
            Generated external ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(4).upper()  # 8 chars random hex
        return f"TRX-{location_id}-{timestamp}-{random_suffix}"

    async def create_transaction(
        self,
        db: Session,
        data: TransactionCreate,
        webhook_url: Optional[str] = None
    ) -> TransactionCreateResponse:
        """
        Create a new transaction and generate QRIS

        Args:
            db: Database session
            data: Transaction creation data
            webhook_url: Webhook callback URL for Xendit

        Returns:
            Transaction creation response

        Raises:
            NotFoundException: If location or price not found
            BadRequestException: If price is inactive
            UnprocessableEntityException: If quota exceeded or location inactive
        """
        # Validate location exists and is active
        location = self.location_repository.get(db, data.location_id)
        if not location:
            raise NotFoundException(
                "Location not found",
                details={"location_id": data.location_id}
            )
        if not location.ml_is_active:
            raise UnprocessableEntityException(
                "Location is not active",
                details={"location_id": data.location_id}
            )

        # Validate price (exists, active, quota)
        await self.price_service.validate_price_for_transaction(db, data.price_id)

        # Get price to use for amount
        price = self.price_repository.get_by_id(db, data.price_id)
        amount = price.mp_price

        # Auto-generate external_id
        external_id = self._generate_external_id(data.location_id)

        # Generate QRIS from Xendit
        qris_data = await self.xendit_service.create_qris(
            external_id=external_id,
            amount=amount,
            callback_url=webhook_url
        )

        # Create transaction in database
        transaction_data = {
            "tr_location_id": data.location_id,
            "tr_price_id": data.price_id,
            "tr_external_id": external_id,
            "tr_xendit_id": qris_data.get("xendit_id"),
            "tr_status": "PENDING",
            "tr_qr_string": qris_data.get("qr_string")
        }

        transaction = self.repository.create(db, transaction_data)

        # Refresh to load relationships
        db.refresh(transaction)

        logger.info(f"Transaction created: {transaction.tr_id} - {transaction.tr_external_id} - Amount: {amount}")

        location_info = LocationInfo(
            id=transaction.location.ml_id,
            machine_code=transaction.location.ml_machine_code
        )

        price_info = PriceInfo(
            id=transaction.price.mp_id,
            price=transaction.price.mp_price
        )

        return TransactionCreateResponse(
            id=transaction.tr_id,
            external_id=transaction.tr_external_id,
            location_id=transaction.tr_location_id,
            location=location_info,
            price_id=transaction.tr_price_id,
            price=price_info,
            status=transaction.tr_status,
            qr_string=transaction.tr_qr_string,
            created_at=transaction.created_at
        )

    async def get_transaction_by_external_id(
        self,
        db: Session,
        external_id: str
    ) -> TransactionByExternalIdResponse:
        """
        Get transaction by external ID

        Args:
            db: Database session
            external_id: External transaction ID

        Returns:
            Transaction response

        Raises:
            NotFoundException: If transaction not found
        """
        transaction = self.repository.get_by_external_id(db, external_id)
        if not transaction:
            raise NotFoundException(
                "Transaction not found",
                details={"external_id": external_id}
            )

        location_info = LocationInfo(
            id=transaction.location.ml_id,
            machine_code=transaction.location.ml_machine_code
        ) if transaction.location else None

        price_info = PriceInfo(
            id=transaction.price.mp_id,
            price=transaction.price.mp_price
        ) if transaction.price else None

        return TransactionByExternalIdResponse(
            id=transaction.tr_id,
            external_id=transaction.tr_external_id,
            location_id=transaction.tr_location_id,
            location=location_info,
            price_id=transaction.tr_price_id,
            price=price_info,
            status=transaction.tr_status,
            qr_string=transaction.tr_qr_string,
            paid_at=transaction.tr_paid_at,
            created_at=transaction.created_at
        )

    async def get_transaction_detail(
        self,
        db: Session,
        transaction_id: int
    ) -> TransactionDetailResponse:
        """
        Get transaction detail by ID with full details

        Args:
            db: Database session
            transaction_id: Transaction ID

        Returns:
            Transaction detail response with full location and price details

        Raises:
            NotFoundException: If transaction not found
        """
        transaction = self.repository.get_by_id_with_location(db, transaction_id)
        if not transaction:
            raise NotFoundException(
                "Transaction not found",
                details={"transaction_id": transaction_id}
            )

        # Map location detail
        location_detail = LocationDetail(
            id=transaction.location.ml_id,
            machine_code=transaction.location.ml_machine_code,
            name=transaction.location.ml_name,
            address=transaction.location.ml_address,
            is_active=transaction.location.ml_is_active,
            created_at=transaction.location.created_at
        ) if transaction.location else None

        # Map price detail with remaining quota calculation
        price_detail = None
        if transaction.price:
            # Calculate remaining quota
            remaining_quota = None
            if transaction.price.mp_quota is not None:
                used_quota = self.price_repository.count_transactions_by_price(db, transaction.price.mp_id)
                remaining_quota = transaction.price.mp_quota - used_quota

            price_detail = PriceDetail(
                id=transaction.price.mp_id,
                price=transaction.price.mp_price,
                description=transaction.price.mp_description,
                quota=transaction.price.mp_quota,
                remaining_quota=remaining_quota,
                is_active=transaction.price.mp_is_active,
                created_at=transaction.price.created_at,
                updated_at=transaction.price.updated_at
            )

        return TransactionDetailResponse(
            id=transaction.tr_id,
            external_id=transaction.tr_external_id,
            xendit_id=transaction.tr_xendit_id,
            location_id=transaction.tr_location_id,
            location=location_detail,
            price_id=transaction.tr_price_id,
            price=price_detail,
            status=transaction.tr_status,
            qr_string=transaction.tr_qr_string,
            paid_at=transaction.tr_paid_at,
            created_at=transaction.created_at
        )

    async def get_transaction_list(
        self,
        db: Session,
        location_ids: Optional[List[int]] = None,
        status: Optional[List[str]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get paginated list of transactions

        Args:
            db: Database session
            location_ids: Filter by location IDs
            status: Filter by status values
            date_from: Start date (required)
            date_to: End date (required)
            page: Page number (1-indexed)
            limit: Items per page
            search: Search text
            sort_by: Column to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            Dictionary with meta and data

        Raises:
            BadRequestException: If parameters are invalid
        """
        # Validate parameters
        if page < 1:
            raise BadRequestException("Page must be at least 1")
        if limit < 1 or limit > 100:
            raise BadRequestException("Limit must be between 1 and 100")
        if not date_from or not date_to:
            raise BadRequestException("date_from and date_to are required")

        # Validate date range (max 365 days)
        date_diff = (date_to - date_from).days
        if date_diff > 365:
            raise BadRequestException("Date range cannot exceed 365 days")
        if date_diff < 0:
            raise BadRequestException("date_to must be after date_from")

        skip = (page - 1) * limit

        transactions, total = self.repository.get_list_with_filters(
            db=db,
            location_ids=location_ids,
            status=status,
            date_from=date_from,
            date_to=date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit
        )

        # Convert to response schema
        items = []
        for txn in transactions:
            location_info = LocationInfo(
                id=txn.location.ml_id,
                machine_code=txn.location.ml_machine_code
            ) if txn.location else None

            price_info = PriceInfo(
                id=txn.price.mp_id,
                price=txn.price.mp_price
            ) if txn.price else None

            items.append(
                TransactionListItem(
                    id=txn.tr_id,
                    external_id=txn.tr_external_id,
                    location_id=txn.tr_location_id,
                    location=location_info,
                    price_id=txn.tr_price_id,
                    price=price_info,
                    status=txn.tr_status,
                    created_at=txn.created_at
                )
            )

        total_pages = ceil(total / limit) if total > 0 else 0

        return {
            "meta": {
                "page": page,
                "limit": limit,
                "total_items": total,
                "total_pages": total_pages
            },
            "data": items
        }

    async def process_webhook(
        self,
        db: Session,
        payload: XenditWebhookPayload
    ) -> Dict[str, str]:
        """
        Process Xendit webhook

        Args:
            db: Database session
            payload: Webhook payload

        Returns:
            Success message

        Raises:
            NotFoundException: If transaction not found
        """
        # Get transaction by external_id
        transaction = self.repository.get_by_external_id(db, payload.external_id)
        if not transaction:
            raise NotFoundException(
                "Transaction not found",
                details={"external_id": payload.external_id}
            )

        # Update transaction
        update_data = {
            "tr_status": payload.status,
            "tr_xendit_id": payload.xendit_id,
        }

        # Set paid_at timestamp to now if status is COMPLETED
        if payload.status == "COMPLETED":
            update_data["tr_paid_at"] = datetime.now()

        self.repository.update_by_external_id(db, payload.external_id, update_data)
        logger.info(f"Transaction updated via webhook: {payload.external_id} - {payload.status}")

        return {"message": "Transaction updated"}
