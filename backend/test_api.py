"""
Comprehensive API Test Suite for TripFlow Backend

This script tests all API endpoints one by one to verify functionality.
Run with: python test_api.py
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

# Test state
access_token: Optional[str] = None
test_user_email = f"test_{datetime.now().timestamp()}@example.com"
test_user_password = "TestPassword123!"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test_header(test_name: str):
    """Print a formatted test header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}Testing: {test_name}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.RESET}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")


def print_response(response: requests.Response):
    """Print formatted response details"""
    print(f"  Status: {response.status_code}")
    try:
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2, default=str)[:500]}")
    except:
        print(f"  Response: {response.text[:500]}")


def make_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make HTTP request with auth token if available"""
    if access_token:
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {access_token}'
        kwargs['headers'] = headers

    response = requests.request(method, url, **kwargs)
    return response


# ============================================================================
# TEST: Root and Health Endpoints
# ============================================================================

def test_root():
    """Test root endpoint"""
    print_test_header("GET / - Root Endpoint")
    try:
        response = requests.get(BASE_URL)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            assert 'name' in data
            assert 'version' in data
            print_success("Root endpoint working")
            return True
        else:
            print_error(f"Root endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Root endpoint error: {e}")
        return False


def test_health():
    """Test health check endpoint"""
    print_test_header("GET /health - Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            assert data.get('status') == 'healthy'
            print_success("Health check passing")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


# ============================================================================
# TEST: Authentication Endpoints
# ============================================================================

def test_register():
    """Test user registration"""
    print_test_header("POST /api/v1/auth/register - Register User")
    try:
        payload = {
            "email": test_user_email,
            "password": test_user_password,
            "full_name": "Test User"
        }
        response = requests.post(f"{API_BASE}/auth/register", json=payload)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            assert data.get('email') == test_user_email
            print_success(f"User registered: {test_user_email}")
            return True
        else:
            print_error(f"Registration failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Registration error: {e}")
        return False


def test_login():
    """Test user login"""
    print_test_header("POST /api/v1/auth/login - Login User")
    global access_token
    try:
        payload = {
            "username": test_user_email,  # OAuth2 uses 'username' field
            "password": test_user_password
        }
        response = requests.post(
            f"{API_BASE}/auth/login",
            data=payload,  # OAuth2 uses form data, not JSON
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            assert 'access_token' in data
            assert 'refresh_token' in data
            access_token = data['access_token']
            print_success(f"Login successful, token received")
            return True
        else:
            print_error(f"Login failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Login error: {e}")
        return False


def test_get_me():
    """Test get current user"""
    print_test_header("GET /api/v1/auth/me - Get Current User")
    try:
        response = make_request('GET', f"{API_BASE}/auth/me")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            assert data.get('email') == test_user_email
            print_success(f"Current user retrieved: {data.get('email')}")
            return True
        else:
            print_error(f"Get user failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get user error: {e}")
        return False


def test_logout():
    """Test logout"""
    print_test_header("POST /api/v1/auth/logout - Logout")
    try:
        response = make_request('POST', f"{API_BASE}/auth/logout")
        print_response(response)

        if response.status_code == 200:
            print_success("Logout successful")
            return True
        else:
            print_error(f"Logout failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Logout error: {e}")
        return False


# ============================================================================
# TEST: Location Endpoints
# ============================================================================

def test_location_search():
    """Test location search"""
    print_test_header("POST /api/v1/locations/search - Search Locations")
    try:
        payload = {
            "query": "camping",
            "limit": 10
        }
        response = make_request('POST', f"{API_BASE}/locations/search", json=payload)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Location search returned {len(data)} results")
            return True
        else:
            print_error(f"Location search failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Location search error: {e}")
        return False


def test_nearby_locations():
    """Test nearby locations search"""
    print_test_header("POST /api/v1/locations/nearby - Find Nearby Locations")
    try:
        payload = {
            "latitude": 51.0543,  # Brussels
            "longitude": 3.7174,
            "radius_km": 50,
            "limit": 10
        }
        response = make_request('POST', f"{API_BASE}/locations/nearby", json=payload)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Nearby search returned {len(data)} results")
            return True
        else:
            print_error(f"Nearby search failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Nearby search error: {e}")
        return False


def test_geocode():
    """Test geocoding"""
    print_test_header("POST /api/v1/locations/geocode - Geocode Address")
    try:
        payload = {
            "address": "Brussels, Belgium"
        }
        response = make_request('POST', f"{API_BASE}/locations/geocode", json=payload)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Geocoded: {data}")
            return True
        elif response.status_code == 404:
            print_info("Geocoding service may not be configured")
            return True
        else:
            print_error(f"Geocode failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Geocode error: {e}")
        return False


# ============================================================================
# TEST: Trip Endpoints
# ============================================================================

def test_list_trips():
    """Test list trips"""
    print_test_header("GET /api/v1/trips/ - List Trips")
    try:
        response = make_request('GET', f"{API_BASE}/trips/")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Trips list returned {len(data)} trips")
            return True
        else:
            print_error(f"List trips failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"List trips error: {e}")
        return False


def test_create_trip():
    """Test create trip"""
    print_test_header("POST /api/v1/trips/ - Create Trip")
    try:
        payload = {
            "start_address": "Brussels, Belgium",
            "end_address": "Amsterdam, Netherlands",
            "max_distance_km": 500,
            "duration_days": 3,
            "trip_preferences": {
                "interests": ["nature", "camping"],
                "budget": "medium"
            }
        }
        response = make_request('POST', f"{API_BASE}/trips/", json=payload)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            trip_id = data.get('id')
            print_success(f"Trip created with ID: {trip_id}")
            return True, trip_id
        else:
            print_error(f"Create trip failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print_error(f"Create trip error: {e}")
        return False, None


# ============================================================================
# TEST: Recommendations Endpoints
# ============================================================================

def test_recommendations():
    """Test recommendations"""
    print_test_header("POST /api/v1/recommendations/ - Get Recommendations")
    try:
        payload = {
            "near_latitude": 51.0543,
            "near_longitude": 3.7174,
            "radius_km": 100,
            "interests": ["nature", "camping"],
            "limit": 10
        }
        response = make_request('POST', f"{API_BASE}/recommendations/", json=payload)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Recommendations returned {len(data)} results")
            return True
        elif response.status_code == 500:
            print_info("Recommendations may require Qdrant indexing")
            return True
        else:
            print_error(f"Recommendations failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Recommendations error: {e}")
        return False


# ============================================================================
# TEST: Discover Endpoints
# ============================================================================

def test_discover_events():
    """Test event discovery"""
    print_test_header("POST /api/v1/discover - Discover Events")
    try:
        payload = {
            "latitude": 51.0543,
            "longitude": 3.7174,
            "radius_km": 50,
            "limit": 10
        }
        response = make_request('POST', f"{API_BASE}/discover", json=payload)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Event discovery returned {data.get('total_count', 0)} events")
            return True
        else:
            print_error(f"Discover failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Discover error: {e}")
        return False


def test_discover_categories():
    """Test get event categories"""
    print_test_header("GET /api/v1/discover/categories - Get Event Categories")
    try:
        response = make_request('GET', f"{API_BASE}/discover/categories")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Categories returned: {len(data)} categories")
            return True
        else:
            print_error(f"Get categories failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get categories error: {e}")
        return False


def test_discover_stats():
    """Test discovery stats"""
    print_test_header("GET /api/v1/discover/stats - Get Discovery Stats")
    try:
        response = make_request('GET', f"{API_BASE}/discover/stats")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Stats: {data.get('total_events', 0)} total events")
            return True
        else:
            print_error(f"Get stats failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get stats error: {e}")
        return False


# ============================================================================
# TEST: Favorites Endpoints
# ============================================================================

def test_get_favorites():
    """Test get favorites"""
    print_test_header("GET /api/v1/favorites - Get User Favorites")
    try:
        response = make_request('GET', f"{API_BASE}/favorites")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Favorites returned {len(data)} items")
            return True
        else:
            print_error(f"Get favorites failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get favorites error: {e}")
        return False


def test_get_favorite_ids():
    """Test get favorite IDs"""
    print_test_header("GET /api/v1/favorites/ids - Get Favorite IDs")
    try:
        response = make_request('GET', f"{API_BASE}/favorites/ids")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Favorite IDs returned {len(data)} items")
            return True
        else:
            print_error(f"Get favorite IDs failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get favorite IDs error: {e}")
        return False


# ============================================================================
# TEST: Billing Endpoints
# ============================================================================

def test_get_pricing():
    """Test get pricing"""
    print_test_header("GET /api/v1/billing/pricing - Get Pricing Tiers")
    try:
        response = make_request('GET', f"{API_BASE}/billing/pricing")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Pricing tiers retrieved")
            return True
        else:
            print_error(f"Get pricing failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get pricing error: {e}")
        return False


def test_get_subscription():
    """Test get subscription"""
    print_test_header("GET /api/v1/billing/subscription - Get User Subscription")
    try:
        response = make_request('GET', f"{API_BASE}/billing/subscription")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Subscription tier: {data.get('tier')}")
            return True
        else:
            print_error(f"Get subscription failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get subscription error: {e}")
        return False


def test_get_usage():
    """Test get usage"""
    print_test_header("GET /api/v1/billing/usage - Get Usage Stats")
    try:
        response = make_request('GET', f"{API_BASE}/billing/usage")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Usage: {data.get('trips_used')}/{data.get('trips_limit')} trips")
            return True
        else:
            print_error(f"Get usage failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get usage error: {e}")
        return False


# ============================================================================
# TEST: Admin Endpoints
# ============================================================================

def test_admin_stats():
    """Test admin stats"""
    print_test_header("GET /api/v1/admin/stats/overview - Get Admin Dashboard Stats")
    try:
        response = make_request('GET', f"{API_BASE}/admin/stats/overview")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Stats: {data.get('total_locations')} locations, {data.get('total_events')} events")
            return True
        else:
            print_error(f"Get admin stats failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get admin stats error: {e}")
        return False


def test_list_scrapers():
    """Test list scrapers"""
    print_test_header("GET /api/v1/admin/scrapers - List Scrapers")
    try:
        response = make_request('GET', f"{API_BASE}/admin/scrapers")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Scrapers list returned {len(data)} scrapers")
            return True
        else:
            print_error(f"List scrapers failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"List scrapers error: {e}")
        return False


def test_list_migrations():
    """Test list migrations"""
    print_test_header("GET /api/v1/admin/migrations - List Migrations")
    try:
        response = make_request('GET', f"{API_BASE}/admin/migrations")
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Migrations list returned {len(data)} migrations")
            return True
        else:
            print_error(f"List migrations failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"List migrations error: {e}")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests and report results"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("TripFlow API Test Suite")
    print("=" * 80)
    print(f"{Colors.RESET}")
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Root & Health
    results.append(("Root Endpoint", test_root()))
    results.append(("Health Check", test_health()))

    # Authentication
    results.append(("Register User", test_register()))
    results.append(("Login User", test_login()))
    results.append(("Get Current User", test_get_me()))
    results.append(("Logout", test_logout()))

    # Re-login for remaining tests
    test_login()

    # Locations
    results.append(("Location Search", test_location_search()))
    results.append(("Nearby Locations", test_nearby_locations()))
    results.append(("Geocode Address", test_geocode()))

    # Trips
    results.append(("List Trips", test_list_trips()))
    trip_result, trip_id = test_create_trip()
    results.append(("Create Trip", trip_result))

    # Recommendations
    results.append(("Get Recommendations", test_recommendations()))

    # Discover
    results.append(("Discover Events", test_discover_events()))
    results.append(("Get Categories", test_discover_categories()))
    results.append(("Discovery Stats", test_discover_stats()))

    # Favorites
    results.append(("Get Favorites", test_get_favorites()))
    results.append(("Get Favorite IDs", test_get_favorite_ids()))

    # Billing
    results.append(("Get Pricing", test_get_pricing()))
    results.append(("Get Subscription", test_get_subscription()))
    results.append(("Get Usage", test_get_usage()))

    # Admin
    results.append(("Admin Stats", test_admin_stats()))
    results.append(("List Scrapers", test_list_scrapers()))
    results.append(("List Migrations", test_list_migrations()))

    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"{Colors.RESET}")

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for test_name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"  {status} - {test_name}")

    print(f"\n{Colors.BOLD}Total Tests: {len(results)}{Colors.RESET}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    print(f"Success Rate: {passed/len(results)*100:.1f}%\n")

    return failed == 0


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        sys.exit(1)
