from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.modules.auth.users.models import User, UserStatus
from app.api.modules.auth.authentication.models import APIKey
from app.middlewares.middleware_response import json_response_with_cors
from app.utils.security import SECRET_KEY, ALGORITHM, hash_key
from logs.logging import logger
from app.utils.token_blacklist import is_token_blacklisted
from app.core.database.db import get_read_session
from jose import JWTError, jwt
from app.core.redis import redis_cache
from app.core.config import settings
import time
import re

# Determine if running in production
ENV = settings.environment

'''
=====================================================
# Middleware for authenticating users via JWT or API Key.
=====================================================
'''
class PermissionMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        start_time = time.perf_counter()

        # Allow OPTIONS requests (CORS support)
        def log_and_return_response(response):
            response_time = (time.perf_counter() - start_time) * 1000
            response.headers["X-Response-Time"] = f"{response_time:.2f} ms"
            logger.info(
                f"Received request: {method} {path} - Response status: {response.status_code}, Time taken: {response_time:.2f} ms")
            return response

        if method == "OPTIONS":
            response = await call_next(request)
            return log_and_return_response(response)

        # Allow access to admin endpoints in development
        if path.startswith("/admin") or path.startswith("/public"):
            response = await call_next(request)
            return log_and_return_response(response)

        # Allow access to documentation and OpenAPI schema in development
        if ENV == "development" and path.startswith(("/docs", "/redoc", "/openapi.json", "/favicon.ico")):
            response = await call_next(request)
            return log_and_return_response(response)

        # Allow access to public endpoints or PUBLIC role (No authentication required)
        if await self.check_permission("PUBLIC", path, method):
            response = await call_next(request)
            return log_and_return_response(response)

        # Try to authenticate via API Key
        user, error_response = await self.authenticate_api_key(request)
        if not user:
            # Fallback to JWT authentication
            user, error_response = await self.authenticate_user(request)

        if error_response:
            response = error_response
            return log_and_return_response(response)

        # Attach user object to request
        request.state.user = user

        # Check user role permissions
        if await self.check_permission(user.role.name, path, method):
            response = await call_next(request)
        else:
            response = json_response_with_cors(
                content={"detail": "You do not have access to this resource"},
                status_code=status.HTTP_403_FORBIDDEN
            )

        return log_and_return_response(response)

    '''
    =====================================================
    # Authenticate user using API Key.
    =====================================================
    '''
    async def authenticate_api_key(self, request: Request):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return None, None  # No API key provided, continue to JWT authentication

        async for session in get_read_session():
            query = await session.execute(
                select(APIKey).where(APIKey.key == hash_key(api_key)).options(
                    selectinload(APIKey.user))
            )
            api_key_entry = query.scalar_one_or_none()

            if not api_key_entry:
                return None, json_response_with_cors(
                    content={"detail": "Invalid API Key"},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            return api_key_entry.user, None  # API Key valid, return user

    '''
    =====================================================
    # Authenticate user using JWT token.
    =====================================================
    '''
    async def authenticate_user(self, request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None, json_response_with_cors(
                content={"detail": "Missing authentication token"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
        except ValueError:
            return None, json_response_with_cors(
                content={"detail": "Invalid authentication header format"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Check if token is blacklisted
        if is_token_blacklisted(token):
            return None, json_response_with_cors(
                content={"detail": "Token has been blacklisted"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            return None, json_response_with_cors(
                content={"detail": "Invalid or expired token"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        user_id = payload.get("id")
        token_type = payload.get("type")

        if token_type != "access" or not user_id:
            return None, json_response_with_cors(
                content={"detail": "Invalid token type"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Fetch user from DB
        async for session in get_read_session():
            query = await session.execute(
                select(User).where(User.id == user_id).options(
                    selectinload(User.role))
            )
            user = query.scalar_one_or_none()
            if not user:
                return None, json_response_with_cors(
                    content={"detail": "User not found"},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            # Verify user status
            error_response = self.verify_user_status(user, request)
            if error_response:
                return None, error_response

            return user, None

    '''
    =====================================================
    # Verify user status before allowing access.
    =====================================================
    '''
    def verify_user_status(self, user: User, request: Request):
        if user.status == UserStatus.PAUSED.value and request.method not in ["GET", "OPTIONS", "HEAD"]:
            return json_response_with_cors(
                content={
                    "detail": "Your account is currently paused. You are only permitted to view resources."},
                status_code=status.HTTP_403_FORBIDDEN
            )

        if user.status == UserStatus.PENDING.value:
            return json_response_with_cors(
                content={
                    "detail": "Your account is pending confirmation. Please verify your email address to activate your account."},
                status_code=status.HTTP_403_FORBIDDEN
            )

        if user.status == UserStatus.BLOCKED.value:
            return json_response_with_cors(
                content={
                    "detail": "Your account has been blocked. Please contact support for further assistance."},
                status_code=status.HTTP_403_FORBIDDEN
            )

        return None

    '''
    =====================================================
    # Check if a role has permission to access a route.
    =====================================================
    '''
    async def check_permission(self, role: str, path: str, method: str):
        permission_data = await redis_cache.get("permission_cache")

        if not permission_data or role not in permission_data:
            return False

        for public_path in permission_data[role]:
            pattern = "^" + self.path_to_regex(public_path) + "$"
            if re.match(pattern, path) and method in permission_data[role][public_path]:
                return True

        return False  # Deny access if no match

    '''
    =====================================================
    # Convert API path parameters to regex patterns.
    =====================================================
    '''
    def path_to_regex(self, path: str):
        path = re.sub(r"\{[^/:]+\}", r"[^/]+", path)
        path = re.sub(r"\{[^/:]+:path\}", r".+", path)
        return path
