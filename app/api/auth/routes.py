from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from .schemas import UserCreateSchema, TokenSchema, UserResponseSchema, UserLoginSchema, ResetTokenSchema, ChangePasswordSchema
from .services import AuthService
from fastapi import status
from app.utils.security import get_current_active_user_with_roles
from .configs import user_required_roles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import EmailStr
from fastapi import BackgroundTasks

router = APIRouter()

'''
-----------------------------------------------------
|                Me API Route                       |
-----------------------------------------------------
'''


@router.get("/me", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
async def me(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_active_user_with_roles(
        user_required_roles.get("me", [])))
):
    return current_user

'''
-----------------------------------------------------
|                Login API Route                    |
-----------------------------------------------------
'''


@router.post("/login", response_model=TokenSchema, status_code=status.HTTP_200_OK)
async def login(
    user: UserLoginSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_active_user_with_roles(
        user_required_roles.get("login", [])))
):
    return await AuthService(db).login_user(user.username, user.password)


'''
-----------------------------------------------------
|                Register API Route                 |
-----------------------------------------------------
'''


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user: UserCreateSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_active_user_with_roles(
        user_required_roles.get("register", [])))
):
    return await AuthService(db).register_user(user, background_tasks)

'''
-----------------------------------------------------
|                Verifty API Route                 |
-----------------------------------------------------
'''


@router.get("/verify/{token}", status_code=status.HTTP_200_OK)
async def verify(
    token: str,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_active_user_with_roles(
        user_required_roles.get("verify", [])))
):
    return await AuthService(db).verify_user(token)


'''
-----------------------------------------------------
|                Logout API Route                  |
-----------------------------------------------------
'''


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_active_user_with_roles(
        user_required_roles.get("logout", []))),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    return await AuthService(db).logout_user(credentials.credentials)


'''
-----------------------------------------------------
|              Forgot Password API Route            |
-----------------------------------------------------
'''


@router.get("/forgot-password/{email}", status_code=status.HTTP_200_OK)
async def forgot_password(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_active_user_with_roles(
        user_required_roles.get("forgot-password", [])))
):
    return await AuthService(db).forgot_password(email, background_tasks)

'''
-----------------------------------------------------
|            Reset Password API Route               |
-----------------------------------------------------
'''


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    data: ResetTokenSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_active_user_with_roles(
        user_required_roles.get("reset-password", [])))
):
    return await AuthService(db).reset_password(data)

'''
-----------------------------------------------------
|            Change Password API Route               |
-----------------------------------------------------
'''


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePasswordSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_active_user_with_roles(
        user_required_roles.get("change-password", [])))
):
    return await AuthService(db).change_password(data, current_user)
