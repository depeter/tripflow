"""
Unit tests for LocationService

These tests mock the database and external APIs to test business logic in isolation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.location_service import LocationService
from app.models import Location, LocationType


@pytest.mark.unit
class TestLocationService:
    """Test LocationService business logic"""

    def test_get_location_by_id(self, mock_db_session, sample_location_data):
        """Test retrieving a location by ID"""
        # Arrange
        mock_location = Mock()
        mock_location.id = 1
        mock_location.name = "Beautiful Camping Spot"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_location

        service = LocationService(mock_db_session)

        # Act
        result = service.get_location_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.name == "Beautiful Camping Spot"
        mock_db_session.query.assert_called_once()

    def test_get_location_by_id_not_found(self, mock_db_session):
        """Test retrieving a non-existent location"""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        service = LocationService(mock_db_session)

        # Act
        result = service.get_location_by_id(999)

        # Assert
        assert result is None

    def test_search_locations_with_query(self, mock_db_session, sample_location_data):
        """Test searching locations with text query"""
        # Arrange
        mock_location = Mock()
        mock_location.name = "Beautiful Camping Spot"
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [mock_location]
        mock_db_session.query.return_value = mock_query

        service = LocationService(mock_db_session)

        # Act
        results = service.search_locations(query="camping", limit=10)

        # Assert
        assert len(results) == 1
        assert results[0].name == "Beautiful Camping Spot"
        # Verify filter was called for active locations
        assert mock_query.filter.called

    def test_search_locations_with_filters(self, mock_db_session):
        """Test searching locations with multiple filters"""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        service = LocationService(mock_db_session)

        # Act
        results = service.search_locations(
            query="beach",
            location_types=[LocationType.CAMPSITE],  # Fixed: CAMPSITE not CAMPING
            min_rating=4.0,
            max_price=30.0,
            amenities=["wifi"],
            tags=["nature"],
            limit=20
        )

        # Assert
        # Should have called filter multiple times (active, query, type, rating, price, amenities, tags)
        assert mock_query.filter.call_count >= 5
        assert mock_query.limit.called

    def test_find_nearby_locations_basic(self, mock_db_session):
        """Test finding nearby locations with PostGIS query"""
        # Arrange
        mock_location = Mock()
        mock_location.id = 1
        mock_location.name = "Nearby Location"

        # The query returns tuples of (Location, distance_meters)
        mock_tuple = (mock_location, 25500)  # distance in meters

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [mock_tuple]
        mock_db_session.query.return_value = mock_query

        service = LocationService(mock_db_session)

        # Act
        results = service.find_nearby_locations(
            latitude=51.0543,
            longitude=3.7174,
            radius_km=50,
            limit=10
        )

        # Assert
        assert len(results) == 1
        assert results[0]["location"].id == 1
        assert results[0]["distance_km"] == 25.5  # Converted from meters
        mock_db_session.query.assert_called_once()

    def test_find_nearby_locations_with_type_filter(self, mock_db_session):
        """Test finding nearby locations filtered by type"""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        service = LocationService(mock_db_session)

        # Act
        results = service.find_nearby_locations(
            latitude=51.0543,
            longitude=3.7174,
            radius_km=100,
            location_types=[LocationType.CAMPSITE, LocationType.PARKING],  # Fixed
            limit=20
        )

        # Assert
        assert len(results) == 0
        # Verify filter was called (including type filter)
        assert mock_query.filter.call_count >= 2

    @patch('geopy.geocoders.Nominatim')
    def test_geocode_address_success(self, mock_nominatim_class, mock_db_session):
        """Test successful address geocoding"""
        # Arrange
        mock_geocoder = Mock()
        mock_location = Mock()
        mock_location.latitude = 50.8503
        mock_location.longitude = 4.3517
        mock_geocoder.geocode.return_value = mock_location
        mock_nominatim_class.return_value = mock_geocoder

        service = LocationService(mock_db_session)

        # Act
        result = service.geocode_address("Brussels, Belgium")

        # Assert
        assert result is not None
        assert result["latitude"] == 50.8503
        assert result["longitude"] == 4.3517
        mock_geocoder.geocode.assert_called_once()

    @patch('geopy.geocoders.Nominatim')
    def test_geocode_address_not_found(self, mock_nominatim_class, mock_db_session):
        """Test geocoding with invalid address"""
        # Arrange
        mock_geocoder = Mock()
        mock_geocoder.geocode.return_value = None
        mock_nominatim_class.return_value = mock_geocoder

        service = LocationService(mock_db_session)

        # Act
        result = service.geocode_address("Invalid Address XYZ123")

        # Assert
        assert result is None
        mock_geocoder.geocode.assert_called_once()

    @patch('geopy.geocoders.Nominatim')
    def test_reverse_geocode_success(self, mock_nominatim_class, mock_db_session):
        """Test successful reverse geocoding"""
        # Arrange
        mock_geocoder = Mock()
        mock_location = Mock()
        mock_location.address = "Brussels, Belgium"
        mock_geocoder.reverse.return_value = mock_location
        mock_nominatim_class.return_value = mock_geocoder

        service = LocationService(mock_db_session)

        # Act
        result = service.reverse_geocode(50.8503, 4.3517)

        # Assert
        assert result == "Brussels, Belgium"
        mock_geocoder.reverse.assert_called_once()

    @patch('geopy.geocoders.Nominatim')
    def test_reverse_geocode_failure(self, mock_nominatim_class, mock_db_session):
        """Test reverse geocoding with invalid coordinates"""
        # Arrange
        mock_geocoder = Mock()
        mock_geocoder.reverse.return_value = None
        mock_nominatim_class.return_value = mock_geocoder

        service = LocationService(mock_db_session)

        # Act
        result = service.reverse_geocode(999, 999)

        # Assert
        assert result is None
        mock_geocoder.reverse.assert_called_once()
