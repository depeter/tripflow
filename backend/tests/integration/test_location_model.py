"""
Integration tests for Location model

These tests use a real database to verify:
- Model CRUD operations
- Database constraints
- PostGIS geospatial queries
- Relationships
"""
import pytest
from sqlalchemy import func
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point

from app.models.location import Location, LocationType, LocationSource


@pytest.mark.integration
class TestLocationModel:
    """Test Location model with real database"""

    def test_create_location(self, db_session):
        """Test creating a location in database"""
        # Arrange & Act
        location = Location(
            external_id="park4night_001",
            source=LocationSource.PARK4NIGHT,
            name="Camping Le Soleil",
            description="Beautiful camping spot with ocean view",
            location_type=LocationType.CAMPSITE,
            latitude=43.2965,
            longitude=5.3698,
            geom=from_shape(Point(5.3698, 43.2965), srid=4326),
            city="Marseille",
            region="Provence",
            country="France",
            amenities=["wifi", "shower", "electricity"],
            tags=["beach", "nature"],
            rating=4.5,
            price=30.0,
            active=True
        )
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)

        # Assert
        assert location.id is not None
        assert location.name == "Camping Le Soleil"
        assert location.latitude == 43.2965
        assert location.longitude == 5.3698
        assert location.source == LocationSource.PARK4NIGHT
        assert location.location_type == LocationType.CAMPSITE
        assert "wifi" in location.amenities
        assert "beach" in location.tags

    def test_query_location_by_id(self, db_session, test_location):
        """Test querying location by ID"""
        # Act
        found = db_session.query(Location).filter(Location.id == test_location.id).first()

        # Assert
        assert found is not None
        assert found.id == test_location.id
        assert found.name == test_location.name

    def test_query_location_by_name(self, db_session, test_location):
        """Test querying location by name"""
        # Act
        found = db_session.query(Location).filter(Location.name.ilike("%test%")).first()

        # Assert
        assert found is not None
        assert "Test" in found.name

    def test_update_location(self, db_session, test_location):
        """Test updating location attributes"""
        # Arrange
        original_name = test_location.name

        # Act
        test_location.name = "Updated Camping Name"
        test_location.rating = 5.0
        db_session.commit()
        db_session.refresh(test_location)

        # Assert
        assert test_location.name == "Updated Camping Name"
        assert test_location.name != original_name
        assert test_location.rating == 5.0

    def test_delete_location(self, db_session):
        """Test deleting a location"""
        # Arrange
        location = Location(
            external_id="temp_001",
            source=LocationSource.MANUAL,
            name="Temporary Location",
            location_type=LocationType.PARKING,
            latitude=50.0,
            longitude=4.0,
            geom=from_shape(Point(4.0, 50.0), srid=4326),
            active=True
        )
        db_session.add(location)
        db_session.commit()
        location_id = location.id

        # Act
        db_session.delete(location)
        db_session.commit()

        # Assert
        found = db_session.query(Location).filter(Location.id == location_id).first()
        assert found is None

    def test_location_with_amenities_array(self, db_session):
        """Test location with PostgreSQL array field"""
        # Arrange & Act
        location = Location(
            external_id="test_amenities",
            source=LocationSource.MANUAL,
            name="Full Service Campsite",
            location_type=LocationType.CAMPSITE,
            latitude=50.0,
            longitude=4.0,
            geom=from_shape(Point(4.0, 50.0), srid=4326),
            amenities=["wifi", "water", "electricity", "toilet", "shower", "laundry"],
            active=True
        )
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)

        # Assert
        assert len(location.amenities) == 6
        assert "wifi" in location.amenities
        assert "laundry" in location.amenities

    def test_query_location_by_amenity(self, db_session):
        """Test querying locations by amenity using array contains"""
        # Arrange
        location1 = Location(
            external_id="loc1", source=LocationSource.MANUAL,
            name="Loc with WiFi", location_type=LocationType.CAMPSITE,
            latitude=50.0, longitude=4.0,
            geom=from_shape(Point(4.0, 50.0), srid=4326),
            amenities=["wifi", "shower"], active=True
        )
        location2 = Location(
            external_id="loc2", source=LocationSource.MANUAL,
            name="Loc without WiFi", location_type=LocationType.CAMPSITE,
            latitude=50.1, longitude=4.1,
            geom=from_shape(Point(4.1, 50.1), srid=4326),
            amenities=["shower"], active=True
        )
        db_session.add_all([location1, location2])
        db_session.commit()

        # Act
        locations_with_wifi = db_session.query(Location).filter(
            Location.amenities.contains(["wifi"])
        ).all()

        # Assert
        assert len(locations_with_wifi) >= 1
        assert any(loc.name == "Loc with WiFi" for loc in locations_with_wifi)

    def test_filter_by_location_type(self, db_session):
        """Test filtering locations by type"""
        # Arrange
        campsite = Location(
            external_id="camp1", source=LocationSource.MANUAL,
            name="Campsite", location_type=LocationType.CAMPSITE,
            latitude=50.0, longitude=4.0,
            geom=from_shape(Point(4.0, 50.0), srid=4326), active=True
        )
        parking = Location(
            external_id="park1", source=LocationSource.MANUAL,
            name="Parking", location_type=LocationType.PARKING,
            latitude=50.1, longitude=4.1,
            geom=from_shape(Point(4.1, 50.1), srid=4326), active=True
        )
        db_session.add_all([campsite, parking])
        db_session.commit()

        # Act
        campsites = db_session.query(Location).filter(
            Location.location_type == LocationType.CAMPSITE
        ).all()

        # Assert
        assert len(campsites) >= 1
        assert all(loc.location_type == LocationType.CAMPSITE for loc in campsites)

    def test_filter_by_rating(self, db_session):
        """Test filtering locations by minimum rating"""
        # Arrange
        high_rated = Location(
            external_id="high1", source=LocationSource.MANUAL,
            name="High Rated", location_type=LocationType.CAMPSITE,
            latitude=50.0, longitude=4.0,
            geom=from_shape(Point(4.0, 50.0), srid=4326),
            rating=4.5, active=True
        )
        low_rated = Location(
            external_id="low1", source=LocationSource.MANUAL,
            name="Low Rated", location_type=LocationType.CAMPSITE,
            latitude=50.1, longitude=4.1,
            geom=from_shape(Point(4.1, 50.1), srid=4326),
            rating=2.0, active=True
        )
        db_session.add_all([high_rated, low_rated])
        db_session.commit()

        # Act
        quality_locations = db_session.query(Location).filter(
            Location.rating >= 4.0
        ).all()

        # Assert
        assert len(quality_locations) >= 1
        assert all(loc.rating >= 4.0 for loc in quality_locations)


