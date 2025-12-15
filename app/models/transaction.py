"""
Transaction Model - Transactions Table
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from atams.db import Base


class Transaction(Base):
    """Transaction model for transactions table"""
    __tablename__ = "transactions"
    __table_args__ = {"schema": "photobox"}

    tr_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    # Relasi ke Lokasi
    tr_location_id = Column(BigInteger, ForeignKey("photobox.master_locations.ml_id", ondelete="SET NULL"), nullable=True)

    # Relasi ke Price
    tr_price_id = Column(UUID(as_uuid=True), ForeignKey("photobox.master_price.mp_id"), nullable=True, index=True)

    # Data dari Xendit
    tr_external_id = Column(String(255), unique=True, nullable=False, index=True)
    tr_xendit_id = Column(String(255), nullable=True)
    tr_status = Column(String(50), nullable=False, default="PENDING", index=True)
    tr_qr_string = Column(Text, nullable=True)

    # Audit Waktu
    tr_paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    location = relationship("Location", foreign_keys=[tr_location_id])
    price = relationship("Price", foreign_keys=[tr_price_id])
