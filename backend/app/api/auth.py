"""
Authentication API endpoints
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.models.user import User
from app.dependencies.auth import get_current_user, get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])


# ===== Schemas =====

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_admin: bool
    is_active: bool
    subscription_tier: str = "free"
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Endpoints =====

@router.post("/register", response_model=UserResponse)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with email/password

    - **email**: Valid email address
    - **password**: Password (min 8 characters recommended)
    - **full_name**: Optional full name
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        is_active=True,
        email_verified=False,  # TODO: Send verification email
        is_admin=False,
        subscription_tier="free"
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email/password

    Uses OAuth2 password flow (username = email)
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Update last login time
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login_at=datetime.utcnow())
    )
    await db.commit()

    # Create JWT tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(user_id=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user's information

    Requires valid JWT token in Authorization header
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user

    Note: Client should delete stored tokens
    In future: invalidate refresh token in database
    """
    # TODO: Invalidate refresh token in database
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token
    """
    from app.core.security import verify_token

    # Verify refresh token
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(user_id=user.id)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# ===== OAuth Endpoints =====

@router.get("/google")
async def google_login(redirect_uri: str):
    """
    Redirect to Google OAuth login

    - **redirect_uri**: Frontend callback URL
    """
    from app.services.oauth_service import OAuthService
    from app.core.config import settings

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )

    try:
        auth_url = OAuthService.get_google_auth_url(redirect_uri)
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Google OAuth URL"
        )


@router.get("/google/callback")
async def google_callback(
    code: str,
    redirect_uri: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth callback

    - **code**: Authorization code from Google
    - **redirect_uri**: Same redirect URI used in initial request
    """
    from app.services.oauth_service import OAuthService

    try:
        result = await OAuthService.handle_google_callback(code, redirect_uri, db)
        return Token(
            access_token=result['access_token'],
            refresh_token=result['refresh_token'],
            token_type='bearer'
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Google callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


@router.get("/microsoft")
async def microsoft_login(redirect_uri: str):
    """
    Redirect to Microsoft OAuth login

    - **redirect_uri**: Frontend callback URL
    """
    from app.services.oauth_service import OAuthService
    from app.core.config import settings

    if not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft OAuth not configured. Please set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET."
        )

    try:
        auth_url = OAuthService.get_microsoft_auth_url(redirect_uri)
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Microsoft OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Microsoft OAuth URL"
        )


@router.get("/microsoft/callback")
async def microsoft_callback(
    code: str,
    redirect_uri: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Microsoft OAuth callback

    - **code**: Authorization code from Microsoft
    - **redirect_uri**: Same redirect URI used in initial request
    """
    from app.services.oauth_service import OAuthService

    try:
        result = await OAuthService.handle_microsoft_callback(code, redirect_uri, db)
        return Token(
            access_token=result['access_token'],
            refresh_token=result['refresh_token'],
            token_type='bearer'
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Microsoft callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )
