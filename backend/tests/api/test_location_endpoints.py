"""
API tests for location endpoints

Tests the HTTP API layer with mocked database and services:
- GET /api/v1/locations/{location_id} - Get location by ID
- POST /api/v1/locations/search - Search locations
- POST /api/v1/locations/nearby - Find nearby locations
- POST /api/v1/locations/geocode - Geocode address
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import status
from app.models.location import LocationType, LocationSource
from datetime import datetime


def create_mock_location(
    id=1,
    name="Test Location",
    description="Test description",
    latitude=50.0,
    longitude=4.0,
    location_type=LocationType.CAMPSITE,
    source=LocationSource.MANUAL,
    **kwargs
):
    """Helper to create properly configured location mock"""
    defaults = {
        'id': id,
        'name': name,
        'description': description,
        'location_type': location_type,
        'latitude': latitude,
        'longitude': longitude,
        'address': kwargs.get('address'),
        'city': kwargs.get('city'),
        'region': kwargs.get('region'),
        'country': kwargs.get('country'),
        'amenities': kwargs.get('amenities', []),
        'rating': kwargs.get('rating', 4.5),
        'price': kwargs.get('price', 25.0),
        'website': kwargs.get('website'),
        'images': kwargs.get('images', []),
        'tags': kwargs.get('tags', []),
        'active': kwargs.get('active', True),
        'review_count': kwargs.get('review_count', 0),
        'created_at': kwargs.get('created_at', datetime(2025, 11, 19, 10, 0, 0)),
        'source': source,
    }

    # Create mock with spec to avoid Mock objects as attributes
    mock_loc = Mock()
    for key, value in defaults.items():
        setattr(mock_loc, key, value)

    return mock_loc


@pytest.mark.api
class TestLocationEndpoints:
    """Test location API endpoints"""

    def test_get_location_by_id_success(self, test_client, mock_db_session):
        """Test getting location by ID"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        location_id = 1

        with patch('app.api.locations.LocationService') as MockService:
            # Mock location service with properly configured mock
            mock_location = create_mock_location(
                id=location_id,
                name="Test Camping Spot",
                description="Beautiful location",
                latitude=50.8503,
                longitude=4.3517,
                amenities=["wifi", "shower"],
                tags=["nature"]
            )
            MockService.return_value.get_location_by_id.return_value = mock_location

            # Override database dependency
            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.get(f"/api/v1/locations/{location_id}")

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == location_id
                assert data["name"] == "Test Camping Spot"
                assert data["latitude"] == 50.8503
            finally:
                app.dependency_overrides.clear()

    def test_get_location_by_id_not_found(self, test_client, mock_db_session):
        """Test getting non-existent location"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        location_id = 999

        with patch('app.api.locations.LocationService') as MockService:
            # Mock location not found
            MockService.return_value.get_location_by_id.return_value = None

            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.get(f"/api/v1/locations/{location_id}")

                # Assert
                assert response.status_code == status.HTTP_404_NOT_FOUND
            finally:
                app.dependency_overrides.clear()

    def test_search_locations_success(self, test_client, mock_db_session):
        """Test searching locations with filters"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        search_params = {
            "query": "camping",
            "location_types": ["campsite"],  # API uses lowercase
            "min_rating": 4.0,
            "max_price": 50.0,
            "amenities": ["wifi"],
            "limit": 10
        }

        with patch('app.api.locations.LocationService') as MockService:
            # Mock search results with properly configured mocks
            mock_locations = [
                create_mock_location(
                    id=1,
                    name="Camping A",
                    latitude=50.0,
                    longitude=4.0,
                    rating=4.5,
                    price=30.0,
                    amenities=["wifi", "shower"]
                ),
                create_mock_location(
                    id=2,
                    name="Camping B",
                    latitude=50.1,
                    longitude=4.1,
                    rating=4.2,
                    price=25.0,
                    amenities=["wifi"]
                )
            ]
            MockService.return_value.search_locations.return_value = mock_locations

            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.post(
                    "/api/v1/locations/search",
                    json=search_params
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data) == 2
                assert data[0]["name"] == "Camping A"
                assert data[1]["name"] == "Camping B"
            finally:
                app.dependency_overrides.clear()

    def test_search_locations_empty_results(self, test_client, mock_db_session):
        """Test search with no matching locations"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        search_params = {
            "query": "nonexistent",
            "limit": 10
        }

        with patch('app.api.locations.LocationService') as MockService:
            # Mock empty results
            MockService.return_value.search_locations.return_value = []

            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.post(
                    "/api/v1/locations/search",
                    json=search_params
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data) == 0
            finally:
                app.dependency_overrides.clear()

    def test_find_nearby_locations_success(self, test_client, mock_db_session):
        """Test finding nearby locations"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        nearby_params = {
            "latitude": 50.8503,
            "longitude": 4.3517,
            "radius_km": 50,
            "location_types": ["campsite"],  # API uses lowercase
            "limit": 10
        }

        with patch('app.api.locations.LocationService') as MockService:
            # Mock nearby locations with distance (returned as dict from service)
            mock_location_1 = create_mock_location(
                id=1,
                name="Nearby Camping A",
                latitude=50.85,
                longitude=4.35,
                rating=4.5,
                price=30.0
            )

            mock_location_2 = create_mock_location(
                id=2,
                name="Nearby Camping B",
                latitude=50.88,
                longitude=4.38,
                rating=4.2,
                price=25.0
            )

            mock_results = [
                {"location": mock_location_1, "distance_km": 5.5},
                {"location": mock_location_2, "distance_km": 12.0}
            ]
            MockService.return_value.find_nearby_locations.return_value = mock_results

            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.post(
                    "/api/v1/locations/nearby",
                    json=nearby_params
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data) == 2
                assert data[0]["name"] == "Nearby Camping A"
                assert data[0]["distance_km"] == pytest.approx(5.5, abs=0.1)
                assert data[1]["distance_km"] == pytest.approx(12.0, abs=0.1)
            finally:
                app.dependency_overrides.clear()

    def test_find_nearby_locations_empty_results(self, test_client, mock_db_session):
        """Test nearby search with no matching locations"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        nearby_params = {
            "latitude": 50.8503,
            "longitude": 4.3517,
            "radius_km": 50,
            "limit": 10
        }

        with patch('app.api.locations.LocationService') as MockService:
            # Mock empty results
            MockService.return_value.find_nearby_locations.return_value = []

            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.post(
                    "/api/v1/locations/nearby",
                    json=nearby_params
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data) == 0
            finally:
                app.dependency_overrides.clear()

    def test_geocode_address_success(self, test_client, mock_db_session):
        """Test geocoding an address"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        geocode_params = {
            "address": "Brussels, Belgium"
        }

        with patch('app.api.locations.LocationService') as MockService:
            # Mock geocoding result (returns dict, not Location object)
            mock_result = {
                "address": "Brussels, Belgium",
                "latitude": 50.8503,
                "longitude": 4.3517,
                "display_name": "Brussels, Brussels-Capital, Belgium"
            }
            MockService.return_value.geocode_address.return_value = mock_result

            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.post(
                    "/api/v1/locations/geocode",
                    json=geocode_params
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["latitude"] == 50.8503
                assert data["longitude"] == 4.3517
                assert "Brussels" in data["display_name"]
            finally:
                app.dependency_overrides.clear()

    def test_geocode_address_not_found(self, test_client, mock_db_session):
        """Test geocoding with invalid address"""
        # Arrange
        from app.db.database import get_db
        from app.main import app

        geocode_params = {
            "address": "Nonexistent Place 12345"
        }

        with patch('app.api.locations.LocationService') as MockService:
            # Mock geocoding failure
            MockService.return_value.geocode_address.return_value = None

            app.dependency_overrides[get_db] = lambda: mock_db_session

            try:
                # Act
                response = test_client.post(
                    "/api/v1/locations/geocode",
                    json=geocode_params
                )

                # Assert
                assert response.status_code == status.HTTP_404_NOT_FOUND
            finally:
                app.dependency_overrides.clear()
