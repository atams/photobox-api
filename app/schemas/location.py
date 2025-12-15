"""
Location Schemas - DTOs for Location API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Request Schemas
class LocationCreate(BaseModel):
    """Schema for creating a location"""
    machine_code: str = Field(..., max_length=50, description="Unique machine code (e.g., PB-JKT-001)")
    name: str = Field(..., max_length=100, description="Location name")
    address: Optional[str] = Field(None, description="Full address")
    is_active: bool = Field(True, description="Is location active")


class LocationUpdate(BaseModel):
    """Schema for updating a location"""
    name: Optional[str] = Field(None, max_length=100, description="Location name")
    address: Optional[str] = Field(None, description="Full address")
    is_active: Optional[bool] = Field(None, description="Is location active")


# Response Schemas
class LocationResponse(BaseModel):
    """Schema for location detail response"""
    id: int = Field(..., description="Location ID")
    machine_code: str = Field(..., description="Machine code")
    name: str = Field(..., description="Location name")
    address: Optional[str] = Field(None, description="Address")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class LocationListItem(BaseModel):
    """Schema for location list item"""
    id: int = Field(..., description="Location ID")
    machine_code: str = Field(..., description="Machine code")
    name: str = Field(..., description="Location name")
    address: Optional[str] = Field(None, description="Address")
    is_active: bool = Field(..., description="Active status")

    class Config:
        from_attributes = True


class LocationUpdateResponse(BaseModel):
    """Schema for location update response"""
    message: str = Field(default="Location updated successfully")
