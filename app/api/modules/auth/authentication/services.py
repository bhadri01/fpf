from .schemas import OTPSetupSchema, OTPVerificationSchema, ResetTokenSchema, ChangePasswordSchema, UserLoginSchema, UserRegisterCreate,InvitedUserRegisterCreate
from app.utils.security import create_access_token, decode_token, decrypt_secret, encrypt_secret, hash_key
from app.utils.token_blacklist import add_token_to_blacklist, is_token_blacklisted
from app.api.modules.auth.authentication.models import APIKey, RoleRedirection
from app.middlewares.middleware_response import json_response_with_cors
from app.utils.password_utils import get_password_hash, verify_password
from fastapi import BackgroundTasks, HTTPException, status
from app.api.modules.auth.users.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta, datetime, UTC
from app.utils.mail.email import send_email
from app.core.redis import redis_cache
from app.core.config import settings
from sqlalchemy.future import select
from sqlalchemy.sql import or_
from pydantic import EmailStr
from PIL import Image
from jose import jwt
from jose.exceptions import JWTError,ExpiredSignatureError
from app.utils.security import SECRET_KEY, ALGORITHM, hash_key
from app.utils.mail.email import send_email
import hashlib
import secrets
import random
import qrcode
import pyotp
import os
import io
import uuid
from jose import JWTError, jwt


