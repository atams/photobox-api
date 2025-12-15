"""
Webhook Endpoints - API routes for webhooks
"""
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.orm import Session

from atams.db import get_db
from app.core.config import settings
from app.services.transaction_service import TransactionService
from app.schemas.transaction import XenditWebhookPayload, WebhookResponse

router = APIRouter()

# Initialize with Xendit API key from settings
transaction_service = TransactionService(xendit_api_key=getattr(settings, "XENDIT_API_KEY", ""))


@router.post("/xendit", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
async def xendit_webhook(
    request: Request,
    payload: XenditWebhookPayload,
    db: Session = Depends(get_db)
):
    """
    Xendit webhook endpoint

    Receives payment status updates from Xendit

    **Security:**
    - Verifies x-callback-token header to ensure request originates from Xendit
    - Token is verified against XENDIT_CALLBACK_TOKEN in environment variables

    **Payload:**
    - **external_id**: External transaction ID
    - **status**: Transaction status (PENDING, COMPLETED, FAILED, EXPIRED)
    - **xendit_id**: Xendit transaction ID
    - **paid_at**: Payment timestamp

    **Note:**
    - This endpoint is called by Xendit, not by users
    - For testing, send header: x-callback-token with value from .env
    """
    # TASK B: Verify webhook authenticity using callback token
    callback_token = request.headers.get("x-callback-token")

    if not callback_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-callback-token header"
        )

    # Compare with configured token
    expected_token = getattr(settings, "XENDIT_CALLBACK_TOKEN", "")
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="XENDIT_CALLBACK_TOKEN not configured"
        )

    if callback_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid callback token"
        )

    # TASK B: Token verified, proceed with webhook processing
    return await transaction_service.process_webhook(db, payload)
