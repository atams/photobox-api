from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict

from atams.db import get_db
from app.services.transaction_service import TransactionService
from app.services.cloudinary_service import CloudinaryService
from app.core.config import settings
from atams.exceptions import NotFoundException

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/{external_id}", response_class=HTMLResponse)
async def view_photo_gallery(
    request: Request,
    external_id: str,
    db: Session = Depends(get_db)
):
    """
    Display photo gallery for a transaction.

    This endpoint renders an HTML page showing all photos uploaded for a transaction.
    Users can view and download individual photos or all photos at once.

    Args:
        external_id: Transaction external ID

    Returns:
        HTMLResponse: Rendered photo gallery page

    Raises:
        NotFoundException: If transaction not found or no photos uploaded
    """
    # Initialize services
    cloudinary_service = CloudinaryService(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        base_folder=settings.CLOUDINARY_FOLDER
    )

    # Get transaction repository
    from app.repositories.transaction_repository import TransactionRepository
    transaction_repository = TransactionRepository()

    # Get transaction to verify it exists
    transaction = transaction_repository.get_by_external_id(db, external_id)
    if not transaction:
        raise NotFoundException(f"Transaction {external_id} not found")

    # Check if photos have been uploaded (email_sent_at should be set after upload)
    if not transaction.tr_email_sent_at:
        raise NotFoundException(f"No photos found for transaction {external_id}")

    # Get all photos from Cloudinary folder
    try:
        photo_urls = cloudinary_service.list_folder_photos(external_id)

        if not photo_urls:
            raise NotFoundException(f"No photos found for transaction {external_id}")

        # Prepare photo data
        photos: List[Dict[str, str]] = []
        for url in photo_urls:
            photos.append({
                "url": url
            })

        # Calculate expiry date (14 days from email sent, at 00:00 WIB on that day)
        # This matches the cleanup cron job schedule (daily at 00:00 WIB)
        expiry_date = None
        if transaction.tr_email_sent_at:
            # Add 14 days and set time to 00:00 (midnight)
            expiry_datetime = (transaction.tr_email_sent_at + timedelta(days=14)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            expiry_date = expiry_datetime.strftime("%d %B %Y, %H:%M WIB")

        # Render template
        return templates.TemplateResponse(
            "photo_gallery.html",
            {
                "request": request,
                "external_id": external_id,
                "photos": photos,
                "photo_count": len(photos),
                "expiry_date": expiry_date
            }
        )

    except Exception as e:
        raise NotFoundException(f"Error loading photos: {str(e)}")
