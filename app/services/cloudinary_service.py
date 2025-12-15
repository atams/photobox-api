"""
Cloudinary Service - Integration with Cloudinary for photo storage
"""
from typing import List, Dict, Any
import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile
from atams.logging import get_logger
from atams.exceptions import InternalServerException, BadRequestException

logger = get_logger(__name__)

# Allowed image formats
ALLOWED_FORMATS = {"jpg", "jpeg", "png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes


class CloudinaryService:
    """Service for Cloudinary photo upload and management"""

    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
        base_folder: str = "photobox"
    ):
        """
        Initialize Cloudinary service

        Args:
            cloud_name: Cloudinary cloud name
            api_key: Cloudinary API key
            api_secret: Cloudinary API secret
            base_folder: Base folder for uploads (default: photobox)
        """
        self.base_folder = base_folder

        # Configure Cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )

        logger.info(f"Cloudinary service initialized with cloud: {cloud_name}")

    def _validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file

        Args:
            file: File to validate

        Raises:
            BadRequestException: If file is invalid
        """
        # Check file extension
        filename_lower = file.filename.lower() if file.filename else ""
        file_ext = filename_lower.split(".")[-1] if "." in filename_lower else ""

        if file_ext not in ALLOWED_FORMATS:
            raise BadRequestException(
                f"File '{file.filename}' has invalid format. Allowed: JPG, JPEG, PNG",
                details={"filename": file.filename, "format": file_ext}
            )

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to start

        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            raise BadRequestException(
                f"File '{file.filename}' exceeds maximum size of 10MB (size: {size_mb:.2f}MB)",
                details={"filename": file.filename, "size": file_size, "max_size": MAX_FILE_SIZE}
            )

        logger.debug(f"File validated: {file.filename} ({file_size} bytes)")

    async def upload_photos(
        self,
        external_id: str,
        files: List[UploadFile]
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple photos to Cloudinary folder

        Args:
            external_id: Transaction external ID (used as folder name)
            files: List of files to upload

        Returns:
            List of uploaded photo information

        Raises:
            BadRequestException: If file validation fails
            InternalServerException: If upload fails
        """
        if not files:
            raise BadRequestException("No files provided for upload")

        uploaded_photos = []
        folder_path = f"{self.base_folder}/{external_id}"

        logger.info(f"Starting upload of {len(files)} photos to folder: {folder_path}")

        for idx, file in enumerate(files, start=1):
            try:
                # Validate file
                self._validate_file(file)

                # Read file content
                file_content = await file.read()

                # Generate unique public_id for each file
                # Format: photo_1, photo_2, photo_3, etc.
                public_id = f"photo_{idx}"

                # Upload to Cloudinary
                result = cloudinary.uploader.upload(
                    file_content,
                    folder=folder_path,
                    public_id=public_id,
                    resource_type="image",
                    overwrite=False
                )

                # Get file size
                file.file.seek(0, 2)
                file_size = file.file.tell()

                uploaded_photos.append({
                    "filename": file.filename,
                    "url": result.get("secure_url"),
                    "size": file_size
                })

                logger.info(f"Successfully uploaded: {file.filename} to {folder_path}")

            except BadRequestException:
                # Re-raise validation errors
                raise
            except Exception as e:
                logger.error(f"Failed to upload {file.filename}: {str(e)}")
                raise InternalServerException(
                    f"Failed to upload photo: {file.filename}",
                    details={"error": str(e), "filename": file.filename}
                )
            finally:
                # Reset file pointer
                await file.seek(0)

        logger.info(f"Successfully uploaded {len(uploaded_photos)} photos to {folder_path}")
        return uploaded_photos

    def list_folder_photos(self, external_id: str) -> List[str]:
        """
        List all photo URLs in a transaction folder

        Args:
            external_id: Transaction external ID

        Returns:
            List of photo URLs

        Raises:
            InternalServerException: If listing fails
        """
        folder_path = f"{self.base_folder}/{external_id}"

        try:
            # Get all resources in folder
            result = cloudinary.api.resources(
                type="upload",
                prefix=folder_path,
                max_results=500  # Max photos per transaction
            )

            resources = result.get("resources", [])

            # Extract secure URLs
            photo_urls = [resource.get("secure_url") for resource in resources]

            logger.info(f"Found {len(photo_urls)} photos in folder: {folder_path}")
            return photo_urls

        except Exception as e:
            logger.error(f"Failed to list photos in folder {folder_path}: {str(e)}")
            raise InternalServerException(
                f"Failed to list photos in folder: {folder_path}",
                details={"error": str(e), "folder": folder_path}
            )

    def get_folder_url(self, external_id: str) -> str:
        """
        Get public URL for folder (base path for photos)

        Args:
            external_id: Transaction external ID

        Returns:
            Base URL for folder - user will receive individual photo URLs in email
        """
        cloud_name = cloudinary.config().cloud_name
        folder_path = f"{self.base_folder}/{external_id}"

        # Return base folder path (photos will be sent individually in email)
        folder_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{folder_path}"

        logger.debug(f"Generated folder URL: {folder_url}")
        return folder_url

    def delete_folder(self, external_id: str) -> bool:
        """
        Delete folder and all its contents from Cloudinary

        Args:
            external_id: Transaction external ID

        Returns:
            True if deletion successful, False otherwise

        Raises:
            InternalServerException: If deletion fails
        """
        folder_path = f"{self.base_folder}/{external_id}"

        try:
            # Delete all resources in folder
            result = cloudinary.api.delete_resources_by_prefix(
                prefix=folder_path,
                resource_type="image"
            )

            deleted_count = len(result.get("deleted", {}))
            logger.info(f"Deleted {deleted_count} photos from folder: {folder_path}")

            # Delete the folder itself
            try:
                cloudinary.api.delete_folder(folder_path)
                logger.info(f"Deleted folder: {folder_path}")
            except Exception as e:
                # Folder deletion might fail if not empty or doesn't exist, but that's okay
                logger.warning(f"Could not delete folder {folder_path}: {str(e)}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete folder {folder_path}: {str(e)}")
            raise InternalServerException(
                f"Failed to delete folder: {folder_path}",
                details={"error": str(e), "folder": folder_path}
            )
