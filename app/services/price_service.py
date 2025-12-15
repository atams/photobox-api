"""
Price Service - Business logic for prices
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

from atams.exceptions import NotFoundException, BadRequestException, UnprocessableEntityException
from atams.logging import get_logger

from app.repositories.price_repository import PriceRepository
from app.schemas.price import PriceCreate, PriceResponse, PriceListItem

logger = get_logger(__name__)


class PriceService:
    """Service for price business logic"""

    def __init__(self):
        self.repository = PriceRepository()

    async def create_price(self, db: Session, data: PriceCreate) -> PriceResponse:
        """
        Create a new price

        Args:
            db: Database session
            data: Price creation data

        Returns:
            Created price response
        """
        # Create price
        price_data = {
            "mp_price": data.price,
            "mp_description": data.description,
            "mp_quota": data.quota,
            "mp_is_active": True
        }

        price = self.repository.create(db, price_data)
        logger.info(f"Price created: {price.mp_id} - {price.mp_price}")

        return PriceResponse(
            id=price.mp_id,
            price=price.mp_price,
            description=price.mp_description,
            quota=price.mp_quota,
            is_active=price.mp_is_active,
            created_at=price.created_at,
            updated_at=price.updated_at
        )

    async def deactivate_price(self, db: Session, price_id: UUID) -> PriceResponse:
        """
        Deactivate a price (soft delete)

        Args:
            db: Database session
            price_id: Price UUID

        Returns:
            Updated price response

        Raises:
            NotFoundException: If price not found
            BadRequestException: If price already inactive
        """
        # Check if price exists
        price = self.repository.get_by_id(db, price_id)
        if not price:
            raise NotFoundException(
                "Price not found",
                details={"price_id": str(price_id)}
            )

        # Check if already inactive
        if not price.mp_is_active:
            raise BadRequestException(
                "Price already inactive",
                details={"price_id": str(price_id)}
            )

        # Deactivate price
        update_data = {
            "mp_is_active": False,
            "updated_at": datetime.now()
        }
        self.repository.update(db, price, update_data)
        logger.info(f"Price deactivated: {price_id}")

        return PriceResponse(
            id=price.mp_id,
            price=price.mp_price,
            description=price.mp_description,
            quota=price.mp_quota,
            is_active=price.mp_is_active,
            created_at=price.created_at,
            updated_at=price.updated_at
        )

    async def activate_price(self, db: Session, price_id: UUID) -> PriceResponse:
        """
        Activate a price

        Args:
            db: Database session
            price_id: Price UUID

        Returns:
            Updated price response

        Raises:
            NotFoundException: If price not found
            BadRequestException: If price already active
        """
        # Check if price exists
        price = self.repository.get_by_id(db, price_id)
        if not price:
            raise NotFoundException(
                "Price not found",
                details={"price_id": str(price_id)}
            )

        # Check if already active
        if price.mp_is_active:
            raise BadRequestException(
                "Price already active",
                details={"price_id": str(price_id)}
            )

        # Activate price
        update_data = {
            "mp_is_active": True,
            "updated_at": datetime.now()
        }
        self.repository.update(db, price, update_data)
        logger.info(f"Price activated: {price_id}")

        return PriceResponse(
            id=price.mp_id,
            price=price.mp_price,
            description=price.mp_description,
            quota=price.mp_quota,
            is_active=price.mp_is_active,
            created_at=price.created_at,
            updated_at=price.updated_at
        )

    async def validate_price_for_transaction(self, db: Session, price_id: UUID) -> None:
        """
        Validate price for transaction creation

        Args:
            db: Database session
            price_id: Price UUID

        Raises:
            NotFoundException: If price not found
            BadRequestException: If price is inactive
            UnprocessableEntityException: If quota exceeded
        """
        # Check if price exists
        price = self.repository.get_by_id(db, price_id)
        if not price:
            raise NotFoundException(
                "Price not found",
                details={"price_id": str(price_id)}
            )

        # Check if price is active
        if not price.mp_is_active:
            raise BadRequestException(
                "Price is inactive",
                details={"price_id": str(price_id)}
            )

        # Check quota if set
        if price.mp_quota is not None:
            used_quota = self.repository.count_transactions_by_price(db, price_id)
            if used_quota >= price.mp_quota:
                raise UnprocessableEntityException(
                    "Price quota exceeded",
                    details={
                        "price_id": str(price_id),
                        "quota": price.mp_quota,
                        "used": used_quota
                    }
                )

        logger.debug(f"Price validated for transaction: {price_id}")

    async def get_price_list(self, db: Session) -> list[PriceListItem]:
        """
        Get list of all prices with remaining quota

        Args:
            db: Database session

        Returns:
            List of prices with remaining quota calculated
        """
        prices = self.repository.get_all(db)

        result = []
        for price in prices:
            # Calculate remaining quota
            remaining_quota = None
            if price.mp_quota is not None:
                used_quota = self.repository.count_transactions_by_price(db, price.mp_id)
                remaining_quota = price.mp_quota - used_quota

            result.append(
                PriceListItem(
                    id=price.mp_id,
                    price=price.mp_price,
                    description=price.mp_description,
                    quota=price.mp_quota,
                    remaining_quota=remaining_quota,
                    is_active=price.mp_is_active,
                    created_at=price.created_at,
                    updated_at=price.updated_at
                )
            )

        return result
