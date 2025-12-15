"""
Price Model - Master Price Table
"""
from sqlalchemy import Column, String, Numeric, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from atams.db import Base


class Price(Base):
    """Price model for master_price table"""
    __tablename__ = "master_price"
    __table_args__ = {"schema": "photobox"}

    mp_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    mp_price = Column(Numeric(15, 2), nullable=False)
    mp_description = Column(String(255), nullable=True)
    mp_quota = Column(Integer, nullable=True)
    mp_is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
