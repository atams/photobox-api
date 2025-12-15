"""
Price Schemas - DTOs for Price API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# Request Schemas
class PriceCreate(BaseModel):
    """Schema for creating a price"""
    price: Decimal = Field(..., gt=0, description="Price amount in IDR")
    description: Optional[str] = Field(None, max_length=255, description="Price description (e.g., 'Event Special Price')")
    quota: Optional[int] = Field(None, gt=0, description="Maximum transaction quota (NULL = unlimited)")


# Response Schemas
class PriceResponse(BaseModel):
    """Schema for price detail response"""
    id: UUID = Field(..., description="Price ID")
    price: Decimal = Field(..., description="Price amount")
    description: Optional[str] = Field(None, description="Price description")
    quota: Optional[int] = Field(None, description="Transaction quota")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class PriceInfo(BaseModel):
    """Schema for price info in nested responses (minimal fields)"""
    id: UUID = Field(..., description="Price ID")
    price: Decimal = Field(..., description="Price amount")

    class Config:
        from_attributes = True


class PriceListItem(BaseModel):
    """Schema for price list item with remaining quota"""
    id: UUID = Field(..., description="Price ID")
    price: Decimal = Field(..., description="Price amount")
    description: Optional[str] = Field(None, description="Price description")
    quota: Optional[int] = Field(None, description="Total quota (NULL = unlimited)")
    remaining_quota: Optional[int] = Field(None, description="Remaining quota (NULL = unlimited)")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True
