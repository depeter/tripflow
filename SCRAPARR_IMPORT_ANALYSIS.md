# Scraparr to Tripflow Import Analysis

**Generated:** 2025-12-29
**Purpose:** Identify data in Scraparr that can be imported into Tripflow

---

## Current State

### Tripflow Database (tripflow-postgres:5433)

**Locations:** 311,403 total

| Source | Type | Count | Notes |
|--------|------|-------|-------|
| park4night | PARKING | 223,131 | Camping/parking spots across Europe |
| uitinvlaanderen | EVENT | 55,078 | Cultural events (also in events table) |
| visitwallonia | POI | 12,254 | Tourism POIs in Wallonia |
| visitwallonia | ATTRACTION | 8,553 | Tourist attractions |
| visitwallonia | HOTEL | 6,378 | Hotels/accommodations |
| visitwallonia | RESTAURANT | 3,253 | Restaurants |
| other | EVENT | 2,718 | Manual/other sources |
| campercontact | CAMPSITE | 19 | Very limited data |
| other | CAMPSITE | 19 | Manual/other sources |

**Events:** 41,725 total

| Source | Count | Notes |
|--------|-------|-------|
| uitinvlaanderen | 20,610 | UiT in Vlaanderen events |
| other | 11,516 | Manual/other sources |
| ticketmaster | 9,099 | Ticketmaster events |
| eventbrite | 500 | Eventbrite events |

---

### Scraparr Database (scraparr-postgres:5434)

#### POI/Location Data

| Scraper ID | Name | Schema | Table | Count | Type |
|------------|------|--------|-------|-------|------|
| 1 | Park4Night Grid Scraper | scraper_1 | places | 223,577 | Camping/parking |
| 5 | CamperContact Grid Scraper | scraper_5 | places | 24,726 | Camping/motorhome |
| 6 | Visit Wallonia (PIVOT) | scraper_6 | pois | 15,219 | Tourism POIs |
| 7 | DagjeWeg.NL | scraper_7 | attractions | 3,416 | Day trip attractions |
| 11 | OpenStreetMap POIs | scraper_11 | pois | **0** | Not scraped yet |
| 12 | Wikidata Tourist Attractions | scraper_12 | pois | **8,340** | Museums, monuments, castles |

#### Event Data

| Scraper ID | Name | Schema | Table | Count | Type |
|------------|------|--------|-------|-------|------|
| 2 | UiTinVlaanderen Events | scraper_2 | events | 41,932 | Cultural events |
| 3 | Eventbrite Events Scraper | scraper_3 | events | 2,067 | Events |
| 4 | Ticketmaster Events | scraper_4 | events | 16,745 | Events |

---

## Import Opportunities

### 🎯 HIGH PRIORITY - New POI Data

#### 1. **Wikidata Tourist Attractions (8,340 POIs)**
- **Schema:** `scraper_12.pois`
- **Why:** Brand new high-quality structured data about museums, monuments, castles, heritage sites
- **Fields available:**
  - Basic: name, name_en, description, description_en, poi_type
  - Location: latitude, longitude, country, country_code, city, address
  - Rich data: heritage_status, architect, architectural_style, inception (year built)
  - Links: official_website, wikipedia_en, wikipedia_local, image_url
  - Visitors: visitors_per_year (when available)
  - Contact: opening_hours, phone, email
- **Mapping to Tripflow:**
  - `source`: 'wikidata'
  - `external_id`: wikidata_id (e.g., "Q2677140")
  - `location_type`: Map poi_type → 'ATTRACTION' or 'POI'
  - `name`: Use name_en if available, fallback to name
  - `description`: Use description_en if available, fallback to description
  - `images`: Parse image_url into images array
  - `tags`: Extract from heritage_status, architectural_style, poi_type
  - `website`: official_website
  - Store heritage_status, architect, inception in `raw_data` or `features`

#### 2. **DagjeWeg.NL Attractions (3,416 POIs)**
- **Schema:** `scraper_7.attractions`
- **Why:** Dutch day trip destinations not currently in Tripflow
- **Action:** Need to check schema structure first
- **Mapping:** TBD after reviewing structure

#### 3. **CamperContact Places (24,726 → only 19 in Tripflow!)**
- **Schema:** `scraper_5.places`
- **Why:** We only have 19 CamperContact places but Scraparr has 24,726!
- **Status:** MAJOR DATA GAP - Need to import ~24,700 camping places
- **Fields available:**
  - Detailed info: name, description, rating, price_per_night
  - Location: latitude, longitude, street, city, postal_code, country
  - Amenities: amenities (JSON), usps (unique selling points)
  - Booking: is_bookable, subscription_level
  - Contact: phone, email, website
  - Photos: photos (JSONB array)
