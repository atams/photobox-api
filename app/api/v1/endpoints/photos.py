"""
Photo Upload Endpoints - API routes for photo upload and management
"""
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from atams.db import get_db
from app.core.config import settings
from app.services.transaction_service import TransactionService
from app.services.cloudinary_service import CloudinaryService
from app.services.email_service import EmailService
from app.schemas.transaction import PhotoUploadResponse

router = APIRouter()

# Initialize services
cloudinary_service = CloudinaryService(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    base_folder=settings.CLOUDINARY_FOLDER
)

email_service = EmailService(
    smtp_server=settings.MAIL_SERVER,
    smtp_port=settings.MAIL_PORT,
    username=settings.MAIL_USERNAME,
    password=settings.MAIL_PASSWORD,
    from_email=settings.MAIL_FROM,
    from_name=settings.MAIL_FROM_NAME,
    use_ssl=settings.MAIL_SSL_TLS,
    use_starttls=settings.MAIL_STARTTLS
)

transaction_service = TransactionService(
    xendit_api_key=settings.XENDIT_API_KEY,
    cloudinary_service=cloudinary_service,
    email_service=email_service
)


@router.post("/{external_id}/photos", response_model=PhotoUploadResponse, status_code=status.HTTP_200_OK)
async def upload_photos(
    external_id: str,
    files: List[UploadFile] = File(..., description="List of photo files to upload"),
    db: Session = Depends(get_db)
):
    """
    Upload photos for a transaction

    Uploads multiple photos to Cloudinary and sends email notification with download links.

    **Requirements:**
    - Transaction must exist
    - Transaction status must be COMPLETED
    - Email must not have been sent yet
    - Each file must be JPG/JPEG/PNG format
    - Each file must be ≤ 10MB

    **Process:**
    1. Validates transaction and files
    2. Uploads all photos to Cloudinary folder: photobox/{external_id}/
    3. Sends email with invoice (if requested) + photo download links
    4. Updates tr_email_sent_at timestamp

    **Returns:**
    - uploaded_count: Number of photos uploaded
    - folder_url: Cloudinary folder URL for all photos
    - email_sent: Whether email was sent successfully
    - email_sent_at: Timestamp of email sent
    - photos: List of uploaded photo details
    """
    result = await transaction_service.upload_photos(db, external_id, files)
    return result