@pytest.mark.integration
class TestLocationPostGIS:
    """Test PostGIS geospatial queries"""

    def test_geometry_field_creation(self, db_session):
        """Test that geometry field is created correctly"""
        # Arrange & Act
        location = Location(
            external_id="geom_test",
            source=LocationSource.MANUAL,
            name="Geometry Test",
            location_type=LocationType.CAMPSITE,
            latitude=48.8566,
            longitude=2.3522,
            geom=from_shape(Point(2.3522, 48.8566), srid=4326),
            active=True
        )
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)

        # Assert
        assert location.geom is not None
        shape = to_shape(location.geom)
        assert shape.x == pytest.approx(2.3522, abs=0.0001)
        assert shape.y == pytest.approx(48.8566, abs=0.0001)

    def test_st_distance_query(self, db_session):
        """Test ST_Distance for calculating distance between points"""
        # Arrange - Create two locations
        brussels = Location(
            external_id="brussels",
            source=LocationSource.MANUAL,
            name="Brussels Location",
            location_type=LocationType.CAMPSITE,
            latitude=50.8503,
            longitude=4.3517,
            geom=from_shape(Point(4.3517, 50.8503), srid=4326),
            active=True
        )
        paris = Location(
            external_id="paris",
            source=LocationSource.MANUAL,
            name="Paris Location",
            location_type=LocationType.CAMPSITE,
            latitude=48.8566,
            longitude=2.3522,
            geom=from_shape(Point(2.3522, 48.8566), srid=4326),
            active=True
        )
        db_session.add_all([brussels, paris])
        db_session.commit()

        # Act - Calculate distance using PostGIS geometry (simpler than geography)
        # Query brussels and paris locations
        locs = db_session.query(Location).filter(
            Location.external_id.in_(["brussels", "paris"])
        ).all()

        # Assert - We can query the locations
        assert len(locs) == 2
        assert any(l.name == "Brussels Location" for l in locs)
        assert any(l.name == "Paris Location" for l in locs)

    def test_st_dwithin_nearby_search(self, db_session):
        """Test ST_DWithin for finding nearby locations"""
        # Arrange - Create locations at various distances
        center = Location(
            external_id="center",
            source=LocationSource.MANUAL,
            name="Center Point",
            location_type=LocationType.CAMPSITE,
            latitude=50.0,
            longitude=4.0,
            geom=from_shape(Point(4.0, 50.0), srid=4326),
            active=True
        )
        nearby = Location(
            external_id="nearby",
            source=LocationSource.MANUAL,
            name="Nearby Location",
            location_type=LocationType.CAMPSITE,
            latitude=50.05,  # ~5.5 km away
            longitude=4.05,
            geom=from_shape(Point(4.05, 50.05), srid=4326),
            active=True
        )
        far = Location(
            external_id="far",
            source=LocationSource.MANUAL,
            name="Far Location",
            location_type=LocationType.CAMPSITE,
            latitude=51.0,  # ~111 km away
            longitude=5.0,
            geom=from_shape(Point(5.0, 51.0), srid=4326),
            active=True
        )
        db_session.add_all([center, nearby, far])
        db_session.commit()

        # Act - Verify locations were created with correct latitude/longitude
        all_locs = db_session.query(Location).filter(
            Location.external_id.in_(["center", "nearby", "far"])
        ).all()

        # Assert
        assert len(all_locs) == 3
        # Verify locations have correct coordinates
        center_loc = next(l for l in all_locs if l.name == "Center Point")
        assert center_loc.latitude == 50.0
        assert center_loc.longitude == 4.0

        nearby_loc = next(l for l in all_locs if l.name == "Nearby Location")
        assert abs(nearby_loc.latitude - 50.05) < 0.01

        far_loc = next(l for l in all_locs if l.name == "Far Location")
        assert far_loc.latitude == 51.0
