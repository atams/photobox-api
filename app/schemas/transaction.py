"""
Transaction Schemas - DTOs for Transaction API
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# Request Schemas
class TransactionCreate(BaseModel):
    """Schema for creating a transaction"""
    location_id: int = Field(..., description="Location ID where QR is generated")
    price_id: UUID = Field(..., description="Price ID to use for this transaction")
    email: EmailStr = Field(..., description="User email for photo delivery")
    send_invoice: bool = Field(default=False, description="Whether to include invoice in email")


# Response Schemas
class LocationInfo(BaseModel):
    """Schema for location info in transaction response (minimal)"""
    id: int = Field(..., description="Location ID")
    machine_code: str = Field(..., description="Machine code")

    class Config:
        from_attributes = True


class LocationDetail(BaseModel):
    """Schema for detailed location info in transaction detail response"""
    id: int = Field(..., description="Location ID")
    machine_code: str = Field(..., description="Machine code")
    name: str = Field(..., description="Location name")
    address: Optional[str] = Field(None, description="Location address")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class PriceInfo(BaseModel):
    """Schema for price info in transaction response (minimal)"""
    id: UUID = Field(..., description="Price ID")
    price: Decimal = Field(..., description="Price amount")

    class Config:
        from_attributes = True


class PriceDetail(BaseModel):
    """Schema for detailed price info in transaction detail response"""
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


class TransactionCreateResponse(BaseModel):
    """Schema for transaction creation response"""
    id: int = Field(..., description="Transaction ID")
    external_id: str = Field(..., description="External transaction ID")
    location_id: int = Field(..., description="Location ID")
    location: LocationInfo = Field(..., description="Location information")
    price_id: UUID = Field(..., description="Price ID")
    price: PriceInfo = Field(..., description="Price information")
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
    location_id: int = Field(..., description="Location ID")
    location: LocationDetail = Field(..., description="Detailed location information")
    price_id: UUID = Field(..., description="Price ID")
    price: PriceDetail = Field(..., description="Detailed price information")
    status: str = Field(..., description="Transaction status")
    qr_string: str = Field(..., description="QR code string")
    paid_at: Optional[datetime] = Field(None, description="Payment timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class TransactionByExternalIdResponse(BaseModel):
    """Schema for transaction by external ID response (used for polling)"""
    id: int = Field(..., description="Transaction ID")
    external_id: str = Field(..., description="External transaction ID")
    location_id: int = Field(..., description="Location ID")
    location: LocationInfo = Field(..., description="Location information")
    price_id: UUID = Field(..., description="Price ID")
    price: PriceInfo = Field(..., description="Price information")
    status: str = Field(..., description="Transaction status")
    qr_string: str = Field(..., description="QR code string for display")
    paid_at: Optional[datetime] = Field(None, description="Payment timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class TransactionListItem(BaseModel):
    """Schema for transaction list item"""
    id: int = Field(..., description="Transaction ID")
    external_id: str = Field(..., description="External transaction ID")
    location_id: int = Field(..., description="Location ID")
    location: LocationInfo = Field(..., description="Location information")
    price_id: UUID = Field(..., description="Price ID")
    price: PriceInfo = Field(..., description="Price information")
    status: str = Field(..., description="Transaction status")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# Webhook Schema
class XenditWebhookPayload(BaseModel):
    """Schema for Xendit webhook payload"""
    external_id: str = Field(..., description="External transaction ID")
    status: str = Field(..., description="Transaction status")
    xendit_id: str = Field(..., description="Xendit transaction ID")


class WebhookResponse(BaseModel):
    """Schema for webhook response"""
    message: str = Field(default="Transaction updated")


# Photo Upload Schemas
class PhotoUploadInfo(BaseModel):
    """Schema for individual photo upload info"""
    filename: str = Field(..., description="Original filename")
    url: str = Field(..., description="Cloudinary public URL")
    size: int = Field(..., description="File size in bytes")


class PhotoUploadResponse(BaseModel):
    """Schema for photo upload response"""
    uploaded_count: int = Field(..., description="Number of photos uploaded")
    folder_url: str = Field(..., description="Cloudinary folder URL for all photos")
    email_sent: bool = Field(..., description="Whether email was sent successfully")
    email_sent_at: Optional[datetime] = Field(None, description="Email sent timestamp")
    photos: List[PhotoUploadInfo] = Field(..., description="List of uploaded photos")


# Cleanup Schemas
class CleanupResponse(BaseModel):
    """Schema for cleanup maintenance response"""
    deleted_count: int = Field(..., description="Number of folders deleted")
    folders: List[str] = Field(..., description="List of deleted folder names (external_ids)")
    message: str = Field(..., description="Status message")


# Transaction List Response
class TransactionListMeta(BaseModel):
    """Schema for transaction list metadata"""
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")


class TransactionListResponse(BaseModel):
    """Schema for transaction list response"""
    meta: TransactionListMeta = Field(..., description="Pagination metadata")
    data: List[TransactionListItem] = Field(..., description="List of transactions")
