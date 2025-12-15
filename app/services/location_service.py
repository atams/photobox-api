"""
Location Service - Business logic for locations
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from math import ceil

from atams.exceptions import NotFoundException, ConflictException, BadRequestException
from atams.logging import get_logger

from app.repositories.location_repository import LocationRepository
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse, LocationListItem

logger = get_logger(__name__)


class LocationService:
    """Service for location business logic"""

    def __init__(self):
        self.repository = LocationRepository()

    async def create_location(self, db: Session, data: LocationCreate) -> LocationResponse:
        """
        Create a new location

        Args:
            db: Database session
            data: Location creation data

        Returns:
            Created location response

        Raises:
            ConflictException: If machine_code already exists
        """
        # Check if machine_code already exists
        existing = self.repository.get_by_machine_code(db, data.machine_code)
        if existing:
            raise ConflictException(
                "Machine code already exists",
                details={"machine_code": data.machine_code}
            )

        # Create location
        location_data = {
            "ml_machine_code": data.machine_code,
            "ml_name": data.name,
            "ml_address": data.address,
            "ml_is_active": data.is_active
        }

        location = self.repository.create(db, location_data)
        logger.info(f"Location created: {location.ml_id} - {location.ml_machine_code}")

        return LocationResponse(
            id=location.ml_id,
            machine_code=location.ml_machine_code,
            name=location.ml_name,
            address=location.ml_address,
            is_active=location.ml_is_active,
            created_at=location.created_at
        )

    async def get_location_list(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        sort_by: str = "machine_code",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """
        Get paginated list of locations

        Args:
            db: Database session
            is_active: Filter by active status
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

        skip = (page - 1) * limit

        locations, total = self.repository.get_list_with_filters(
            db=db,
            is_active=is_active,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit
        )

        # Convert to response schema
        items = [
            LocationListItem(
                id=loc.ml_id,
                machine_code=loc.ml_machine_code,
                name=loc.ml_name,
                address=loc.ml_address,
                is_active=loc.ml_is_active
            )
            for loc in locations
        ]

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

    async def get_location_detail(self, db: Session, location_id: int) -> LocationResponse:
        """
        Get location detail by ID

        Args:
            db: Database session
            location_id: Location ID

        Returns:
            Location detail response

        Raises:
            NotFoundException: If location not found
        """
        location = self.repository.get(db, location_id)
        if not location:
            raise NotFoundException(
                "Location not found",
                details={"location_id": location_id}
            )

        return LocationResponse(
            id=location.ml_id,
            machine_code=location.ml_machine_code,
            name=location.ml_name,
            address=location.ml_address,
            is_active=location.ml_is_active,
            created_at=location.created_at
        )

    async def update_location(
        self,
        db: Session,
        location_id: int,
        data: LocationUpdate
    ) -> Dict[str, str]:
        """
        Update location

        Args:
            db: Database session
            location_id: Location ID
            data: Update data

        Returns:
            Success message

        Raises:
            NotFoundException: If location not found
            BadRequestException: If no fields to update
        """
        # Check if location exists
        location = self.repository.get(db, location_id)
        if not location:
            raise NotFoundException(
                "Location not found",
                details={"location_id": location_id}
            )

        # Prepare update data
        update_data = {}
        if data.name is not None:
            update_data["ml_name"] = data.name
        if data.address is not None:
            update_data["ml_address"] = data.address
        if data.is_active is not None:
            update_data["ml_is_active"] = data.is_active

        if not update_data:
            raise BadRequestException("At least one field required")

        # Update location
        self.repository.update(db, location, update_data)
        logger.info(f"Location updated: {location_id}")

        return {"message": "Location updated successfully"}
