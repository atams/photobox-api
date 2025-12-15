"""
Xendit Service - Integration with Xendit QRIS API
"""
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import base64
import httpx
from atams.logging import get_logger
from atams.exceptions import InternalServerException

logger = get_logger(__name__)


class XenditService:
    """Service for Xendit QRIS integration"""

    def __init__(self, api_key: str, base_url: str = "https://api.xendit.co"):
        """
        Initialize Xendit service

        Args:
            api_key: Xendit API key (secret key from dashboard)
            base_url: Xendit API base URL
        """
        self.api_key = api_key
        self.base_url = base_url

        # Encode API key to Base64 according to Xendit documentation
        # Format: {username}:{password} where username is API key and password is empty
        credentials = f"{api_key}:"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}"
        }

    async def create_qris(
        self,
        external_id: str,
        amount: Decimal,
        callback_url: str
    ) -> Dict[str, Any]:
        """
        Create QRIS payment request

        Args:
            external_id: Unique external ID
            amount: Payment amount
            callback_url: Webhook callback URL (required by Xendit)

        Returns:
            Dictionary containing qr_string and xendit_id

        Raises:
            InternalServerException: If API call fails
        """
        try:
            # TASK A: Calculate expiration time (15 minutes from now)
            # Using UTC to ensure consistency with Xendit's timezone expectations
            expiration_time = datetime.utcnow() + timedelta(minutes=15)
            # Format as ISO 8601 string as required by Xendit API
            expires_at = expiration_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

            # Build payload - callback_url is required by Xendit API
            payload = {
                "external_id": external_id,
                "type": "DYNAMIC",
                "amount": float(amount),
                "callback_url": callback_url,
                "expires_at": expires_at  # TASK A: Set QRIS expiration to 15 minutes
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/qr_codes",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"QRIS created successfully for external_id: {external_id}")
                    return {
                        "qr_string": data.get("qr_string"),
                        "xendit_id": data.get("id")
                    }
                else:
                    logger.error(f"Xendit API error: {response.status_code} - {response.text}")
                    raise InternalServerException(
                        "Failed to create QRIS payment",
                        details={"status_code": response.status_code, "response": response.text}
                    )

        except httpx.RequestError as e:
            logger.error(f"Xendit API request error: {str(e)}")
            raise InternalServerException(
                "Failed to connect to Xendit API",
                details={"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected error in create_qris: {str(e)}")
            raise InternalServerException(
                "Unexpected error creating QRIS",
                details={"error": str(e)}
            )

    async def get_qris_status(self, xendit_id: str) -> Dict[str, Any]:
        """
        Get QRIS payment status

        Args:
            xendit_id: Xendit QRIS ID

        Returns:
            Dictionary containing payment status

        Raises:
            InternalServerException: If API call fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/qr_codes/{xendit_id}",
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Xendit API error: {response.status_code} - {response.text}")
                    raise InternalServerException(
                        "Failed to get QRIS status",
                        details={"status_code": response.status_code}
                    )

        except httpx.RequestError as e:
            logger.error(f"Xendit API request error: {str(e)}")
            raise InternalServerException(
                "Failed to connect to Xendit API",
                details={"error": str(e)}
            )
