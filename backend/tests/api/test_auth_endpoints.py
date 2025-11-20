"""
API tests for authentication endpoints

Tests the HTTP API layer using dependency override:
- POST /api/v1/auth/register - User registration
- POST /api/v1/auth/login - User login
- GET /api/v1/auth/me - Get current user
"""
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from fastapi import status
from datetime import datetime


@pytest.mark.api
class TestAuthEndpoints:
    """Test authentication API endpoints"""

    def test_register_success(self, test_client):
        """Test successful user registration"""
        # Arrange
        from app.db.database import get_db
        from app.main import app
        from app.models.user import User

        registration_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User"
        }

        # Create async mock database
        async def mock_get_db():
            mock_db = AsyncMock()

            # Mock execute for user existence check (returns None - user doesn't exist)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            # Mock add (does nothing)
            mock_db.add = MagicMock()

            # Mock commit
            mock_db.commit = AsyncMock()

            # Mock refresh - sets user attributes
            async def mock_refresh(user):
                user.id = 1
                user.created_at = datetime(2025, 11, 19, 10, 0, 0)

            mock_db.refresh = mock_refresh

            return mock_db

        # Override dependency
        app.dependency_overrides[get_db] = mock_get_db

        try:
            # Act
            response = test_client.post(
                "/api/v1/auth/register",
                json=registration_data
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == registration_data["email"]
            assert data["full_name"] == registration_data["full_name"]
            assert data["is_active"] == True
            assert data["is_admin"] == False
        finally:
            # Cleanup
            app.dependency_overrides.clear()

    def test_register_duplicate_email(self, test_client):
        """Test registration with existing email"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        registration_data = {
            "email": "existing@example.com",
            "password": "password123",
            "full_name": "Existing User"
        }

        # Create async mock database
        async def mock_get_db():
            mock_db = AsyncMock()

            # Mock execute - user already exists
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = Mock(email="existing@example.com")
            mock_db.execute.return_value = mock_result

            return mock_db

        app.dependency_overrides[get_db] = mock_get_db

        try:
            # Act
            response = test_client.post(
                "/api/v1/auth/register",
                json=registration_data
            )

            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "already registered" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_register_invalid_email(self, test_client):
        """Test registration with invalid email format"""
        # Arrange
        registration_data = {
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Test User"
        }

        # Act
        response = test_client.post(
            "/api/v1/auth/register",
            json=registration_data
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self, test_client):
        """Test successful user login"""
        # Arrange
        from app.db.database import get_db
        from app.main import app
        from app.core.security import get_password_hash

        login_data = {
            "username": "test@example.com",  # OAuth2 uses "username"
            "password": "testpass123"
        }

        # Create async mock database
        async def mock_get_db():
            mock_db = AsyncMock()

            # Mock user lookup
            mock_user = Mock()
            mock_user.id = 1
            mock_user.email = login_data["username"]
            mock_user.password_hash = get_password_hash(login_data["password"])
            mock_user.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result

            # Mock commit for last_login_at update
            mock_db.commit = AsyncMock()

            return mock_db

        app.dependency_overrides[get_db] = mock_get_db

        try:
            # Act
            response = test_client.post(
                "/api/v1/auth/login",
                data=login_data  # OAuth2 uses form data, not JSON
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
        finally:
            app.dependency_overrides.clear()

    def test_login_invalid_email(self, test_client):
        """Test login with non-existent email"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }

        # Create async mock database
        async def mock_get_db():
            mock_db = AsyncMock()

            # Mock user not found
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            return mock_db

        app.dependency_overrides[get_db] = mock_get_db

        try:
            # Act
            response = test_client.post(
                "/api/v1/auth/login",
                data=login_data
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Incorrect email or password" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_login_invalid_password(self, test_client):
        """Test login with wrong password"""
        # Arrange
        from app.db.database import get_db
        from app.main import app
        from app.core.security import get_password_hash

        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }

        # Create async mock database
        async def mock_get_db():
            mock_db = AsyncMock()

            # Mock user with different password
            mock_user = Mock()
            mock_user.id = 1
            mock_user.email = login_data["username"]
            mock_user.password_hash = get_password_hash("correctpassword")
            mock_user.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result

            return mock_db

        app.dependency_overrides[get_db] = mock_get_db

        try:
            # Act
            response = test_client.post(
                "/api/v1/auth/login",
                data=login_data
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            app.dependency_overrides.clear()

    def test_login_inactive_user(self, test_client):
        """Test login with deactivated user account"""
        # Arrange
        from app.db.database import get_db
        from app.main import app
        from app.core.security import get_password_hash

        login_data = {
            "username": "inactive@example.com",
            "password": "password123"
        }

        # Create async mock database
        async def mock_get_db():
            mock_db = AsyncMock()

            # Mock inactive user
            mock_user = Mock()
            mock_user.id = 1
            mock_user.email = login_data["username"]
            mock_user.password_hash = get_password_hash(login_data["password"])
            mock_user.is_active = False  # Inactive!

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result

            return mock_db

        app.dependency_overrides[get_db] = mock_get_db

        try:
            # Act
            response = test_client.post(
                "/api/v1/auth/login",
                data=login_data
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Inactive user" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_current_user_no_token(self, test_client):
        """Test getting current user without authentication"""
        # Act
        response = test_client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, test_client):
        """Test getting current user with invalid token"""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token_here"}

        # Act
        response = test_client.get(
            "/api/v1/auth/me",
            headers=headers
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_success(self, test_client, auth_headers):
        """Test getting current user with valid token"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        # Create async mock database
        async def mock_get_db():
            mock_db = AsyncMock()

            # Mock user lookup by ID from JWT
            mock_user = Mock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.full_name = "Test User"
            mock_user.is_active = True
            mock_user.is_admin = False
            mock_user.subscription_tier = "free"
            mock_user.avatar_url = None
            mock_user.created_at = datetime(2025, 11, 19, 10, 0, 0)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result

            return mock_db

        app.dependency_overrides[get_db] = mock_get_db

        try:
            # Act
            response = test_client.get(
                "/api/v1/auth/me",
                headers=auth_headers
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["full_name"] == "Test User"
        finally:
            app.dependency_overrides.clear()
