"""
Integration tests for the discover API endpoint.
Tests the deployed API at https://tripflow.pm-consulting.be
"""
import requests
import pytest


BASE_URL = "https://tripflow.pm-consulting.be/api/v1"


def test_discover_basic_search():
    """Test basic discover search returns results"""
    payload = {
        "latitude": 51.0543,
        "longitude": 3.7174,
        "radius_km": 25,
        "limit": 5
    }

    response = requests.post(f"{BASE_URL}/discover", json=payload, verify=False)

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"

    data = response.json()
    assert "events" in data
    assert "locations" in data
    assert "total_count" in data
    assert "search_center" in data
    assert "radius_km" in data

    # Verify we got results
    assert data["total_count"] > 0, "Expected some results but got none"

    # Verify search center matches request
    assert data["search_center"]["latitude"] == 51.0543
    assert data["search_center"]["longitude"] == 3.7174
    assert data["radius_km"] == 25


def test_discover_with_location_filters():
    """Test discover with location filters"""
    payload = {
        "latitude": 51.0543,
        "longitude": 3.7174,
        "radius_km": 50,
        "item_types": ["locations"],
        "location_filters": {
            "location_types": ["CAMPSITE", "PARKING"],
            "min_rating": 3.0
        },
        "limit": 10
    }

    response = requests.post(f"{BASE_URL}/discover", json=payload, verify=False)

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"

    data = response.json()
    assert isinstance(data["locations"], list)

    # Verify locations match filters if we got results
    if len(data["locations"]) > 0:
        for loc in data["locations"]:
            assert loc["location_type"] in ["CAMPSITE", "PARKING"]
            if loc["rating"] is not None:
                assert loc["rating"] >= 3.0


def test_discover_with_event_filters():
    """Test discover with event filters"""
    payload = {
        "latitude": 51.0543,
        "longitude": 3.7174,
        "radius_km": 25,
        "item_types": ["events"],
        "event_filters": {
            "categories": ["concert", "theater"],
            "free_only": False
        },
        "limit": 5
    }

    response = requests.post(f"{BASE_URL}/discover", json=payload, verify=False)

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"

    data = response.json()
    assert isinstance(data["events"], list)

    # Verify events match filters if we got results
    if len(data["events"]) > 0:
        for event in data["events"]:
            # Category should be one of the requested ones (case insensitive)
            assert event["category"].lower() in ["concert", "theater"], \
                f"Expected concert or theater, got {event['category']}"


def test_discover_corridor_search():
    """Test corridor (route) search between two points"""
    payload = {
        "latitude": 51.0543,  # Ghent
        "longitude": 3.7174,
        "destination_latitude": 50.8503,  # Brussels
        "destination_longitude": 4.3517,
        "corridor_width_km": 10,
        "max_distance_km": 100,
        "item_types": ["events"],
        "limit": 5
    }

    response = requests.post(f"{BASE_URL}/discover", json=payload, verify=False)

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"

    data = response.json()
    assert "events" in data
    # Should have results along the Ghent-Brussels corridor
    assert isinstance(data["events"], list)


def test_discover_with_text_search():
    """Test text search in discover"""
    payload = {
        "latitude": 51.0543,
        "longitude": 3.7174,
        "radius_km": 50,
        "search_text": "festival",
        "limit": 10
    }

    response = requests.post(f"{BASE_URL}/discover", json=payload, verify=False)

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"

    data = response.json()
    # Should filter by text (in name, description, venue, etc.)
    assert isinstance(data["events"], list)


def test_discover_date_range_filter():
    """Test filtering events by date range"""
    from datetime import datetime, timedelta

    start_date = datetime.now().isoformat()
    end_date = (datetime.now() + timedelta(days=30)).isoformat()

    payload = {
        "latitude": 51.0543,
        "longitude": 3.7174,
        "radius_km": 25,
        "item_types": ["events"],
        "event_filters": {
            "date_start": start_date,
            "date_end": end_date
        },
        "limit": 10
    }

    response = requests.post(f"{BASE_URL}/discover", json=payload, verify=False)

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"

    data = response.json()
    assert isinstance(data["events"], list)

    # Verify events are within date range if we got results
    if len(data["events"]) > 0:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        for event in data["events"]:
            event_start = datetime.fromisoformat(event["start_datetime"])
            assert event_start >= start_dt.replace(tzinfo=None)
            assert event_start <= end_dt.replace(tzinfo=None)


def test_discover_handles_wikidata_source():
    """Test that discover can handle locations from wikidata source"""
    payload = {
        "latitude": 51.0543,
        "longitude": 3.7174,
        "radius_km": 100,
        "item_types": ["locations"],
        "limit": 50
    }

    response = requests.post(f"{BASE_URL}/discover", json=payload, verify=False)

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"

    data = response.json()

    # Find if any locations have wikidata as source
    wikidata_locations = [loc for loc in data["locations"] if loc.get("source") == "wikidata"]

    # This was the bug - it should not crash even if wikidata locations exist
    print(f"Found {len(wikidata_locations)} wikidata locations in results")


def test_discover_handles_all_location_sources():
    """Test that discover can handle all location sources without enum errors"""
    payload = {
        "latitude": 51.0543,
        "longitude": 3.7174,
        "radius_km": 100,
        "item_types": ["locations"],
        "limit": 100
    }

    response = requests.post(f"{BASE_URL}/discover", json=payload, verify=False)

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"

    data = response.json()

    # Collect all unique sources
    sources = set(loc.get("source") for loc in data["locations"])
    print(f"Found locations from sources: {sources}")

    # Verify we can handle wikidata, visitwallonia, dagjeweg
    expected_sources = ["wikidata", "visitwallonia", "dagjeweg"]
    for expected in expected_sources:
        if expected in sources:
            print(f"✓ Successfully handled {expected} source")


if __name__ == "__main__":
    # Run tests
    import sys

    print("Running integration tests for discover API...")
    print("=" * 70)

    tests = [
        ("Basic search", test_discover_basic_search),
        ("Location filters", test_discover_with_location_filters),
        ("Event filters", test_discover_with_event_filters),
        ("Corridor search", test_discover_corridor_search),
        ("Text search", test_discover_with_text_search),
        ("Date range filter", test_discover_date_range_filter),
        ("Wikidata source handling", test_discover_handles_wikidata_source),
        ("All location sources", test_discover_handles_all_location_sources),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"\nTest: {name}")
            test_func()
            print(f"✓ PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")

    sys.exit(0 if failed == 0 else 1)
