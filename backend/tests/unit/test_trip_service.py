"""
Unit tests for TripPlanningService

These tests mock the database and dependencies to test trip planning logic in isolation.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.trip_service import TripPlanningService
from app.models import Trip, TripStatus


@pytest.mark.unit
class TestTripPlanningService:
    """Test TripPlanningService business logic"""

    def test_create_trip_round_trip(self, mock_db_session):
        """Test creating a round trip (no end address)"""
        # Arrange
        mock_location_service = Mock()
        mock_location_service.geocode_address.return_value = {
            "latitude": 50.8503,
            "longitude": 4.3517
        }

        service = TripPlanningService(mock_db_session)
        service.location_service = mock_location_service

        # Mock the Trip object that would be created
        mock_trip = Mock(spec=Trip)
        mock_trip.id = 1
        mock_trip.user_id = 123
        mock_trip.status = TripStatus.PLANNING

        # Mock db operations
        def mock_add(trip):
            trip.id = 1
        mock_db_session.add.side_effect = mock_add
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        # Act
        with patch('app.services.trip_service.Trip', return_value=mock_trip):
            result = service.create_trip(
                user_id=123,
                start_address="Brussels, Belgium",
                max_distance_km=500,
                duration_days=3
            )

        # Assert
        assert result.id == 1
        assert result.user_id == 123
        assert result.status == TripStatus.PLANNING
        mock_location_service.geocode_address.assert_called_once_with("Brussels, Belgium")
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_create_trip_point_to_point(self, mock_db_session):
        """Test creating a point-to-point trip"""
        # Arrange
        mock_location_service = Mock()
        mock_location_service.geocode_address.side_effect = [
            {"latitude": 50.8503, "longitude": 4.3517},  # Brussels
            {"latitude": 52.3676, "longitude": 4.9041}   # Amsterdam
        ]

        service = TripPlanningService(mock_db_session)
        service.location_service = mock_location_service

        mock_trip = Mock(spec=Trip)
        mock_trip.id = 2
        mock_trip.user_id = 123

        def mock_add(trip):
            trip.id = 2
        mock_db_session.add.side_effect = mock_add
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        # Act
        with patch('app.services.trip_service.Trip', return_value=mock_trip):
            result = service.create_trip(
                user_id=123,
                start_address="Brussels, Belgium",
                end_address="Amsterdam, Netherlands",
                max_distance_km=300,
                duration_days=2
            )

        # Assert
        assert result.id == 2
        assert mock_location_service.geocode_address.call_count == 2
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_create_trip_invalid_start_address(self, mock_db_session):
        """Test creating trip with invalid start address"""
        # Arrange
        mock_location_service = Mock()
        mock_location_service.geocode_address.return_value = None

        service = TripPlanningService(mock_db_session)
        service.location_service = mock_location_service

        # Act & Assert
        with pytest.raises(ValueError, match="Could not geocode start address"):
            service.create_trip(
                user_id=123,
                start_address="Invalid Address XYZ123",
            )

        # Verify geocode was attempted
        mock_location_service.geocode_address.assert_called_once()
        # Verify no database operations occurred
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    def test_create_trip_invalid_end_address(self, mock_db_session):
        """Test creating trip with invalid end address"""
        # Arrange
        mock_location_service = Mock()
        mock_location_service.geocode_address.side_effect = [
            {"latitude": 50.8503, "longitude": 4.3517},  # Valid start
            None  # Invalid end
        ]

        service = TripPlanningService(mock_db_session)
        service.location_service = mock_location_service

        # Act & Assert
        with pytest.raises(ValueError, match="Could not geocode end address"):
            service.create_trip(
                user_id=123,
                start_address="Brussels, Belgium",
                end_address="Invalid End XYZ123",
            )

        # Verify both geocode attempts
        assert mock_location_service.geocode_address.call_count == 2
        mock_db_session.add.assert_not_called()

    def test_create_trip_with_preferences(self, mock_db_session):
        """Test creating trip with preferences"""
        # Arrange
        mock_location_service = Mock()
        mock_location_service.geocode_address.return_value = {
            "latitude": 50.8503,
            "longitude": 4.3517
        }

        service = TripPlanningService(mock_db_session)
        service.location_service = mock_location_service

        mock_trip = Mock(spec=Trip)
        mock_trip.id = 3
        mock_trip.trip_preferences = {"interests": ["nature", "camping"], "budget": "medium"}

        def mock_add(trip):
            trip.id = 3
        mock_db_session.add.side_effect = mock_add
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        # Act
        with patch('app.services.trip_service.Trip', return_value=mock_trip):
            result = service.create_trip(
                user_id=123,
                start_address="Brussels, Belgium",
                trip_preferences={
                    "interests": ["nature", "camping"],
                    "budget": "medium"
                }
            )

        # Assert
        assert result.id == 3
        assert result.trip_preferences == {"interests": ["nature", "camping"], "budget": "medium"}

    def test_suggest_waypoints_trip_not_found(self, mock_db_session):
        """Test suggesting waypoints for non-existent trip"""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        service = TripPlanningService(mock_db_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Trip 999 not found"):
            service.suggest_waypoints(trip_id=999)

    def test_suggest_waypoints_point_to_point(self, mock_db_session):
        """Test suggesting waypoints for point-to-point trip"""
        # Arrange
        mock_trip = Mock(spec=Trip)
        mock_trip.id = 1
        mock_trip.start_latitude = 50.8503
        mock_trip.start_longitude = 4.3517
        mock_trip.end_latitude = 52.3676
        mock_trip.end_longitude = 4.9041

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_trip

        # Mock location along route
        mock_location = Mock()
        mock_location.id = 10
        mock_location.name = "Camping Spot"
        mock_location.latitude = 51.5
        mock_location.longitude = 4.5
        mock_location.rating = 4.5

        mock_location_service = Mock()
        mock_location_service.find_locations_along_route.return_value = [
            {
                "location": mock_location,
                "distance_from_route_km": 5.0
            }
        ]

        service = TripPlanningService(mock_db_session)
        service.location_service = mock_location_service

        # Act
        results = service.suggest_waypoints(trip_id=1, num_stops=1)

        # Assert
        assert len(results) > 0
        mock_location_service.find_locations_along_route.assert_called_once()

    def test_suggest_waypoints_round_trip(self, mock_db_session):
        """Test suggesting waypoints for round trip"""
        # Arrange
        mock_trip = Mock(spec=Trip)
        mock_trip.id = 2
        mock_trip.user_id = 123
        mock_trip.start_latitude = 50.8503
        mock_trip.start_longitude = 4.3517
        mock_trip.end_latitude = None
        mock_trip.end_longitude = None
        mock_trip.max_distance_km = 200

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_trip

        # Mock nearby locations
        mock_location = Mock()
        mock_location.id = 20
        mock_location.name = "Nearby Camping"
        mock_location.latitude = 51.0
        mock_location.longitude = 4.0
        mock_location.rating = 4.0

        mock_location_service = Mock()
        mock_location_service.find_nearby_locations.return_value = [
            {
                "location": mock_location,
                "distance_km": 30.0
            }
        ]

        # Mock recommendation service
        mock_recommendation_service = Mock()
        mock_recommendation_service.recommend_locations.return_value = [
            {
                "location": mock_location,
                "score": 0.85,
                "distance_km": 30.0
            }
        ]

        service = TripPlanningService(mock_db_session)
        service.location_service = mock_location_service
        service.recommendation_service = mock_recommendation_service

        # Act
        results = service.suggest_waypoints(trip_id=2, num_stops=2)

        # Assert
        assert len(results) > 0
        # Round trips use recommendation service, not find_nearby_locations
        mock_recommendation_service.recommend_locations.assert_called_once()
