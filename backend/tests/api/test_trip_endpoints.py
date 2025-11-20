"""
API tests for trip endpoints

Tests the HTTP API layer with mocked services:
- GET /api/v1/trips/{trip_id} - Get trip by ID
- POST /api/v1/trips/ - Create new trip
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import status
from app.models.trip import TripStatus
from datetime import datetime


def create_mock_trip(
    id=1,
    user_id=1,
    name=None,
    status=TripStatus.PLANNING,
    start_address="Test Start",
    start_latitude=50.0,
    start_longitude=4.0,
    end_address="Test End",
    end_latitude=51.0,
    end_longitude=5.0,
    **kwargs
):
    """Helper to create properly configured trip mock"""
    from datetime import date
    mock_trip = Mock()
    mock_trip.id = id
    mock_trip.user_id = user_id
    mock_trip.name = name
    mock_trip.status = status
    mock_trip.start_address = start_address
    mock_trip.start_latitude = start_latitude
    mock_trip.start_longitude = start_longitude
    mock_trip.end_address = end_address
    mock_trip.end_latitude = end_latitude
    mock_trip.end_longitude = end_longitude
    mock_trip.max_distance_km = kwargs.get('max_distance_km')
    mock_trip.duration_days = kwargs.get('duration_days')
    mock_trip.waypoints = kwargs.get('waypoints', [])
    mock_trip.start_date = kwargs.get('start_date', date(2025, 12, 1))
    mock_trip.end_date = kwargs.get('end_date', date(2025, 12, 4))
    mock_trip.created_at = kwargs.get('created_at', datetime(2025, 11, 19, 10, 0, 0))
    mock_trip.updated_at = kwargs.get('updated_at', datetime(2025, 11, 19, 10, 0, 0))
    return mock_trip


@pytest.mark.api
class TestTripEndpoints:
    """Test trip API endpoints"""

    def test_get_trip_by_id_success(self, test_client, mock_db_session):
        """Test getting trip by ID"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        trip_id = 1

        # Mock the query chain
        mock_query = MagicMock()
        mock_trip = create_mock_trip(id=trip_id, name="My Trip")
        mock_query.filter.return_value.first.return_value = mock_trip
        mock_db_session.query.return_value = mock_query

        app.dependency_overrides[get_db] = lambda: mock_db_session

        try:
            # Act
            response = test_client.get(f"/api/v1/trips/{trip_id}")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == trip_id
            assert data["name"] == "My Trip"
        finally:
            app.dependency_overrides.clear()

    def test_get_trip_not_found(self, test_client, mock_db_session):
        """Test getting non-existent trip"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        trip_id = 999

        # Mock the query chain to return None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        app.dependency_overrides[get_db] = lambda: mock_db_session

        try:
            # Act
            response = test_client.get(f"/api/v1/trips/{trip_id}")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
        finally:
            app.dependency_overrides.clear()

    def test_create_trip_success(self, test_client, mock_db_session):
        """Test creating a new trip"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        trip_data = {
            "start_address": "Brussels, Belgium",
            "end_address": "Amsterdam, Netherlands",
            "max_distance_km": 500,
            "duration_days": 3,
            "trip_preferences": {
                "interests": ["nature", "camping"],
                "budget": "medium"
            }
        }

        with patch('app.api.trips.TripPlanningService') as MockService:
            # Mock trip creation
            mock_trip = create_mock_trip(
                id=1,
                user_id=1,
                start_address=trip_data["start_address"],
                end_address=trip_data["end_address"],
                start_latitude=50.8503,
                start_longitude=4.3517,
                end_latitude=52.3676,
                end_longitude=4.9041,
                max_distance_km=trip_data["max_distance_km"],
                duration_days=trip_data["duration_days"]
            )
            MockService.return_value.create_trip.return_value = mock_trip

            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.post(
                    "/api/v1/trips/",
                    json=trip_data
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == 1
                assert data["start_address"] == trip_data["start_address"]
                assert data["end_address"] == trip_data["end_address"]
            finally:
                app.dependency_overrides.clear()

    def test_create_round_trip(self, test_client, mock_db_session):
        """Test creating a round trip (no end address)"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        trip_data = {
            "start_address": "Brussels, Belgium",
            "max_distance_km": 300,
            "duration_days": 2
        }

        with patch('app.api.trips.TripPlanningService') as MockService:
            # Mock trip creation
            mock_trip = create_mock_trip(
                id=1,
                user_id=1,
                start_address=trip_data["start_address"],
                end_address=None,
                start_latitude=50.8503,
                start_longitude=4.3517,
                end_latitude=None,
                end_longitude=None,
                max_distance_km=trip_data["max_distance_km"],
                duration_days=trip_data["duration_days"]
            )
            MockService.return_value.create_trip.return_value = mock_trip

            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.post(
                    "/api/v1/trips/",
                    json=trip_data
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["end_address"] is None
            finally:
                app.dependency_overrides.clear()

    def test_list_trips_success(self, test_client, mock_db_session):
        """Test listing user's trips"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        # Mock the query chain
        mock_trips = [
            create_mock_trip(id=1, name="Trip 1", status=TripStatus.PLANNING),
            create_mock_trip(id=2, name="Trip 2", status=TripStatus.ACTIVE),
            create_mock_trip(id=3, name="Trip 3", status=TripStatus.COMPLETED),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_trips
        mock_db_session.query.return_value = mock_query

        app.dependency_overrides[get_db] = lambda: mock_db_session

        try:
            # Act
            response = test_client.get("/api/v1/trips/")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 3
            assert data[0]["name"] == "Trip 1"
            assert data[1]["name"] == "Trip 2"
            assert data[2]["name"] == "Trip 3"
        finally:
            app.dependency_overrides.clear()

    def test_list_trips_empty(self, test_client, mock_db_session):
        """Test listing trips when user has none"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        # Mock the query chain to return empty list
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        app.dependency_overrides[get_db] = lambda: mock_db_session

        try:
            # Act
            response = test_client.get("/api/v1/trips/")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 0
        finally:
            app.dependency_overrides.clear()
