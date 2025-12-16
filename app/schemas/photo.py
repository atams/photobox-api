"""
Photo Schemas - DTOs for Photo API
"""
from pydantic import BaseModel, Field
from typing import List


class PhotoItem(BaseModel):
    """Schema for individual photo item"""
    url: str = Field(..., description="Photo URL")


class PhotosListResponse(BaseModel):
    """Schema for photos list response"""
    external_id: str = Field(..., description="Transaction external ID")
    photo_count: int = Field(..., description="Total number of photos")
    email_sent_at: str = Field(..., description="Email sent timestamp (ISO format)")
    expiry_date: str = Field(..., description="Photos expiry date (ISO format)")
    photos: List[PhotoItem] = Field(..., description="List of photo URLs")
