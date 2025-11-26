"""Tests for the discover endpoint with location filters"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_discover_with_location_filters():
    """Test discovery endpoint with nested location_filters object"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with location filters as nested object
        payload = {
            "latitude": 51.0543,
            "longitude": 3.7174,
            "radius_km": 25,
            "item_types": ["locations"],
            "location_filters": {
                "location_types": ["CAMPSITE", "PARKING"],
                "min_rating": 4.0,
                "is_24_7": True
            }
        }

        response = await client.post("/api/v1/discover", json=payload)

        # Should return 200 even if no results (empty database)
        assert response.status_code == 200

        data = response.json()
        assert "locations" in data
        assert "events" in data
        assert "total_count" in data
        assert isinstance(data["locations"], list)


@pytest.mark.asyncio
async def test_discover_with_event_filters():
    """Test discovery endpoint with nested event_filters object"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with event filters as nested object
        payload = {
            "latitude": 51.0543,
            "longitude": 3.7174,
            "radius_km": 25,
            "item_types": ["events"],
            "event_filters": {
                "categories": ["MUSIC", "FESTIVAL"],
                "free_only": True,
                "time_of_day": ["evening"]
            }
        }

        response = await client.post("/api/v1/discover", json=payload)

        assert response.status_code == 200

        data = response.json()
        assert "events" in data
        assert "locations" in data
        assert isinstance(data["events"], list)


@pytest.mark.asyncio
async def test_discover_with_both_filters():
    """Test discovery endpoint with both event and location filters"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with both filter types (though only one will be applied based on item_types)
        payload = {
            "latitude": 51.0543,
            "longitude": 3.7174,
            "radius_km": 25,
            "item_types": ["events", "locations"],
            "event_filters": {
                "categories": ["MUSIC"],
                "free_only": False
            },
            "location_filters": {
                "location_types": ["CAMPSITE"],
                "min_rating": 3.5
            }
        }

        response = await client.post("/api/v1/discover", json=payload)

        assert response.status_code == 200

        data = response.json()
        assert "events" in data
        assert "locations" in data


@pytest.mark.asyncio
async def test_discover_without_filters():
    """Test discovery endpoint without any filters (should return all nearby)"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "latitude": 51.0543,
            "longitude": 3.7174,
            "radius_km": 25
        }

        response = await client.post("/api/v1/discover", json=payload)

        assert response.status_code == 200

        data = response.json()
        assert "events" in data
        assert "locations" in data


@pytest.mark.asyncio
async def test_discover_legacy_event_filters():
    """Test that legacy flat event filters still work for backwards compatibility"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with old-style flat parameters (should still work due to fallback)
        payload = {
            "latitude": 51.0543,
            "longitude": 3.7174,
            "radius_km": 25,
            "item_types": ["events"],
            "categories": ["MUSIC"],
            "free_only": True
        }

        response = await client.post("/api/v1/discover", json=payload)

        # Should still work for events (legacy support exists)
        assert response.status_code == 200

        data = response.json()
        assert "events" in data