FORGOT_PASSWORD_COOLDOWN = 5 * 60  # 5 minutes in seconds


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    '''
    =====================================================
    # Login User Function
    =====================================================
    '''

    async def login_user(self, user_login: UserLoginSchema):
        query = select(User).where(
            or_(User.username == user_login.identifier, User.email == user_login.identifier))
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user or not verify_password(user_login.password, user.password):
            raise HTTPException(
                status_code=401, detail="Invalid username or password")
        if user.status_2fa:
            return {
                "detail": "2FA Required", "required_2fa": True,
                "user": {"id": str(user.id), "email": user.email}
            }

        access_token = create_access_token(data={"id": str(
            user.id), "type": "access"}, expires_delta=timedelta(days=1))
        refresh_token = create_access_token(data={"id": str(
            user.id), "type": "refresh"}, expires_delta=timedelta(days=7))
        return {"detail": f"Welcome, {user.username}", "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    '''
    =====================================================
    # Register User Function
    =====================================================
    '''

    async def register_user(self, user: UserRegisterCreate, background_tasks: BackgroundTasks):
        # Check if user exists
        existing_user_result = await self.db.execute(select(User).where(User.username == user.username))
        existing_user = existing_user_result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Check if email exists
        existing_email_result = await self.db.execute(select(User).where(User.email == user.email))
        existing_email = existing_email_result.scalar_one_or_none()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

        # Create user (ensure this operation is in an async context)
        count = await User.create(self.db, [user])
        if count != 1:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        objs = await self.db.execute(select(User).where(User.email == user.email))
        created_user = objs.scalars().first()

        # Create Access Token
        return_token = create_access_token(data={
            "id": str(created_user.id),
            "type": "verify_user"},
            expires_delta=timedelta(days=1))

        # Send verification email asynchronously in the background
        context = {
            "app_name": settings.app_name,
            "user_name": created_user.username,
            "verification_link": f"{settings.verify_url}?token={return_token}"
        }
        email_list = [created_user.email]
        background_tasks.add_task(
            send_email, email_list, "Account Verification", "verification.html", context)

        return {"detail": "User registered successfully. Verification link sent to your email"}

    '''
    =====================================================
    # Verify User Function
    =====================================================
    '''

    async def verify_user(self, token: str):
        if is_token_blacklisted(token):
            raise HTTPException(
                status_code=400, detail="The provided token has been blacklisted.")
        payload = decode_token(token)
        query = select(User).where(User.id == payload.get("id"))
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        if payload["type"] != "verify_user":
            raise HTTPException(
                status_code=400, detail="The token provided is invalid for user verification.")
        if datetime.now(UTC) > datetime.fromtimestamp(payload.get("exp"), tz=UTC):
            raise HTTPException(
                status_code=400, detail="The token has expired.")
        user.status = "active"
        await self.db.commit()
        add_token_to_blacklist(token)
        return {"detail": "User has been successfully verified."}

    '''
    =====================================================
    # Resend Verify Token Function
    =====================================================
    '''

    async def resend_verify_token(self, email: EmailStr, background_tasks: BackgroundTasks):
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.status == "active":
            raise HTTPException(
                status_code=400, detail="User already verified")

        # Check if the user has already requested within cooldown period
        cooldown_key = f"verify_token:{user.id}"
        last_request_time = await redis_cache.get(cooldown_key)

        if last_request_time:
            last_request_time = datetime.fromtimestamp(
                float(last_request_time), tz=UTC)
            time_since_last_request = (datetime.now(
                UTC) - last_request_time).total_seconds()

            if time_since_last_request < FORGOT_PASSWORD_COOLDOWN:
                remaining_time = int(
                    FORGOT_PASSWORD_COOLDOWN - time_since_last_request)
                return json_response_with_cors(
                    {
                        "detail": "Please wait before requesting another verification email.",
                        "cooldown_remaining": remaining_time
                    },
                    status.HTTP_429_TOO_MANY_REQUESTS
                )

        return_token = create_access_token(data={"id": str(
            user.id), "type": "verify_user"}, expires_delta=timedelta(days=1))

        # Store request timestamp in Redis
        await redis_cache.set(cooldown_key, str(datetime.now(UTC).timestamp()), ttl=FORGOT_PASSWORD_COOLDOWN)

        context = {
            "app_name": settings.app_name,
            "user_name": user.username,
            "verification_link": f"{settings.verify_url}?token={return_token}"
        }
        email_list = [user.email]
        background_tasks.add_task(
            send_email, email_list, "Account Verification", "verification.html", context)
        return {"detail": "Verification link sent to your email", "cooldown_remaining": FORGOT_PASSWORD_COOLDOWN}

    '''
    =====================================================
    # Logout User Function
    =====================================================
    '''

    async def logout_user(self, token: str):
        add_token_to_blacklist(token)
        return {"detail": "Logout successful"}

    '''
    =====================================================
    # Forgot Password Function
    =====================================================
    '''

    async def forgot_password(self, email: EmailStr, background_tasks: BackgroundTasks):
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=404, detail="User with the provided email not found")

        # Check if the user has already requested within cooldown period
        cooldown_key = f"password_reset:{user.id}"
        last_request_time = await redis_cache.get(cooldown_key)

        if last_request_time:
            last_request_time = datetime.fromtimestamp(
                float(last_request_time), tz=UTC)
            time_since_last_request = (datetime.now(
                UTC) - last_request_time).total_seconds()

            if time_since_last_request < FORGOT_PASSWORD_COOLDOWN:
                remaining_time = int(
                    FORGOT_PASSWORD_COOLDOWN - time_since_last_request)
                return json_response_with_cors(
                    {
                        "detail": "Please wait before requesting another reset email.",
                        "cooldown_remaining": remaining_time
                    },
                    status.HTTP_429_TOO_MANY_REQUESTS
                )

        # Generate reset token
        return_token = create_access_token(
            data={"id": str(user.id), "type": "reset_password"},
            expires_delta=timedelta(hours=1)
        )

        # Store request timestamp in Redis
        await redis_cache.set(cooldown_key, str(datetime.now(UTC).timestamp()), ttl=FORGOT_PASSWORD_COOLDOWN)

        # Prepare email context
        context = {
            "app_name": settings.app_name,
            "user_name": user.username,
            "reset_link": f"{settings.reset_url}?token={return_token}"
        }
        email_list = [user.email]

        # Send email in background
        background_tasks.add_task(
            send_email, email_list, "Reset Password Link", "password_reset.html", context)

        return {"detail": "Password reset link sent to your email", "cooldown_remaining": FORGOT_PASSWORD_COOLDOWN}

    '''
    =====================================================
    # Reset Password Function
    =====================================================
    '''

    async def reset_password(self, data: ResetTokenSchema):
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
        if len(token_data["new_password"]) < 8:
            raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long")
        if token_data["new_password"] != token_data["confirm_password"]:
            raise HTTPException(
            status_code=400, detail="Passwords do not match")
        user.password = get_password_hash(token_data["new_password"])
        await self.db.commit()
        add_token_to_blacklist(token_data["token"])
        return {"detail": "Password reset successful"}

    '''
    =====================================================
    # Change Password Function
    =====================================================
    '''

    async def change_password(self, data: ChangePasswordSchema, user: User):
        query = select(User).where(User.id == user.id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user or not verify_password(data.current_password, user.password):
            raise HTTPException(
                status_code=401, detail="Invalid Old password")
        if len(data.new_password) < 8:
            raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long")
        if data.new_password != data.confirm_password:
            raise HTTPException(
            status_code=400, detail="Passwords do not match")
        user.password = get_password_hash(data.new_password)
        await self.db.commit()
        return {"detail": "Password changed successfully"}

    '''
    =====================================================
    # Random Profile Picture Generation
    =====================================================
    '''

    def generate_pixel_avatar(self, email, size=6, scale=32):
        # Seed the random generator for consistent avatar per email
        random.seed(str(email))

        # Generate a single color for the avatar
        main_color = (random.randint(50, 200), random.randint(
            50, 200), random.randint(50, 200))  # One solid color

        # Generate a 6x6 pattern (only half is randomly generated, then mirrored)
        pixels = [[random.choice([0, 1]) for _ in range(size // 2)]
                  for _ in range(size)]

        # Mirror left half to right
        for row in pixels:
            row.extend(reversed(row))  # Ensures perfect mirroring for 6x6

        # Create Image
        img = Image.new("RGB", (size, size), "white")
        for y in range(size):
            for x in range(size):
                color = main_color if pixels[y][x] == 1 else (
                    255, 255, 255)  # Use main color or white
                img.putpixel((x, y), color)

        # Scale up the image for better visibility
        img = img.resize((size * scale, size * scale), Image.NEAREST)

        # Ensure the directory exists
        output_dir = "public/profiles"
        os.makedirs(output_dir, exist_ok=True)

        # Generate a random filename
        filename = f"{random.randint(1000, 9999)}.png"

        # Use a hash of the email to ensure unique filenames
        email_hash = hashlib.md5(email.encode()).hexdigest()
        filename = f"{email_hash}.png"

        # Save the image in the specified directory
        filepath = os.path.join(output_dir, filename)
        img.save(filepath)
        return filepath

    '''
    =====================================================
    # Check Username Availability Route
    =====================================================
    '''

    async def check_username(self, username: str):
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            raise HTTPException(
                status_code=400, detail="Username is already taken")
        return {"detail": "Username is available"}

    '''
    =====================================================
    # Check Email Availability Route
    =====================================================
    '''

    async def check_email(self, email: EmailStr):
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            raise HTTPException(
                status_code=400, detail="Email is already taken")
        return {"detail": "Email is available"}

    '''
    =====================================================
    # Refresh Token Route
    =====================================================
    '''

    async def refresh_token(self, refresh_token: str):
        if is_token_blacklisted(refresh_token):
            raise HTTPException(
                status_code=400, detail="The provided token has been blacklisted.")
        payload = decode_token(refresh_token)
        if payload["type"] != "refresh":
            raise HTTPException(
                status_code=400, detail="The token provided is invalid for token refresh.")
        query = select(User).where(User.id == payload.get("id"))
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        access_token = create_access_token(data={"id": str(
            user.id), "type": "access"}, expires_delta=timedelta(days=1))
        return {"access_token": access_token, "token_type": "bearer"}

    '''
    =====================================================
    # 2FA Setup Route
    =====================================================
    '''

    async def two_factor_setup(self, user: User):
        # Generate a temporary secret (not stored in DB yet)
        if user.status_2fa:
            raise HTTPException(
                status_code=400, detail="2FA is already enabled for this user")

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Generate QR Code
        qr_data = totp.provisioning_uri(
            name=user.username, issuer_name=settings.app_name)
        qr = qrcode.make(qr_data)

        img_io = io.BytesIO()
        qr.save(img_io, format="PNG")
        img_io.seek(0)

        return {
            "qr_code": img_io.getvalue().hex(),  # Only for immediate display
            "secret": encrypt_secret(secret)  # Only used once
        }

    '''
    =====================================================
    # 2FA Setup Verify Route
    =====================================================
    '''

    async def two_factor_verify_setup(self, user: User, data: OTPSetupSchema):
        if user.status_2fa:
            raise HTTPException(
                status_code=400, detail="2FA is already enabled for this user")
        totp = pyotp.TOTP(decrypt_secret(data.secret))
        if not totp.verify(data.otp_code):
            raise HTTPException(
                status_code=400, detail="Invalid OTP. Please try again.")
        query = select(User).where(User.id == user.id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # ✅ OTP is correct → Enable 2FA
        user.status_2fa = True
        user.secret_2fa = data.secret
        await self.db.commit()

        return {"detail": "2FA enabled successfully!"}

    '''
    =====================================================
    # 2FA TOTP Verify Route
    =====================================================
    '''

    async def two_factor_verify(self, data: OTPVerificationSchema):
        query = select(User).where(User.id == data.user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.status_2fa:
            raise HTTPException(
                status_code=400, detail="2FA is not enabled for this user")
        totp = pyotp.TOTP(decrypt_secret(user.secret_2fa))
        if not totp.verify(data.otp_code):
            raise HTTPException(
                status_code=400, detail="Invalid OTP. Please try again.")
        access_token = create_access_token(data={"id": str(
            user.id), "type": "access"}, expires_delta=timedelta(days=1))
        refresh_token = create_access_token(data={"id": str(
            user.id), "type": "refresh"}, expires_delta=timedelta(days=7))
        return {"detail": f"Welcome, {user.username}", "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    '''
    =====================================================
    # 2FA Disable Route
    =====================================================
    '''

    async def two_factor_disable(self, user: User):
        query = select(User).where(User.id == user.id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.status_2fa:
            raise HTTPException(
                status_code=400, detail="2FA is already disabled")
        user.status_2fa = False
        user.secret_2fa = None
        await self.db.commit()
        return {"detail": "2FA disabled successfully!"}

    '''
    =====================================================
    # Get Api-key Route
    =====================================================
    '''

    async def get_api_keys(self, user: User):
        query = select(APIKey).where(APIKey.user_id == user.id)
        result = await self.db.execute(query)
        api_keys = result.scalars().all()
        masked_keys = [
            {
            "id": api_key.id,
            "key": f"{api_key.key[:4]}{'*' * 5}",
            "created_at": api_key.created_at,
            }
            for api_key in api_keys
        ]
        return masked_keys

    '''
    =====================================================
    # Create Api-key Route
    =====================================================
    '''

    async def create_api_key(self, user: User):
        raw_key = secrets.token_urlsafe(32)
        hashed_key = hash_key(raw_key)

        api_key = APIKey(user_id=user.id, key=hashed_key)
        self.db.add(api_key)
        await self.db.commit()
        return {"detail": raw_key}

    '''
    =====================================================
    # Remove Api-key Route
    =====================================================
    '''

    async def remove_api_key(self, user: User, key_id: str):
        query = select(APIKey).where(APIKey.user_id == user.id, APIKey.id == key_id)
        result = await self.db.execute(query)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(status_code=404, detail="API Key not found")

        await self.db.delete(api_key)
        await self.db.commit()
        return {"detail": "API Key removed successfully"}

    '''
    =====================================================
    # Login Redirect API Route
    =====================================================
    '''

    async def login_redirect(self, user: User):
        if not user.role_id:
            raise HTTPException(
                status_code=404, detail="User does not have a role assigned")
        query = select(RoleRedirection).where(
            RoleRedirection.role_id == user.role_id)
        result = await self.db.execute(query)
        result = result.scalars().one_or_none()
        if not result:
            raise HTTPException(
                status_code=404, detail="No redirection found for the user's role")
        return {"detail": result.redirect}

    '''
    =====================================================
    # Invite user  API Route
    =====================================================
    '''

    async def invite_user(self, email: str, role_id: str, background_tasks: BackgroundTasks):

        existing_email = await self.db.execute(select(User).where(User.email == email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")

        invite_link = create_access_token(
            data={"email": email, "role_id": role_id, "type": "invitation"},
            expires_delta=timedelta(hours=24)
        )
        email_list = [email]

        context = {
            "user_name": email.split("@")[0],
            "app_name": settings.app_name,
            "invitation_link": f"{settings.verify_url}?token={invite_link}"
        }

        background_tasks.add_task(send_email, email_list, "You're Invited!", "invitation.html", context)

        return {"details": "Success", "Message": "Successfully sent the invitation email"}


    '''
    =====================================================
    # Register invited  API Route
    =====================================================
    '''
    async def register_invited_user(self, user: InvitedUserRegisterCreate, background_tasks: BackgroundTasks):


        payload = jwt.decode(user.token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "invitation":
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        email, role_id = payload.get("email"), payload.get("role_id")

        existing_user = await self.db.execute(select(User).where(User.username == user.username))
        if existing_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists")

        existing_email = await self.db.execute(select(User).where(User.email == email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")

        user_data = {
            "username": user.username,
            "email": email,
            "password": user.password,  
            "role_id": role_id
        }

        # Create user
        count = await User.create(self.db, [user_data]) 
        if count != 1:
            raise HTTPException(status_code=400, detail="Failed to create user")

        objs = await self.db.execute(select(User).where(User.email == email))
        created_user = objs.scalars().first()


        return_token = create_access_token(
            data={"id": str(created_user.id), "type": "verify_user"},
            expires_delta=timedelta(days=1)
        )

        # Send verification email asynchronously
        context = {
            "app_name": settings.app_name,
            "user_name": created_user.username,
            "verification_link": f"{settings.verify_url}?token={return_token}"
        }
        email_list = [created_user.email]
        background_tasks.add_task(send_email, email_list, "Account Verification", "verification.html", context)

        return {"detail": "User registered successfully. Verification link sent to your email"}

   
     

#