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

    # API Base URL (for generating gallery links in emails)
    API_BASE_URL: str = "http://localhost:8000"  # Configure via .env for production

    # Xendit Configuration
    XENDIT_API_KEY: str = ""  # Configure via .env file
    XENDIT_WEBHOOK_URL: str = ""  # Webhook URL for Xendit callbacks (optional for testing)
    XENDIT_CALLBACK_TOKEN: str = ""  # Callback verification token from Xendit dashboard

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str = ""  # Cloudinary cloud name
    CLOUDINARY_API_KEY: str = ""  # Cloudinary API key
    CLOUDINARY_API_SECRET: str = ""  # Cloudinary API secret
    CLOUDINARY_FOLDER: str = "photobox"  # Base folder for uploads

    # Email Configuration
    MAIL_USERNAME: str = ""  # SMTP username
    MAIL_PASSWORD: str = ""  # SMTP password
    MAIL_FROM: str = ""  # From email address
    MAIL_FROM_NAME: str = "Photobox Service"  # From name
    MAIL_SERVER: str = ""  # SMTP server
    MAIL_PORT: int = 465  # SMTP port
    MAIL_SSL_TLS: bool = True  # Use SSL/TLS
    MAIL_STARTTLS: bool = False  # Use STARTTLS

    # Maintenance Configuration
    MAINTENANCE_TOKEN: str = ""  # Token for maintenance endpoints


settings = Settings()
