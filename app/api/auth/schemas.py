from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class RoleSchema(BaseModel):
    name: str = Field(..., description="Name of the role")
    description: Optional[str] = Field(None, description="Description of the role")


class UserCreateSchema(BaseModel):
    username: str = Field(..., description="Username of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    password: str = Field(..., min_length=8, description="Password for the user")
    role_id: str = Field(..., description="Role ID associated with the user")


class UserLoginSchema(BaseModel):
    username: str = Field(..., description="Username for login")
    password: str = Field(..., description="Password for login")


class UserResponseSchema(BaseModel):
    id: str = Field(..., description="Unique document ID for the user")
    username: str = Field(..., description="Username of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    status: str = Field(..., description="Current status of the user")
    created_at: datetime = Field(..., description="Timestamp of when the user was created")
    updated_at: datetime = Field(..., description="Timestamp of the last update to the user")
    role: RoleSchema = Field(..., description="Role details associated with the user")

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    detail: str = Field(..., description="Details or message about the token")
    access_token: str = Field(..., description="Access token for authentication")
    token_type: str = Field(..., description="Type of the token, e.g., Bearer")


class ResetTokenSchema(BaseModel):
    token: str = Field(..., description="Reset token for password reset")
    new_password: str = Field(..., min_length=8, description="New password for the user")
    confirm_password: str = Field(..., min_length=8, description="Confirmation of the new password")


class ChangePasswordSchema(BaseModel):
    current_password: str = Field(..., description="Current password of the user")
    new_password: str = Field(..., min_length=8, description="New password for the user")
    confirm_password: str = Field(..., min_length=8, description="Confirmation of the new password")
