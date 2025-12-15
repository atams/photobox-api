"""
Photos List Endpoint - Get photos for a transaction (for frontend gallery)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Dict

from atams.db import get_db
from app.repositories.transaction_repository import TransactionRepository
from app.services.cloudinary_service import CloudinaryService
from app.core.config import settings
from atams.exceptions import NotFoundException

router = APIRouter()


@router.get("/{external_id}/photos")
async def get_transaction_photos(
    external_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all photos for a transaction.

    This endpoint is called by the frontend gallery page to fetch
    the list of photos for display.

    Args:
        external_id: Transaction external ID

    Returns:
        JSON with transaction info and list of photo URLs

    Raises:
        NotFoundException: If transaction not found or no photos uploaded
    """
    # Get transaction repository
    transaction_repository = TransactionRepository()

    # Get transaction to verify it exists
    transaction = transaction_repository.get_by_external_id(db, external_id)
    if not transaction:
        raise NotFoundException(
            "Transaction not found",
            details={"external_id": external_id}
        )

    # Check if photos have been uploaded (email_sent_at should be set after upload)
    if not transaction.tr_email_sent_at:
        raise NotFoundException(
            "No photos found for transaction",
            details={"external_id": external_id}
        )

    # Initialize Cloudinary service
    cloudinary_service = CloudinaryService(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        base_folder=settings.CLOUDINARY_FOLDER
    )

    # Get all photos from Cloudinary folder
    try:
        photo_urls = cloudinary_service.list_folder_photos(external_id)

        if not photo_urls:
            raise NotFoundException(
                "No photos found for transaction",
                details={"external_id": external_id}
            )

        # Prepare photo data with thumbnail URLs
        photos: List[Dict[str, str]] = []
        for url in photo_urls:
            # Generate thumbnail URL (Cloudinary transformation)
            # c_fill,h_300,w_300 = crop to fill 300x300
            thumbnail_url = url.replace("/upload/", "/upload/c_fill,h_300,w_300/")

            photos.append({
                "url": url,
                "thumbnail_url": thumbnail_url
            })

        # Calculate expiry date (14 days from email sent, at 00:00 WIB)
        expiry_datetime = (transaction.tr_email_sent_at + timedelta(days=14)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Return response
        return {
            "external_id": external_id,
            "photo_count": len(photos),
            "email_sent_at": transaction.tr_email_sent_at.isoformat(),
            "expiry_date": expiry_datetime.isoformat(),
            "photos": photos
        }

    except NotFoundException:
        # Re-raise NotFoundException
        raise
    except Exception as e:
        raise NotFoundException(
            f"Error loading photos: {str(e)}",
            details={"external_id": external_id, "error": str(e)}
        )