- **Mapping to Tripflow:**
  - `source`: 'campercontact'
  - `external_id`: poi_id
  - `location_type`: Map type → 'CAMPSITE', 'PARKING', etc.
  - `amenities`: Parse amenities JSON
  - `features`: Parse usps (unique selling points)
  - `price_type`: 'paid' if price_per_night exists
  - `price_min`/`price_max`: price_per_night
  - `images`: Parse photos JSONB

### 🎯 MEDIUM PRIORITY - Additional Event Data

#### 4. **UiTinVlaanderen Events (41,932 → 20,610 in Tripflow)**
- **Schema:** `scraper_2.events`
- **Gap:** ~21,000 missing events
- **Action:** Import events not already in Tripflow (check by external_id/event_id)

#### 5. **Ticketmaster Events (16,745 → 9,099 in Tripflow)**
- **Schema:** `scraper_4.events`
- **Gap:** ~7,600 missing events
- **Action:** Import missing events

#### 6. **Eventbrite Events (2,067 → 500 in Tripflow)**
- **Schema:** `scraper_3.events`
- **Gap:** ~1,500 missing events
- **Action:** Import missing events

### 🎯 LOW PRIORITY - Verify Existing Data

#### 7. **Park4Night Places (223,577 vs 223,131)**
- **Schema:** `scraper_1.places`
- **Gap:** ~450 places (minor difference, might be duplicates or filtered)
- **Action:** Spot check for missing data, low priority

#### 8. **Visit Wallonia (15,219 vs 30,438 in Tripflow)**
- **Schema:** `scraper_6.pois`
- **Note:** Tripflow has MORE data than Scraparr (30,438 vs 15,219)
- **Action:** No import needed, Tripflow is ahead

---

## Import Priority Order

### Phase 1: High-Value POI Data (Immediate)
1. ✅ **Wikidata Tourist Attractions** (8,340 POIs) - NEW high-quality data
2. ✅ **CamperContact Places** (24,707 missing) - CRITICAL data gap
3. ✅ **DagjeWeg.NL Attractions** (3,416 POIs) - NEW Dutch attractions

### Phase 2: Event Data Gap Closure (Next)
4. **UiTinVlaanderen Events** (~21,000 missing)
5. **Ticketmaster Events** (~7,600 missing)
6. **Eventbrite Events** (~1,500 missing)

### Phase 3: Data Validation (Later)
7. **Park4Night** - Verify ~450 missing places
8. **OpenStreetMap** - Currently empty, low priority (Wikidata has better data)

---

## Technical Implementation Notes

### Import Strategy

1. **Deduplication:** Use `(external_id, source)` unique constraint to prevent duplicates
2. **Data mapping:** Create mapping functions for each source schema → Tripflow schema
3. **Batch processing:** Import in batches of 1000-5000 records
4. **Logging:** Track import progress, errors, and statistics
5. **Validation:** Verify coordinates, required fields, data quality

### Database Connection Info

**Tripflow:**
- Host: localhost (via docker)
- Port: 5433
- Database: tripflow
- User: postgres
- Schema: tripflow

**Scraparr:**
- Host: localhost (via docker)
- Port: 5434
- Database: scraparr
- User: scraparr
- Schemas: scraper_1, scraper_2, ..., scraper_12

### Import Script Template

```python
# Example structure for import script
import psycopg2
from datetime import datetime

# Connect to both databases
scraparr_conn = psycopg2.connect(
    host="localhost", port=5434, database="scraparr",
    user="scraparr", password="scraparr"
)
tripflow_conn = psycopg2.connect(
    host="localhost", port=5433, database="tripflow",
    user="postgres", password="tripflow"
)

# Fetch data from Scraparr
scraparr_cur = scraparr_conn.cursor()
scraparr_cur.execute("SELECT * FROM scraper_12.pois")

# Map and insert into Tripflow
tripflow_cur = tripflow_conn.cursor()
for row in scraparr_cur:
    mapped_data = map_wikidata_to_tripflow(row)
    insert_location(tripflow_cur, mapped_data)

tripflow_conn.commit()
```

---

## Next Steps

1. ✅ Review this analysis
2. Create import script for Wikidata POIs (highest value, clean data)
3. Create import script for CamperContact (biggest data gap)
4. Create import script for DagjeWeg.NL
5. Create import script for missing events
6. Schedule imports and monitor results
7. Set up ongoing sync mechanism

---

## Questions to Consider

1. **Location Types:** Should we create new location types for specific POI categories (MUSEUM, MONUMENT, CASTLE)?
2. **Language:** How to handle multi-language data (name_en vs name)?
3. **Images:** Should we download/host images or link to external sources?
4. **Updates:** How often should we re-sync data from Scraparr?
5. **Deactivation:** Should we mark locations as inactive if they disappear from Scraparr?
