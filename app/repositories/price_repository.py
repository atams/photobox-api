"""
Price Repository - Database operations for prices
"""
from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID

from atams.db import BaseRepository
from app.models.price import Price


class PriceRepository(BaseRepository[Price]):
    """Repository for Price model"""

    def __init__(self):
        super().__init__(Price)

    def get_by_id(self, db: Session, price_id: UUID) -> Optional[Price]:
        """
        Get price by ID

        Args:
            db: Database session
            price_id: Price UUID to search for

        Returns:
            Price or None
        """
        return db.query(Price).filter(Price.mp_id == price_id).first()

    def get_active_by_id(self, db: Session, price_id: UUID) -> Optional[Price]:
        """
        Get active price by ID

        Args:
            db: Database session
            price_id: Price UUID to search for

        Returns:
            Price or None (only if active)
        """
        return db.query(Price).filter(
            Price.mp_id == price_id,
            Price.mp_is_active == True
        ).first()

    def get_all(self, db: Session) -> list[Price]:
        """
        Get all prices ordered by created_at desc

        Args:
            db: Database session

        Returns:
            List of all prices
        """
        return db.query(Price).order_by(Price.created_at.desc()).all()

    def count_transactions_by_price(self, db: Session, price_id: UUID) -> int:
        """
        Count transactions using this price

        Args:
            db: Database session
            price_id: Price UUID

        Returns:
            Number of transactions
        """
        from app.models.transaction import Transaction
        return db.query(Transaction).filter(Transaction.tr_price_id == price_id).count()
