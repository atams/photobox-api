from fastapi.responses import JSONResponse
from fastapi import HTTPException
from typing import Any, Union
from app.core.encryption import encryption
from app.core.config import settings
from atams.logging import get_logger

logger = get_logger(__name__)


def encrypt_response_if_enabled(data: Any) -> Union[Any, JSONResponse]:
    """
    Encrypt response data if encryption is enabled globally

    Args:
        data: Response data (Pydantic model or dict)

    Returns:
        JSONResponse with encrypted data if enabled, otherwise original data
    """
    # Check if encryption is enabled globally
    if not settings.ENCRYPTION_ENABLED:
        # Return original data if encryption is disabled
        return data  # Return Pydantic model as-is for proper OpenAPI documentation

    try:
        # Convert Pydantic model to dict if needed
        if hasattr(data, 'model_dump'):
            response_dict = data.model_dump(mode='json')  # Use mode='json' to serialize datetime properly
        elif hasattr(data, 'dict'):
            response_dict = data.dict()
        else:
            response_dict = data

        # Encrypt the data
        encrypted_payload = encryption.encrypt_data(response_dict)

        return JSONResponse(
            content={
                "data": encrypted_payload
            },
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        logger.error(f"Response encryption failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")


def maybe_encrypt_response(data: Any, force_encrypt: bool = False) -> JSONResponse:
    """
    Conditionally encrypt response based on global setting or force flag

    Args:
        data: Response data
        force_encrypt: Force encryption regardless of global setting

    Returns:
        JSONResponse (encrypted or normal)
    """
    if force_encrypt or settings.ENCRYPTION_ENABLED:
        return encrypt_response_if_enabled(data)

    # Return normal response
    if hasattr(data, 'model_dump') or hasattr(data, 'dict'):
        return data  # Let FastAPI handle Pydantic serialization
    return JSONResponse(content=data)
