"""
Email Service - Send email notifications via SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from decimal import Decimal

from atams.logging import get_logger
from atams.exceptions import InternalServerException

logger = get_logger(__name__)


class EmailService:
    """Service for sending email notifications"""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str,
        use_ssl: bool = True,
        use_starttls: bool = False
    ):
        """
        Initialize Email service

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: From email address
            from_name: From name
            use_ssl: Use SSL/TLS connection
            use_starttls: Use STARTTLS
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_ssl = use_ssl
        self.use_starttls = use_starttls

        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates" / "emails"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        logger.info(f"Email service initialized with server: {smtp_server}:{smtp_port}")

    def _render_template(
        self,
        template_name: str,
        context: dict
    ) -> str:
        """
        Render Jinja2 template with context

        Args:
            template_name: Template filename
            context: Template context variables

        Returns:
            Rendered HTML string
        """
        try:
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**context)
            return html_content
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            raise InternalServerException(
                "Failed to render email template",
                details={"template": template_name, "error": str(e)}
            )

    def send_photobox_notification(
        self,
        to_email: str,
        external_id: str,
        folder_url: str,
        amount: Optional[Decimal] = None,
        paid_at: Optional[datetime] = None,
        send_invoice: bool = False
    ) -> bool:
        """
        Send photobox notification email (invoice + photos)

        Args:
            to_email: Recipient email address
            external_id: Transaction external ID
            folder_url: Cloudinary folder base URL
            amount: Transaction amount (for invoice)
            paid_at: Payment timestamp (for invoice)
            send_invoice: Whether to include invoice section

        Returns:
            True if email sent successfully

        Raises:
            InternalServerException: If email sending fails
        """
        try:
            # Calculate expiry date (14 days from now, at 00:00 WIB)
            # This matches the cleanup cron job schedule (daily at 00:00 WIB)
            expiry_date = (datetime.now() + timedelta(days=14)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            expiry_date_str = expiry_date.strftime("%d %B %Y")

            # Format paid_at timestamp
            paid_at_str = paid_at.strftime("%d %B %Y, %H:%M") if paid_at else "N/A"

            # Format amount (convert Decimal to float for template)
            amount_float = float(amount) if amount else 0.0

            # Prepare template context
            context = {
                "transaction_id": external_id,
                "amount": amount_float,
                "paid_at": paid_at_str,
                "folder_url": folder_url,
                "expiry_date": expiry_date_str,
                "send_invoice": send_invoice
            }

            # Render HTML template
            html_content = self._render_template("photobox_notification.html", context)

            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Foto Photobox Anda Sudah Siap! 📸" if not send_invoice else "Invoice & Foto Photobox Anda Sudah Siap! 📸"
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            if self.use_ssl:
                # Use SSL/TLS
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.username, self.password)
                    server.send_message(message)
            else:
                # Use STARTTLS or plain
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.use_starttls:
                        server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(message)

            logger.info(f"Email sent successfully to {to_email} for transaction {external_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise InternalServerException(
                "Failed to send email notification",
                details={"to_email": to_email, "error": str(e)}
            )
