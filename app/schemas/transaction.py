"""
Transaction Schemas - DTOs for Transaction API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


# Request Schemas
class TransactionCreate(BaseModel):
    """Schema for creating a transaction"""
    location_id: int = Field(..., description="Location ID where QR is generated")


# Response Schemas
class LocationInfo(BaseModel):
    """Schema for location info in transaction response"""
    id: int = Field(..., description="Location ID")
    name: str = Field(..., description="Location name")


class TransactionCreateResponse(BaseModel):
    """Schema for transaction creation response"""
    transaction_id: int = Field(..., description="Transaction ID")
    external_id: str = Field(..., description="External transaction ID")
    amount: Decimal = Field(..., description="Transaction amount")
    status: str = Field(..., description="Transaction status")
    qr_string: str = Field(..., description="QR code string")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class TransactionDetailResponse(BaseModel):
    """Schema for transaction detail response"""
    id: int = Field(..., description="Transaction ID")
    external_id: str = Field(..., description="External transaction ID")
    xendit_id: Optional[str] = Field(None, description="Xendit transaction ID")
    amount: Decimal = Field(..., description="Transaction amount")
    status: str = Field(..., description="Transaction status")
    paid_at: Optional[datetime] = Field(None, description="Payment timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    location: LocationInfo = Field(..., description="Location information")

    class Config:
        from_attributes = True


class TransactionByExternalIdResponse(BaseModel):
    """Schema for transaction by external ID response (used for polling)"""
    transaction_id: int = Field(..., description="Transaction ID")
    external_id: str = Field(..., description="External transaction ID")
    amount: Decimal = Field(..., description="Transaction amount")
    status: str = Field(..., description="Transaction status")
    qr_string: str = Field(..., description="QR code string for display")  # CRITICAL: Frontend needs this for QR display
    paid_at: Optional[datetime] = Field(None, description="Payment timestamp")
    location: LocationInfo = Field(..., description="Location information")

    class Config:
        from_attributes = True


class TransactionListItem(BaseModel):
    """Schema for transaction list item"""
    id: int = Field(..., description="Transaction ID")
    external_id: str = Field(..., description="External transaction ID")
    amount: Decimal = Field(..., description="Transaction amount")
    status: str = Field(..., description="Transaction status")
    created_at: datetime = Field(..., description="Creation timestamp")
    location: LocationInfo = Field(..., description="Location information")

    class Config:
        from_attributes = True


# Webhook Schema
class XenditWebhookPayload(BaseModel):
    """Schema for Xendit webhook payload"""
    external_id: str = Field(..., description="External transaction ID")
    status: str = Field(..., description="Transaction status")
    xendit_id: str = Field(..., description="Xendit transaction ID")
    paid_at: datetime = Field(..., description="Payment timestamp")


class WebhookResponse(BaseModel):
    """Schema for webhook response"""
    message: str = Field(default="Transaction updated")
