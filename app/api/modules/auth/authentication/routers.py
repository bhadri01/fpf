from uuid import UUID
from .schemas import AccessTokenResponseSchema, OTPSetupSchema, OTPVerificationSchema, RefreshTokenSchema, Setup2FASchema, TokenSchema, TwoFactorAuthSchema, UserLoginSchema, ResetTokenSchema, ChangePasswordSchema
from app.api.modules.auth.users.schemas import UserCreate, UserResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.database.db import get_read_session, get_write_session
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks
from .services import AuthService
from pydantic import EmailStr
from fastapi import Request
from fastapi import status

router = APIRouter()

'''
=====================================================
# Me API Route
=====================================================
'''


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def me(request: Request):
    if hasattr(request.state, 'user'):
        return request.state.user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authenticated")

'''
=====================================================
# Login API Route
=====================================================
'''


@router.post("/login", response_model=TokenSchema | TwoFactorAuthSchema, status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def login(
    request: Request,
    user: UserLoginSchema,
    db: AsyncSession = Depends(get_read_session),
):
    return await AuthService(db).login_user(user)


'''
=====================================================
# Register API Route
=====================================================
'''


@router.post("/register", status_code=status.HTTP_201_CREATED, name="Auth", tags=["Auth"])
async def register(
    request: Request,
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_write_session),
):
    return await AuthService(db).register_user(user, background_tasks)

'''
=====================================================
# Verifty API Route
=====================================================
'''


@router.get("/verify/{token}", status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def verify(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_write_session),
):
    return await AuthService(db).verify_user(token)

'''
=====================================================
# Resend Verify Token
=====================================================
'''


@router.get("/resend-verify-token/{email}", status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def resend_verify_token(
    request: Request,
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_read_session),
):
    return await AuthService(db).resend_verify_token(email, background_tasks)

'''
=====================================================
# Logout API Route
=====================================================
'''


@router.post("/logout", status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_write_session),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    return await AuthService(db).logout_user(credentials.credentials)


'''
=====================================================
# Forgot Password API Route
=====================================================
'''


@router.post("/forgot-password/{email}", status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def forgot_password(
    request: Request,
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_write_session),
):
    return await AuthService(db).forgot_password(email, background_tasks)

'''
=====================================================
# Reset Password API Route
=====================================================
'''


@router.post("/reset-password", status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def reset_password(
    request: Request,
    data: ResetTokenSchema,
    db: AsyncSession = Depends(get_write_session),
):
    return await AuthService(db).reset_password(data)

'''
=====================================================
# Change Password API Route
=====================================================
'''


@router.post("/change-password", status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def change_password(
    request: Request,
    data: ChangePasswordSchema,
    db: AsyncSession = Depends(get_write_session),
):
    return await AuthService(db).change_password(data, request.state.user)


'''
=====================================================
# Check Username Availability Route
=====================================================
'''


@router.get("/check-username/{username}", status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def check_username(
    request: Request,
    username: str,
    db: AsyncSession = Depends(get_read_session),
):
    return await AuthService(db).check_username(username)

'''
=====================================================
# Check Email Availability Route
=====================================================
'''


@router.get("/check-email/{email}", status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def check_email(
    request: Request,
    email: EmailStr,
    db: AsyncSession = Depends(get_read_session),
):
    return await AuthService(db).check_email(email)

'''
=====================================================
# Refresh Token Route
=====================================================
'''


@router.post("/refresh-token", response_model=AccessTokenResponseSchema, status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def refresh_token(
    request: Request,
    refresh_token: RefreshTokenSchema,
    db: AsyncSession = Depends(get_write_session),
):
    return await AuthService(db).refresh_token(refresh_token)

'''
=====================================================
# 2FA Setup Route
=====================================================
'''


@router.get("/2fa-setup", response_model=Setup2FASchema, status_code=status.HTTP_200_OK, name="Auth-2FA", tags=["Auth-2FA"])
async def two_factor_setup(
    request: Request,
    db: AsyncSession = Depends(get_write_session),
):
    if hasattr(request.state, 'user'):
        return await AuthService(db).two_factor_setup(request.state.user)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authenticated")

'''
=====================================================
# 2FA Setup Verify Route
=====================================================
'''


@router.post("/2fa-verify-setup", status_code=status.HTTP_200_OK, name="Auth-2FA", tags=["Auth-2FA"])
async def two_factor_verify(
    request: Request,
    data: OTPSetupSchema,
    db: AsyncSession = Depends(get_write_session),
):
    if hasattr(request.state, 'user'):
        return await AuthService(db).two_factor_verify_setup(request.state.user, data)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authenticated")

'''
=====================================================
# 2FA TOTP Verify Route
=====================================================
'''


@router.post("/2fa-verify", response_model=TokenSchema, status_code=status.HTTP_200_OK, name="Auth-2FA", tags=["Auth-2FA"])
async def two_factor_verify(
    request: Request,
    data: OTPVerificationSchema,
    db: AsyncSession = Depends(get_write_session),
):
    return await AuthService(db).two_factor_verify(data)

'''
=====================================================
# 2FA Disable Route
=====================================================
'''


@router.get("/2fa-disable", status_code=status.HTTP_200_OK, name="Auth-2FA", tags=["Auth-2FA"])
async def two_factor_disable(
    request: Request,
    db: AsyncSession = Depends(get_write_session),
):
    if hasattr(request.state, 'user'):
        return await AuthService(db).two_factor_disable(request.state.user)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authenticated")


'''
=====================================================
# Create Api-key Route
=====================================================
'''


@router.post("/create-api-key", status_code=status.HTTP_201_CREATED, name="Api-key", tags=["Api-key"])
async def create_api_key(
    request: Request,
    db: AsyncSession = Depends(get_write_session),
):
    if hasattr(request.state, 'user'):
        return await AuthService(db).create_api_key(request.state.user)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authenticated")

'''
=====================================================
# Remove Api-key Route
=====================================================
'''


@router.delete("/remove-api-key/{key}", status_code=status.HTTP_200_OK, name="Api-key", tags=["Api-key"])
async def remove_api_key(
    request: Request,
    key: str,
    db: AsyncSession = Depends(get_write_session),
):
    if hasattr(request.state, 'user'):
        return await AuthService(db).remove_api_key(request.state.user, key)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authenticated")

'''
=====================================================
# Login Redirect API Route
=====================================================
'''


@router.get("/login-redirect", status_code=status.HTTP_200_OK, name="Auth", tags=["Auth"])
async def login_redirect(
    request: Request,
    db: AsyncSession = Depends(get_read_session),
):
    if hasattr(request.state, 'user'):
        return await AuthService(db).login_redirect(request.state.user)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authenticated")
