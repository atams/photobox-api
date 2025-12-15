from atams import AtamsBaseSettings


class Settings(AtamsBaseSettings):
    """
    Application Settings

    Inherits from AtamsBaseSettings which includes:
    - DATABASE_URL (required)
    - ATLAS_SSO_URL, ATLAS_APP_CODE, ATLAS_ENCRYPTION_KEY, ATLAS_ENCRYPTION_IV
    - ENCRYPTION_ENABLED, ENCRYPTION_KEY, ENCRYPTION_IV (response encryption)
    - LOGGING_ENABLED, LOG_LEVEL, LOG_TO_FILE, LOG_FILE_PATH
    - CORS_ORIGINS, CORS_ALLOW_CREDENTIALS, CORS_ALLOW_METHODS, CORS_ALLOW_HEADERS
    - RATE_LIMIT_ENABLED, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
    - DEBUG

    All settings can be overridden via .env file or by redefining them here.
    """
    APP_NAME: str = "photobox_api"
    APP_VERSION: str = "1.0.0"

    # Xendit Configuration
    XENDIT_API_KEY: str = ""  # Configure via .env file
    XENDIT_WEBHOOK_URL: str = ""  # Webhook URL for Xendit callbacks (optional for testing)
    XENDIT_CALLBACK_TOKEN: str = ""  # TASK B: Callback verification token from Xendit dashboard


settings = Settings()
