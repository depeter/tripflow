"""
Integration tests for Trip model

These tests verify:
- Trip CRUD operations
- User-Trip relationships
- Trip status transitions
- JSON field handling
"""
import pytest
from app.models.trip import Trip, TripStatus
from app.models.user import User


@pytest.mark.integration
class TestTripModel:
    """Test Trip model with real database"""

    def test_create_trip(self, db_session, test_user):
        """Test creating a trip in database"""
        # Arrange & Act
        trip = Trip(
            user_id=test_user.id,
            status=TripStatus.PLANNING,
            start_address="Brussels, Belgium",
            start_latitude=50.8503,
            start_longitude=4.3517,
            end_address="Amsterdam, Netherlands",
            end_latitude=52.3676,
            end_longitude=4.9041,
            max_distance_km=500,
            duration_days=3,
            trip_preferences={"interests": ["nature", "camping"], "budget": "medium"}
        )
        db_session.add(trip)
        db_session.commit()
        db_session.refresh(trip)

        # Assert
        assert trip.id is not None
        assert trip.user_id == test_user.id
        assert trip.status == TripStatus.PLANNING
        assert trip.start_address == "Brussels, Belgium"
        assert trip.trip_preferences["budget"] == "medium"

    def test_trip_user_relationship(self, db_session, test_user):
        """Test that trip is correctly linked to user"""
        # Arrange & Act
        trip = Trip(
            user_id=test_user.id,
            status=TripStatus.PLANNING,
            start_address="Test Location",
            start_latitude=50.0,
            start_longitude=4.0
        )
        db_session.add(trip)
        db_session.commit()
        db_session.refresh(trip)

        # Assert
        assert trip.user_id == test_user.id

        # Query user's trips
        user_trips = db_session.query(Trip).filter(Trip.user_id == test_user.id).all()
        assert len(user_trips) >= 1
        assert trip.id in [t.id for t in user_trips]

    def test_update_trip_status(self, db_session, test_user):
        """Test updating trip status"""
        # Arrange
        trip = Trip(
            user_id=test_user.id,
            status=TripStatus.PLANNING,
            start_address="Test",
            start_latitude=50.0,
            start_longitude=4.0
        )
        db_session.add(trip)
        db_session.commit()

        # Act
        trip.status = TripStatus.ACTIVE
        db_session.commit()
        db_session.refresh(trip)

        # Assert
        assert trip.status == TripStatus.ACTIVE

    def test_trip_with_preferences_json(self, db_session, test_user):
        """Test trip with JSON preferences field"""
        # Arrange & Act
        preferences = {
            "interests": ["beach", "mountains", "culture"],
            "budget": "luxury",
            "accommodation_type": "hotel",
            "dietary_restrictions": ["vegetarian"]
        }
        trip = Trip(
            user_id=test_user.id,
            status=TripStatus.PLANNING,
            start_address="Test",
            start_latitude=50.0,
            start_longitude=4.0,
            trip_preferences=preferences
        )
        db_session.add(trip)
        db_session.commit()
        db_session.refresh(trip)

        # Assert
        assert trip.trip_preferences == preferences
        assert "beach" in trip.trip_preferences["interests"]
        assert trip.trip_preferences["budget"] == "luxury"

    def test_round_trip(self, db_session, test_user):
        """Test round trip (no end address)"""
        # Arrange & Act
        trip = Trip(
            user_id=test_user.id,
            status=TripStatus.PLANNING,
            start_address="Brussels, Belgium",
            start_latitude=50.8503,
            start_longitude=4.3517,
            end_address=None,
            end_latitude=None,
            end_longitude=None,
            max_distance_km=300
        )
        db_session.add(trip)
        db_session.commit()
        db_session.refresh(trip)

        # Assert
        assert trip.end_address is None
        assert trip.end_latitude is None
        assert trip.end_longitude is None
        assert trip.max_distance_km == 300

    def test_query_trips_by_status(self, db_session, test_user):
        """Test filtering trips by status"""
        # Arrange
        planning_trip = Trip(
            user_id=test_user.id, status=TripStatus.PLANNING,
            start_address="Test 1", start_latitude=50.0, start_longitude=4.0
        )
        active_trip = Trip(
            user_id=test_user.id, status=TripStatus.ACTIVE,
            start_address="Test 2", start_latitude=50.1, start_longitude=4.1
        )
        completed_trip = Trip(
            user_id=test_user.id, status=TripStatus.COMPLETED,
            start_address="Test 3", start_latitude=50.2, start_longitude=4.2
        )
        db_session.add_all([planning_trip, active_trip, completed_trip])
        db_session.commit()

        # Act
        planning_trips = db_session.query(Trip).filter(
            Trip.status == TripStatus.PLANNING
        ).all()
        active_trips = db_session.query(Trip).filter(
            Trip.status == TripStatus.ACTIVE
        ).all()

        # Assert
        assert len(planning_trips) >= 1
        assert len(active_trips) >= 1
        assert all(t.status == TripStatus.PLANNING for t in planning_trips)
        assert all(t.status == TripStatus.ACTIVE for t in active_trips)

    def test_delete_trip(self, db_session, test_user):
        """Test deleting a trip"""
        # Arrange
        trip = Trip(
            user_id=test_user.id,
            status=TripStatus.PLANNING,
            start_address="Temp Trip",
            start_latitude=50.0,
            start_longitude=4.0
        )
        db_session.add(trip)
        db_session.commit()
        trip_id = trip.id

        # Act
        db_session.delete(trip)
        db_session.commit()

        # Assert
        found = db_session.query(Trip).filter(Trip.id == trip_id).first()
        assert found is None
