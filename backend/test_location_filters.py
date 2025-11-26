#!/usr/bin/env python3
"""
Test script to verify location filters are working correctly
"""
import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
sys.path.insert(0, '/home/peter/work/tripflow/backend')

from app.db.database import get_db_session
from app.models.location import Location
from app.api.schemas import DiscoverySearchParams, LocationFiltersSchema


async def test_location_filters():
    """Test various location filter scenarios"""

    print("=" * 60)
    print("Testing Location Filters")
    print("=" * 60)

    async for db in get_db_session():
        # Test 1: Check total active locations
        print("\n1. Total active locations:")
        result = await db.execute(
            select(Location).filter(Location.active == True).limit(5)
        )
        locations = result.scalars().all()
        print(f"   Found {len(locations)} locations (showing first 5)")
        for loc in locations:
            print(f"   - {loc.name} ({loc.location_type}) - Rating: {loc.rating}")

        # Test 2: Filter by location type
        print("\n2. Filter by location type (CAMPSITE):")
        result = await db.execute(
            select(Location).filter(
                Location.active == True,
                Location.location_type == 'CAMPSITE'
            ).limit(3)
        )
        campsites = result.scalars().all()
        print(f"   Found {len(campsites)} campsites")
        for loc in campsites:
            print(f"   - {loc.name}")

        # Test 3: Filter by minimum rating
        print("\n3. Filter by minimum rating (4.0+):")
        result = await db.execute(
            select(Location).filter(
                Location.active == True,
                Location.rating >= 4.0
            ).limit(3)
        )
        high_rated = result.scalars().all()
        print(f"   Found {len(high_rated)} locations")
        for loc in high_rated:
            print(f"   - {loc.name} - Rating: {loc.rating}")

        # Test 4: Check JSONB amenities structure
        print("\n4. Checking amenities JSONB structure:")
        result = await db.execute(
            select(Location).filter(
                Location.active == True,
                Location.amenities.isnot(None)
            ).limit(3)
        )
        locations_with_amenities = result.scalars().all()
        print(f"   Found {len(locations_with_amenities)} locations with amenities")
        for loc in locations_with_amenities:
            print(f"   - {loc.name}: {loc.amenities}")

        # Test 5: Check JSONB features structure
        print("\n5. Checking features JSONB structure:")
        result = await db.execute(
            select(Location).filter(
                Location.active == True,
                Location.features.isnot(None)
            ).limit(3)
        )
        locations_with_features = result.scalars().all()
        print(f"   Found {len(locations_with_features)} locations with features")
        for loc in locations_with_features:
            print(f"   - {loc.name}: {loc.features}")

        # Test 6: Test JSONB ? operator (check if amenity key exists)
        print("\n6. Testing JSONB ? operator for amenities:")
        try:
            result = await db.execute(
                select(Location).filter(
                    Location.active == True,
                    Location.amenities.op('?')('wifi')
                ).limit(3)
            )
            wifi_locations = result.scalars().all()
            print(f"   Found {len(wifi_locations)} locations with 'wifi' amenity")
            for loc in wifi_locations:
                print(f"   - {loc.name}")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            print("   This is expected if amenities structure is different")

        # Test 7: Filter by 24/7 access
        print("\n7. Filter by 24/7 access:")
        result = await db.execute(
            select(Location).filter(
                Location.active == True,
                Location.is_24_7 == True
            ).limit(3)
        )
        always_open = result.scalars().all()
        print(f"   Found {len(always_open)} 24/7 locations")
        for loc in always_open:
            print(f"   - {loc.name}")

        # Test 8: Filter by booking not required
        print("\n8. Filter by no booking required:")
        result = await db.execute(
            select(Location).filter(
                Location.active == True,
                Location.requires_booking == False
            ).limit(3)
        )
        no_booking = result.scalars().all()
        print(f"   Found {len(no_booking)} locations without booking requirement")
        for loc in no_booking:
            print(f"   - {loc.name}")

        # Test 9: Check price_type distribution
        print("\n9. Price type distribution:")
        result = await db.execute(
            select(Location.price_type, Location.price_min, Location.price_max).filter(
                Location.active == True,
                Location.price_type.isnot(None)
            ).limit(5)
        )
        price_data = result.all()
        print(f"   Found {len(price_data)} locations with price data")
        for price_type, price_min, price_max in price_data:
            print(f"   - Type: {price_type}, Min: {price_min}, Max: {price_max}")

        # Test 10: Check capacity data
        print("\n10. Locations with capacity data:")
        result = await db.execute(
            select(Location.name, Location.capacity_available, Location.capacity_total).filter(
                Location.active == True,
                Location.capacity_available.isnot(None)
            ).limit(3)
        )
        capacity_data = result.all()
        print(f"   Found {len(capacity_data)} locations with capacity data")
        for name, available, total in capacity_data:
            print(f"   - {name}: {available}/{total} spots")

        print("\n" + "=" * 60)
        print("✅ Location filter compatibility test complete!")
        print("=" * 60)

        break  # Exit the async generator


if __name__ == "__main__":
    asyncio.run(test_location_filters())
