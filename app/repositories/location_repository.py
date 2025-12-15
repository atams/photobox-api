"""
Location Repository - Database operations for locations
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from atams.db import BaseRepository
from app.models.location import Location


class LocationRepository(BaseRepository[Location]):
    """Repository for Location model"""

    def __init__(self):
        super().__init__(Location)

    def get_by_machine_code(self, db: Session, machine_code: str) -> Optional[Location]:
        """
        Get location by machine code

        Args:
            db: Database session
            machine_code: Machine code to search for

        Returns:
            Location or None
        """
        return db.query(Location).filter(Location.ml_machine_code == machine_code).first()

    def get_list_with_filters(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "machine_code",
        sort_order: str = "asc",
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Location], int]:
        """
        Get locations with filters and pagination

        Args:
            db: Database session
            is_active: Filter by active status (None = all)
            search: Search text for machine_code, name, address
            sort_by: Column to sort by
            sort_order: Sort order (asc/desc)
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Tuple of (locations list, total count)
        """
        query = db.query(Location)

        # Filter by is_active
        if is_active is not None:
            query = query.filter(Location.ml_is_active == is_active)

        # Search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Location.ml_machine_code.ilike(search_term),
                    Location.ml_name.ilike(search_term),
                    Location.ml_address.ilike(search_term)
                )
            )

        # Get total count before pagination
        total = query.count()

        # Sorting
        sort_column = {
            "machine_code": Location.ml_machine_code,
            "name": Location.ml_name,
            "address": Location.ml_address
        }.get(sort_by, Location.ml_machine_code)

        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Pagination
        locations = query.offset(skip).limit(limit).all()

        return locations, total
