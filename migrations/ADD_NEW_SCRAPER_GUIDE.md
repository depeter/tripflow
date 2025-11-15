# Adding New Scrapers to Tripflow Migration

## Quick Guide

When you add a new scraper to Scraparr, follow these steps to include it in the Tripflow migration:

## 1. Identify the Scraper Details

Check the scraparr database to get scraper info:
```sql
SELECT id, name, schema_name, module_path, class_name
FROM scrapers
WHERE name LIKE '%YourNewScraper%';
```

## 2. Add Mapping Class

Edit `scraper_mappings.py` and add a new mapping class:

```python
class YourNewScraperMapping(ScraperMapping):
    def __init__(self):
        super().__init__()
        self.scraper_id = 4  # The ID from scrapers table
        self.scraper_name = "Your New Scraper Name"
        self.schema_name = "scraper_4"  # The schema where data is stored
        self.data_type = DataType.EVENT  # or LOCATION or COMBINED
        self.source_name = "other"  # or add new enum value to tripflow

    def get_query(self) -> str:
        """Return SQL to fetch data from your scraper's tables"""
        return f"""
            SELECT * FROM {self.schema_name}.your_table
            ORDER BY id
        """

    def map_to_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map your data to tripflow.locations format"""
        return {
            "external_id": f"yoursource_{row['id']}",
            "source": "other",  # or your source name
            "name": row.get('venue_name'),
            "location_type": "EVENT",  # or appropriate type
            "latitude": float(row['lat']),
            "longitude": float(row['lng']),
            # ... map all fields
        }

    def map_to_event(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map your data to tripflow.events format"""
        return {
            "external_id": row['event_id'],
            "source": "other",
            "name": row['title'],
            "start_date": row['start_time'],
            # ... map all fields
        }
```

## 3. Register the Mapping

At the bottom of `scraper_mappings.py`, add to the registry:

```python
# Add to SCRAPER_REGISTRY
SCRAPER_REGISTRY = {
    1: Park4NightMapping(),
    2: UiTinVlaanderenMapping(),
    3: EventbriteMapping(),
    4: YourNewScraperMapping(),  # <-- Add this
}

# Add to SCHEMA_REGISTRY
SCHEMA_REGISTRY = {
    'scraper_1': Park4NightMapping(),
    'scraper_2': UiTinVlaanderenMapping(),
    'scraper_3': EventbriteMapping(),
    'scraper_4': YourNewScraperMapping(),  # <-- Add this
}
```

## 4. (Optional) Update Tripflow Enum

If your scraper needs a new source type, update the tripflow database:

```sql
-- Add new value to location_source enum
ALTER TYPE tripflow.location_source ADD VALUE 'yoursource';
```

## 5. Test the Migration

```bash
# Test with just your scraper (limit 10 records)
python migrate_all_scrapers.py --scraper-id 4 --limit 10

# Check the results
docker exec tripflow-postgres psql -U tripflow -d tripflow -c "
SELECT * FROM tripflow.locations
WHERE source = 'yoursource'
LIMIT 5;
"
```

## 6. Run Full Migration

```bash
# Migrate just your new scraper
python migrate_all_scrapers.py --scraper-id 4

# Or migrate all new scrapers
python migrate_all_scrapers.py --new-only
```

## Data Type Guide

### DataType.LOCATION
Use for camping spots, parking areas, POIs, restaurants, hotels, etc.
- Creates records in `tripflow.locations` only
- Example: Park4Night camping spots

### DataType.EVENT
Use for standalone events (rare - usually events need a venue/location)
- Creates records in `tripflow.events` only
- Requires a location_id (must exist or be created separately)

### DataType.COMBINED
Use for events with venues (most common for event scrapers)
- Creates records in both `tripflow.locations` and `tripflow.events`
- Location is created first, then event is linked to it
- Example: UiT events, Eventbrite events

## Field Mapping Reference

### tripflow.locations required fields:
- `external_id`: Unique ID from your source
- `source`: From location_source enum
- `name`: Location/venue name
- `location_type`: From location_type enum
- `latitude`, `longitude`: Coordinates

### tripflow.events required fields:
- `external_id`: Unique event ID from your source
- `source`: From location_source enum
- `name`: Event name
- `start_date`: Event start datetime
- `location_id`: Link to tripflow.locations

## Examples

### Mapping a Festival Scraper
```python
class FestivalScraperMapping(ScraperMapping):
    def __init__(self):
        super().__init__()
        self.scraper_id = 5
        self.scraper_name = "European Festivals"
        self.schema_name = "scraper_5"
        self.data_type = DataType.COMBINED  # Both venue and event
        self.source_name = "other"
```

### Mapping a Hotel Scraper
```python
class HotelScraperMapping(ScraperMapping):
    def __init__(self):
        super().__init__()
        self.scraper_id = 6
        self.scraper_name = "Budget Hotels"
        self.schema_name = "scraper_6"
        self.data_type = DataType.LOCATION  # Just locations
        self.source_name = "other"
```

## Troubleshooting

### "No mapping found for scraper"
- Make sure you added the mapping class
- Check the scraper_id matches the database
- Verify you added it to both registries

### "invalid input value for enum"
- The source name isn't in tripflow.location_source enum
- Either use 'other' or add your source to the enum

### Data not appearing
- Check for errors in migration log
- Verify coordinates are valid floats
- Ensure required fields are not null

## Deployment to Scraparr Server

```bash
# Copy files to scraparr server
scp scraper_mappings.py peter@scraparr:/home/peter/tripflow/migrations/
scp migrate_all_scrapers.py peter@scraparr:/home/peter/tripflow/migrations/

# SSH to server and run migration
ssh peter@scraparr
cd /home/peter/tripflow/migrations
python3 migrate_all_scrapers.py --scraper-id YOUR_ID
```