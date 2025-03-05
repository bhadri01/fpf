import os
from typing import List
from fastapi import HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings  # Import the settings object
from logs.logging import logger

'''
=====================================================
# ✅ FastAPI Mail Configuration
=====================================================
'''
template_folder_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), settings.template_folder)
)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=settings.use_credentials,
    VALIDATE_CERTS=settings.validate_certs,
    MAIL_FROM_NAME=settings.mail_from_name,
    TEMPLATE_FOLDER=template_folder_path
)

'''
=====================================================
# ✅ Send Email Function
=====================================================
'''
async def send_email(email: List[str], subject: str, template_name: str, context: dict):
    """
    Sends an email using the configured SMTP settings.

    Args:
        email (List[str]): List of recipient email addresses.
        subject (str): Email subject.
        template_name (str): The HTML template file name.
        context (dict): Context dictionary for template rendering.

    Raises:
        HTTPException: If an error occurs during email sending.
    """
    if not isinstance(email, list) or not all(isinstance(e, str) for e in email):
        raise ValueError("email parameter must be a list of strings")

    try:
        message = MessageSchema(
            subject=subject,
            recipients=email,
            template_body=context,
            subtype="html"
        )

        fm = FastMail(conf)  # ✅ Removed 'async with'
        await fm.send_message(message, template_name=template_name)

        logger.info("✅ Email sent successfully")

    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Email sending failed: {str(e)}")
