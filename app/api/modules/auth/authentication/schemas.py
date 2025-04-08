from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional, List
'''
=====================================================
# User Login Schema
=====================================================
'''
class UserLoginSchema(BaseModel):
    identifier: str = Field(..., description="Username / email for login")
    password: str = Field(..., description="Password for login")

'''
=====================================================
# User Register Schema
=====================================================
'''
class UserRegisterCreate(BaseModel):
    username: str = Field(..., description="Username of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    password: str = Field(..., description="Password for the user")

'''
=====================================================
# Token Schema
=====================================================
'''
class TokenSchema(BaseModel):
    detail: str = Field(..., description="Details or message about the token")
    access_token: str = Field(..., description="Access token for authentication")
    refresh_token: str = Field(..., description="Refresh token for authentication")
    token_type: str = Field(..., description="Type of the token, e.g., Bearer")

'''
=====================================================
# Access Token Response Schema
=====================================================
'''
class AccessTokenResponseSchema(BaseModel):
    access_token: str = Field(..., description="Access token for authentication")
    token_type: str = Field(..., description="Type of the token, e.g., Bearer")

'''
=====================================================
# Reset Token Schema
=====================================================
'''
class ResetTokenSchema(BaseModel):
    token: str = Field(..., description="Reset token for password reset")
    new_password: str = Field(..., description="New password for the user")
    confirm_password: str = Field(..., description="Confirmation of the new password")

'''
=====================================================
# Change Password Schema
=====================================================
'''
class ChangePasswordSchema(BaseModel):
    current_password: str = Field(..., description="Current password of the user")
    new_password: str = Field(..., description="New password for the user")
    confirm_password: str = Field(..., description="Confirmation of the new password")

'''
=====================================================
# Setup 2FA Schema
=====================================================
'''
class Setup2FASchema(BaseModel):
    qr_code: str = Field(..., description="QR code for the OTP")
    secret: str = Field(..., description="Secret key associated with the OTP")

'''
=====================================================
# OTP Setup Schema
=====================================================
'''
class OTPSetupSchema(BaseModel):
    otp_code: str = Field(..., description="One-time password code for verification")
    secret: str = Field(..., description="Secret key associated with the OTP")

'''
=====================================================
# User ID and Email Schema
=====================================================
'''
class UserIdAndEmailSchema(BaseModel):
    id: UUID = Field(..., description="User ID associated with the token")
    email: str = Field(..., description="Email address associated with the token")

'''
=====================================================
# Two-Factor Authentication Schema
=====================================================
'''
class TwoFactorAuthSchema(BaseModel):
    detail: str = Field(..., description="Details or message about the token")
    required_2fa: bool = Field(..., description="Indicates if two-factor authentication is required")
    user: UserIdAndEmailSchema = Field(..., description="User ID and email associated with the token")

'''
=====================================================
# OTP Verification Schema
=====================================================
'''
class OTPVerificationSchema(BaseModel):
    otp_code: str = Field(..., description="One-time password code for verification")
    user_id: UUID = Field(..., description="User ID associated with the OTP")

'''
=====================================================
# Refresh Token Schema
=====================================================
'''
class RefreshTokenSchema(BaseModel):
    token: str = Field(..., description="Refresh token for authentication")


class InvitedUserRegisterCreate(BaseModel):
    token: str = Field(..., description="token for authentication")
    username: str = Field(..., description="Username of the user")
    password: str = Field(..., description="Password for the user")
    
'''
=====================================================
# Export Request Schema
=====================================================
'''

class ExportRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to export")
