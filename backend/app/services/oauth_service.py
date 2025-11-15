"""
OAuth authentication service for Google and Microsoft
"""
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client import OAuthError
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.config import settings
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token
import logging

logger = logging.getLogger(__name__)

# Initialize OAuth client
oauth = OAuth()

# Configure Google OAuth
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

# Configure Microsoft OAuth
if settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET:
    oauth.register(
        name='microsoft',
        client_id=settings.MICROSOFT_CLIENT_ID,
        client_secret=settings.MICROSOFT_CLIENT_SECRET,
        server_metadata_url=f'https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/v2.0/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )


class OAuthService:
    """Service for handling OAuth authentication"""

    @staticmethod
    def get_google_auth_url(redirect_uri: str) -> str:
        """
        Generate Google OAuth authorization URL
        """
        try:
            if not hasattr(oauth, 'google'):
                raise ValueError("Google OAuth not configured")

            request_uri = oauth.google.authorize_redirect_url(redirect_uri)
            return request_uri
        except Exception as e:
            logger.error(f"Error generating Google auth URL: {e}")
            raise

    @staticmethod
    def get_microsoft_auth_url(redirect_uri: str) -> str:
        """
        Generate Microsoft OAuth authorization URL
        """
        try:
            if not hasattr(oauth, 'microsoft'):
                raise ValueError("Microsoft OAuth not configured")

            request_uri = oauth.microsoft.authorize_redirect_url(redirect_uri)
            return request_uri
        except Exception as e:
            logger.error(f"Error generating Microsoft auth URL: {e}")
            raise

    @staticmethod
    async def handle_google_callback(
        code: str,
        redirect_uri: str,
        db: AsyncSession
    ) -> Dict[str, any]:
        """
        Handle Google OAuth callback and create/login user
        """
        try:
            # Exchange authorization code for token
            token = await oauth.google.authorize_access_token(code=code, redirect_uri=redirect_uri)

            # Get user info from Google
            user_info = token.get('userinfo')
            if not user_info:
                # Fetch user info if not in token
                resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo')
                user_info = resp.json()

            email = user_info.get('email')
            google_id = user_info.get('sub')
            full_name = user_info.get('name')
            avatar_url = user_info.get('picture')

            # Find or create user
            result = await db.execute(
                select(User).where(
                    (User.email == email) | (User.google_id == google_id)
                )
            )
            user = result.scalar_one_or_none()

            if user:
                # Update existing user
                if not user.google_id:
                    user.google_id = google_id
                if not user.email_verified and email:
                    user.email_verified = True
                if not user.avatar_url and avatar_url:
                    user.avatar_url = avatar_url
                user.last_login_at = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    email=email,
                    google_id=google_id,
                    full_name=full_name,
                    avatar_url=avatar_url,
                    email_verified=True,
                    is_active=True,
                    is_admin=False,
                    subscription_tier='free',
                    last_login_at=datetime.utcnow()
                )
                db.add(user)

            await db.commit()
            await db.refresh(user)

            # Generate JWT tokens
            access_token = create_access_token(data={"sub": str(user.id)})
            refresh_token = create_refresh_token(user_id=user.id)

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'user': user
            }

        except OAuthError as e:
            logger.error(f"Google OAuth error: {e}")
            raise ValueError(f"OAuth authentication failed: {e.description}")
        except Exception as e:
            logger.error(f"Error handling Google callback: {e}")
            raise

    @staticmethod
    async def handle_microsoft_callback(
        code: str,
        redirect_uri: str,
        db: AsyncSession
    ) -> Dict[str, any]:
        """
        Handle Microsoft OAuth callback and create/login user
        """
        try:
            # Exchange authorization code for token
            token = await oauth.microsoft.authorize_access_token(code=code, redirect_uri=redirect_uri)

            # Get user info from Microsoft
            user_info = token.get('userinfo')
            if not user_info:
                # Fetch user info from Microsoft Graph
                resp = await oauth.microsoft.get('https://graph.microsoft.com/v1.0/me')
                user_info = resp.json()

            email = user_info.get('userPrincipalName') or user_info.get('mail')
            microsoft_id = user_info.get('id')
            full_name = user_info.get('displayName')

            # Find or create user
            result = await db.execute(
                select(User).where(
                    (User.email == email) | (User.microsoft_id == microsoft_id)
                )
            )
            user = result.scalar_one_or_none()

            if user:
                # Update existing user
                if not user.microsoft_id:
                    user.microsoft_id = microsoft_id
                if not user.email_verified and email:
                    user.email_verified = True
                user.last_login_at = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    email=email,
                    microsoft_id=microsoft_id,
                    full_name=full_name,
                    email_verified=True,
                    is_active=True,
                    is_admin=False,
                    subscription_tier='free',
                    last_login_at=datetime.utcnow()
                )
                db.add(user)

            await db.commit()
            await db.refresh(user)

            # Generate JWT tokens
            access_token = create_access_token(data={"sub": str(user.id)})
            refresh_token = create_refresh_token(user_id=user.id)

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'user': user
            }

        except OAuthError as e:
            logger.error(f"Microsoft OAuth error: {e}")
            raise ValueError(f"OAuth authentication failed: {e.description}")
        except Exception as e:
            logger.error(f"Error handling Microsoft callback: {e}")
            raise
