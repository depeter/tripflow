"""
Integration tests for User model

These tests verify:
- User CRUD operations
- Password hashing
- Email uniqueness constraints
- User-Trip relationships
"""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.trip import Trip, TripStatus
from app.core.security import get_password_hash, verify_password


@pytest.mark.integration
class TestUserModel:
    """Test User model with real database"""

    def test_create_user(self, db_session):
        """Test creating a user in database"""
        # Arrange & Act
        user = User(
            email="newuser@example.com",
            password_hash=get_password_hash("password123"),
            full_name="New User",
            is_active=True,
            is_admin=False
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Assert
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.created_at is not None

    def test_password_hashing(self, db_session):
        """Test that password is properly hashed"""
        # Arrange
        plain_password = "secretpassword123"
        user = User(
            email="secure@example.com",
            password_hash=get_password_hash(plain_password),
            full_name="Secure User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Act & Assert
        # Password hash should not match plain password
        assert user.password_hash != plain_password
        # But verification should work
        assert verify_password(plain_password, user.password_hash)
        # Wrong password should not verify
        assert not verify_password("wrongpassword", user.password_hash)

    def test_email_uniqueness_constraint(self, db_session):
        """Test that email must be unique"""
        # Arrange
        user1 = User(
            email="duplicate@example.com",
            password_hash=get_password_hash("pass1"),
            full_name="User One"
        )
        user2 = User(
            email="duplicate@example.com",  # Same email
            password_hash=get_password_hash("pass2"),
            full_name="User Two"
        )

        # Act & Assert
        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_query_user_by_email(self, db_session, test_user):
        """Test querying user by email"""
        # Act
        found = db_session.query(User).filter(User.email == test_user.email).first()

        # Assert
        assert found is not None
        assert found.id == test_user.id
        assert found.email == test_user.email

    def test_update_user(self, db_session, test_user):
        """Test updating user attributes"""
        # Arrange
        original_name = test_user.full_name

        # Act
        test_user.full_name = "Updated Name"
        test_user.is_admin = True
        db_session.commit()
        db_session.refresh(test_user)

        # Assert
        assert test_user.full_name == "Updated Name"
        assert test_user.full_name != original_name
        assert test_user.is_admin is True

    def test_deactivate_user(self, db_session, test_user):
        """Test deactivating a user"""
        # Arrange
        assert test_user.is_active is True

        # Act
        test_user.is_active = False
        db_session.commit()
        db_session.refresh(test_user)

        # Assert
        assert test_user.is_active is False

    def test_delete_user(self, db_session):
        """Test deleting a user"""
        # Arrange
        user = User(
            email="deleteme@example.com",
            password_hash=get_password_hash("password"),
            full_name="Delete Me"
        )
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        # Act
        db_session.delete(user)
        db_session.commit()

        # Assert
        found = db_session.query(User).filter(User.id == user_id).first()
        assert found is None

    def test_user_trips_relationship(self, db_session, test_user):
        """Test querying user's trips"""
        # Arrange - Create trips for user
        trip1 = Trip(
            user_id=test_user.id,
            status=TripStatus.PLANNING,
            start_address="Trip 1",
            start_latitude=50.0,
            start_longitude=4.0
        )
        trip2 = Trip(
            user_id=test_user.id,
            status=TripStatus.ACTIVE,
            start_address="Trip 2",
            start_latitude=50.1,
            start_longitude=4.1
        )
        db_session.add_all([trip1, trip2])
        db_session.commit()

        # Act - Query user's trips
        user_trips = db_session.query(Trip).filter(Trip.user_id == test_user.id).all()

        # Assert
        assert len(user_trips) >= 2
        trip_addresses = [t.start_address for t in user_trips]
        assert "Trip 1" in trip_addresses
        assert "Trip 2" in trip_addresses

    def test_filter_active_users(self, db_session):
        """Test filtering active vs inactive users"""
        # Arrange
        active_user = User(
            email="active@example.com",
            password_hash=get_password_hash("pass"),
            full_name="Active User",
            is_active=True
        )
        inactive_user = User(
            email="inactive@example.com",
            password_hash=get_password_hash("pass"),
            full_name="Inactive User",
            is_active=False
        )
        db_session.add_all([active_user, inactive_user])
        db_session.commit()

        # Act
        active_users = db_session.query(User).filter(User.is_active == True).all()
        inactive_users = db_session.query(User).filter(User.is_active == False).all()

        # Assert
        assert len(active_users) >= 1
        assert len(inactive_users) >= 1
        assert active_user.email in [u.email for u in active_users]
        assert inactive_user.email in [u.email for u in inactive_users]

    def test_admin_users_query(self, db_session):
        """Test querying admin users"""
        # Arrange
        admin = User(
            email="admin@example.com",
            password_hash=get_password_hash("pass"),
            full_name="Admin User",
            is_admin=True
        )
        regular = User(
            email="regular@example.com",
            password_hash=get_password_hash("pass"),
            full_name="Regular User",
            is_admin=False
        )
        db_session.add_all([admin, regular])
        db_session.commit()

        # Act
        admins = db_session.query(User).filter(User.is_admin == True).all()

        # Assert
        assert len(admins) >= 1
        assert admin.email in [u.email for u in admins]
        assert regular.email not in [u.email for u in admins]
