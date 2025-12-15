"""
Transaction Repository - Database operations for transactions
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func, text
from datetime import date, timedelta

from atams.db import BaseRepository
from app.models.transaction import Transaction
from app.models.location import Location


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for Transaction model"""

    def __init__(self):
        super().__init__(Transaction)

    def get_by_external_id(self, db: Session, external_id: str) -> Optional[Transaction]:
        """
        Get transaction by external ID with location relationship

        Args:
            db: Database session
            external_id: External transaction ID

        Returns:
            Transaction or None
        """
        return (
            db.query(Transaction)
            .options(joinedload(Transaction.location))
            .filter(Transaction.tr_external_id == external_id)
            .first()
        )

    def get_by_id_with_location(self, db: Session, transaction_id: int) -> Optional[Transaction]:
        """
        Get transaction by ID with location relationship

        Args:
            db: Database session
            transaction_id: Transaction ID

        Returns:
            Transaction or None
        """
        return (
            db.query(Transaction)
            .options(joinedload(Transaction.location))
            .filter(Transaction.tr_id == transaction_id)
            .first()
        )

    def get_list_with_filters(
        self,
        db: Session,
        location_ids: Optional[List[int]] = None,
        status: Optional[List[str]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Transaction], int]:
        """
        Get transactions with filters and pagination

        Args:
            db: Database session
            location_ids: List of location IDs to filter
            status: List of status values to filter
            date_from: Start date filter (required)
            date_to: End date filter (required)
            search: Search text for external_id, xendit_id, location.name
            sort_by: Column to sort by
            sort_order: Sort order (asc/desc)
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Tuple of (transactions list, total count)
        """
        query = db.query(Transaction).options(joinedload(Transaction.location))

        # Filter by location IDs
        if location_ids:
            query = query.filter(Transaction.tr_location_id.in_(location_ids))

        # Filter by status
        if status:
            query = query.filter(Transaction.tr_status.in_(status))

        # Date range filter (required)
        if date_from:
            query = query.filter(Transaction.created_at >= date_from)
        if date_to:
            # Include the entire end date (add 1 day to make it inclusive)
            # BUG FIX: Use timedelta instead of incorrect SQLAlchemy type_descriptor_class
            end_date = date_to + timedelta(days=1)
            query = query.filter(Transaction.created_at < end_date)

        # Search filter
        if search:
            search_term = f"%{search}%"
            query = query.outerjoin(Location).filter(
                or_(
                    Transaction.tr_external_id.ilike(search_term),
                    Transaction.tr_xendit_id.ilike(search_term),
                    Location.ml_name.ilike(search_term)
                )
            )

        # Get total count before pagination
        total = query.count()

        # Sorting
        sort_column = {
            "created_at": Transaction.created_at,
            "amount": Transaction.tr_amount,
            "status": Transaction.tr_status,
            "paid_at": Transaction.tr_paid_at,
            "external_id": Transaction.tr_external_id
        }.get(sort_by, Transaction.created_at)

        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Pagination
        transactions = query.offset(skip).limit(limit).all()

        return transactions, total

    def update_by_external_id(
        self,
        db: Session,
        external_id: str,
        update_data: dict
    ) -> Optional[Transaction]:
        """
        Update transaction by external ID

        Args:
            db: Database session
            external_id: External transaction ID
            update_data: Dictionary of fields to update

        Returns:
            Updated transaction or None
        """
        transaction = self.get_by_external_id(db, external_id)
        if transaction:
            for key, value in update_data.items():
                if hasattr(transaction, key):
                    setattr(transaction, key, value)
            db.commit()
            db.refresh(transaction)
        return transaction
