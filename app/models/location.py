"""
Location Model - Master Locations Table
"""
from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from atams.db import Base


class Location(Base):
    """Location model for master_locations table"""
    __tablename__ = "master_locations"
    __table_args__ = {"schema": "photobox"}

    ml_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ml_machine_code = Column(String(50), unique=True, nullable=False, index=True)
    ml_name = Column(String(100), nullable=False)
    ml_address = Column(Text, nullable=True)
    ml_is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
