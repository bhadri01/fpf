import asyncio
from pydantic import BaseModel, EmailStr
from typing import List
from fastapi import HTTPException, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
import os

# Email Configuration
APP_NAME = settings.app_name
EMAIL_ADDRESS = settings.email_address
EMAIL_PASSWORD = settings.email_password
SMTP_SERVER = settings.smtp_server
SMTP_PORT = int(settings.smtp_port)

# Ensure the template folder path is correct
template_folder_path = os.path.join(os.path.dirname(__file__), '../templates')

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL_ADDRESS,
    MAIL_PASSWORD=EMAIL_PASSWORD,
    MAIL_FROM=EMAIL_ADDRESS,
    MAIL_PORT=SMTP_PORT,
    MAIL_SERVER=SMTP_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    MAIL_FROM_NAME=APP_NAME,
    TEMPLATE_FOLDER=template_folder_path
)


async def send_email(email: List[str], subject: str, template_name: str, context: dict):
    try:
        message = MessageSchema(
            subject=subject,
            recipients=email,  # Ensure recipients is a list
            template_body=context,
            subtype="html"
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Usage example
# context = {
#     "app_name": APP_NAME,
#     "user_name": "example",
#     "verification_link": "https://example.com/login"
# }
# email = ["bhadri2002@gmail.com"]

# send_email(email, "Invitation request",
#             "invitation.html", context)
