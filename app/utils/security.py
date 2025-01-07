from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db_session
from fastapi import Request
from sqlalchemy.exc import SQLAlchemyError
from app.core.token_blacklist import is_token_blacklisted
from app.core.config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer()

'''
-----------------------------------------------------
|         User password hash function               |
-----------------------------------------------------
'''


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


'''
-----------------------------------------------------
|         Token generation for authentication       |
-----------------------------------------------------
'''


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + \
            timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

'''
-----------------------------------------------------
|                Decode JWT token                   |
-----------------------------------------------------
'''

def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

'''
-----------------------------------------------------
|         Token validation for authentication       |
-----------------------------------------------------
'''


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: AsyncSession = Depends(get_db_session)
):
    from app.api.auth.models import User
    token = credentials.credentials
    try:
        if is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been blacklisted",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="UserId not found in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        query = await session.execute(select(User).where(User.id == user_id))
        user = query.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except SQLAlchemyError as e:
        error_message = str(e).split("\n")[1] if len(
            str(e).split("\n")) > 1 else str(e)
        if "DETAIL:" in error_message:
            error_message = error_message.replace("DETAIL:", "").strip()
        raise HTTPException(status_code=500, detail=error_message)
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            headers={"WWW-Authenticate": "Bearer"},
        )


'''
-----------------------------------------------------
|        Enforce active status for users           |
-----------------------------------------------------
'''


async def get_current_active_user(request: Request, current_user=Depends(get_current_user), ):
    from app.api.auth.models import UserStatus
    # Enforce status checks for paused accounts based on the request method
    if current_user.status == UserStatus.PAUSED.value:
        if request.method not in ["GET", "OPTIONS", "HEAD"]:
            raise HTTPException(
                status_code=403,
                detail="Your account is paused. You can only view resources."
            )

    # new users with a pending status
    if current_user.status == UserStatus.PENDING.value:
        raise HTTPException(
            status_code=403,
            detail="Your account is pending confirmation."
        )

    if current_user.status == UserStatus.BLOCKED.value:
        raise HTTPException(
            status_code=403,
            detail="Your account is blocked."
        )
    return current_user


'''
-----------------------------------------------------
|        Enforce role-based access control          |
-----------------------------------------------------
'''


def get_current_active_user_with_roles(required_roles: list[str]):
    if "PUBLIC" in required_roles:
        async def allow_all_users():
            return True
        return allow_all_users
    else:
        async def _get_current_active_user_with_roles(current_user=Depends(get_current_active_user)):
            if current_user.role.name not in required_roles:  # Ensure `role` is eagerly loaded
                raise HTTPException(
                    status_code=403, detail="Not enough permissions"
                )
            return current_user
        return _get_current_active_user_with_roles
