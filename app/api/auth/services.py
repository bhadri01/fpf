from sqlalchemy.ext.asyncio import AsyncSession
from .models import User
from app.utils.security import verify_password, create_access_token, decode_token, get_password_hash
from fastapi import HTTPException
from .schemas import UserCreateSchema, ResetTokenSchema, ChangePasswordSchema
from sqlalchemy.future import select
from datetime import timedelta, datetime, UTC
from app.core.token_blacklist import add_token_to_blacklist, is_token_blacklisted
from pydantic import EmailStr
from app.utils.email_service import send_email
from fastapi import BackgroundTasks
from app.core.config import settings


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Retrieve the current authenticated user
    async def get_me(self):
        try:
            query = select(User).where(User.id == "1")
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Authenticate user and return access token
    async def login_user(self, username: str, password: str):
        try:
            query = select(User).where(User.username == username)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            if not user or not verify_password(password, user._password):
                raise HTTPException(
                    status_code=401, detail="Invalid credentials")
            if user.status == "blocked":
                raise HTTPException(
                    status_code=403, detail="Your account is blocked. Contact the admin")
            token = create_access_token(data={"id": str(
                user.id), "type": "access"}, expires_delta=timedelta(days=1))
            return {"detail": f"Welcome, {user.username}", "access_token": token, "token_type": "bearer"}
        except HTTPException as error:
            raise error
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Register a new user and send verification email
    async def register_user(self, user: UserCreateSchema, background_tasks: BackgroundTasks):
        try:
            user = User(**user.model_dump())
            existing_user_query = select(User).where(User.username == user.username)
            existing_user_result = await self.db.execute(existing_user_query)
            existing_user = existing_user_result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")

            existing_email_query = select(User).where(User.email == user.email)
            existing_email_result = await self.db.execute(existing_email_query)
            existing_email = existing_email_result.scalar_one_or_none()
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already exists")
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return_token = create_access_token(data={"id": str(
                user.id), "type": "verify_user"}, expires_delta=timedelta(days=1))
            # Send email with password reset link
            context = {
                "app_name": settings.app_name,
                "user_name": user.username,
                "verification_link": f"http://localhost:8000/verify?token={return_token}"
            }
            email_list = [user.email]
            background_tasks.add_task(
                send_email, email_list, "Account Verification", "verification.html", context)
            return {"detail": "User registered successfully. Verification link sent to your email"}
        except HTTPException as error:
            raise error
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Verify user account using token
    async def verify_user(self, token: str):
        try:
            if is_token_blacklisted(token):
                raise HTTPException(
                    status_code=400, detail="Token has been blacklisted")
            payload = decode_token(token)
            query = select(User).where(User.id == payload.get("id"))
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if payload["type"] != "verify_user":
                raise HTTPException(
                    status_code=400, detail="Invalid token")
            if datetime.now(UTC) > datetime.fromtimestamp(payload.get("exp"), tz=UTC):
                raise HTTPException(
                    status_code=400, detail="Token expired")
            user.status = "active"
            await self.db.commit()
            add_token_to_blacklist(token)
            return {"detail": "User verified successfully"}
        except HTTPException as error:
            raise error
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Logout user by blacklisting the token
    async def logout_user(self, token: str):
        try:
            add_token_to_blacklist(token)
            return {"detail": "Logout successful"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Send password reset link to user's email
    async def forgot_password(self, email: EmailStr, background_tasks: BackgroundTasks):
        try:
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return_token = create_access_token(data={"id": str(
                user.id), "type": "reset_password"}, expires_delta=timedelta(hours=1))
            # Send email with password reset link
            context = {
                "app_name": settings.app_name,
                "user_name": user.username,
                "reset_link": f"http://localhost:8000/reset-password?token={return_token}"
            }
            email_list = [user.email]
            background_tasks.add_task(
                send_email, email_list, "Reset Password Link", "password_reset.html", context)
            return {"detail": "Password reset link sent to your email"}
        except HTTPException as error:
            raise error
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Reset user password using token
    async def reset_password(self, data: ResetTokenSchema):
        try:
            token_data = data.model_dump()
            if is_token_blacklisted(token_data["token"]):
                raise HTTPException(
                    status_code=400, detail="Token has been blacklisted")
            if token_data["new_password"] != token_data["confirm_password"]:
                raise HTTPException(
                    status_code=400, detail="Passwords do not match")
            payload = decode_token(token_data["token"])
            query = select(User).where(User.id == payload.get("id"))
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if payload["type"] != "reset_password":
                raise HTTPException(
                    status_code=400, detail="Invalid token")
            if datetime.now(UTC) > datetime.fromtimestamp(payload.get("exp"), tz=UTC):
                raise HTTPException(
                    status_code=400, detail="Token expired")

            user._password = get_password_hash(token_data["new_password"])
            await self.db.commit()
            add_token_to_blacklist(token_data["token"])
            return {"detail": "Password reset successful"}
        except HTTPException as error:
            raise error
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Change user password
    async def change_password(self, data: ChangePasswordSchema, user: User):
        try:
            query = select(User).where(User.id == user.id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            if not user or not verify_password(data.current_password, user._password):
                raise HTTPException(
                    status_code=401, detail="Invalid Old password")
            if data.new_password != data.confirm_password:
                raise HTTPException(
                    status_code=400, detail="Passwords do not match")
            user._password = get_password_hash(data.new_password)
            await self.db.commit()
            return {"detail": "Password changed successfully"}
        except HTTPException as error:
            raise error
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
