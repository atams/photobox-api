"""
Location Endpoints - API routes for locations

Protected by Atlas SSO - Admin only (role_level <= 10)
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from atams.db import get_db
from app.api.deps import require_auth, require_min_role_level
from app.services.location_service import LocationService
from app.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationUpdateResponse,
    LocationListResponse
)

router = APIRouter()
location_service = LocationService()


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_min_role_level(10))]
)
async def create_location(
    data: LocationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """
    Create a new location (Admin only - role_level <= 10)

    - **machine_code**: Unique machine code (required, max 50 chars)
    - **name**: Location name (required, max 100 chars)
    - **address**: Full address (optional)
    - **is_active**: Active status (optional, default: true)
    """
    return await location_service.create_location(db, data)


@router.get(
    "",
    response_model=LocationListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_min_role_level(10))]
)
async def get_locations(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number (minimum 1)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (1-100)"),
    search: Optional[str] = Query(None, description="Search text"),
    sort_by: str = Query("machine_code", description="Sort column (machine_code, name, address)"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """
    Get paginated list of locations (Admin only - role_level <= 10)

    **Query Parameters:**
    - **is_active**: Filter by active status (null = all, true = active, false = inactive)
    - **page**: Page number (minimum 1)
    - **limit**: Items per page (1-100)
    - **search**: Search in machine_code, name, or address
    - **sort_by**: Column to sort by (machine_code, name, address)
    - **sort_order**: Sort order (asc/desc)
    """
    return await location_service.get_location_list(
        db=db,
        is_active=is_active,
        page=page,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get(
    "/{id}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_min_role_level(10))]
)
async def get_location_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """
    Get location detail by ID (Admin only - role_level <= 10)

    - **id**: Location ID
    """
    return await location_service.get_location_detail(db, id)


@router.put(
    "/{id}",
    response_model=LocationUpdateResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_min_role_level(10))]
)
async def update_location(
    id: int,
    data: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """
    Update location (Admin only - role_level <= 10)

    - **id**: Location ID
    - **name**: Location name (optional, max 100 chars)
    - **address**: Full address (optional)
    - **is_active**: Active status (optional)

    **Note:** `machine_code` and `created_at` cannot be updated
    """
    return await location_service.update_location(db, id, data)
