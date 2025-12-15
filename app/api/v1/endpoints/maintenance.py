"""
Maintenance Endpoints - API routes for system maintenance tasks
"""
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.orm import Session

from atams.db import get_db
from app.core.config import settings
from app.services.transaction_service import TransactionService
from app.services.cloudinary_service import CloudinaryService
from app.schemas.transaction import CleanupResponse

router = APIRouter()

# Initialize services
cloudinary_service = CloudinaryService(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    base_folder=settings.CLOUDINARY_FOLDER
)

transaction_service = TransactionService(
    xendit_api_key=settings.XENDIT_API_KEY,
    cloudinary_service=cloudinary_service
)


@router.delete("/cleanup-old-folders", response_model=CleanupResponse, status_code=status.HTTP_200_OK)
async def cleanup_old_folders(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Clean up Cloudinary folders older than 14 days

    This endpoint is designed to be called by GitHub Actions cron job.

    **Security:**
    - Requires X-Maintenance-Token header for authentication
    - Token must match MAINTENANCE_TOKEN from environment

    **Process:**
    1. Finds all transactions with email_sent_at > 14 days ago
    2. Deletes corresponding Cloudinary folders
    3. Returns list of deleted folders

    **Headers:**
    - X-Maintenance-Token: Maintenance authentication token

    **Returns:**
    - deleted_count: Number of folders successfully deleted
    - folders: List of deleted folder names (external_ids)
    - failed_count: Number of folders that failed to delete
    - failed_folders: List of folders that failed
    - message: Status message
    """
    # Verify maintenance token
    maintenance_token = request.headers.get("x-maintenance-token")

    if not maintenance_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Maintenance-Token header"
        )

    expected_token = settings.MAINTENANCE_TOKEN
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MAINTENANCE_TOKEN not configured"
        )

    if maintenance_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid maintenance token"
        )

    # Execute cleanup
    result = await transaction_service.cleanup_old_folders(db, days=14)
    return result
