# TripFlow Frontend - Flow-Based UI Design Plan

## Overview

A step-by-step wizard interface that guides users through trip planning with personalized recommendations.

## User Flow - Detailed Breakdown

### **Step 1: Welcome & Trip Type**

**Purpose**: Determine user type and trip style

**UI Elements**:
- Hero section with "Plan Your Next Adventure"
- Two main options:
  - 🚐 "Multi Day Trip" (multi-day with overnight stays)
  - 🚗 "Day Trip" (single day exploration)
- Quick stats: "1000+ locations | AI-powered recommendations"

**Data Collected**:
- `is_camper`: boolean
- `trip_type`: "multi_day" | "day_trip"

---

### **Step 2: Start & Travel Duration**

**Purpose**: Define trip starting point and duration preferences with real-time interactive route planning

**Key Interaction**: All changes trigger immediate route recalculation and map updates

**UI Layout** (Split Screen):
- **Left Panel**: Form inputs
  - "Where are you starting?" (address autocomplete)
  - For multi-day: "How many days?" (1-30 days slider/input)
  - For day trip: "How many hours?" (2-12 hours slider)
  - "How far are you willing to travel?" (slider: 0-1000 km)

  - **Planning Mode** (toggle options):
    - 🎯 **Option 1: "Explore based on duration"** (default/recommended)
      - "Let us suggest destinations based on your time and distance"
      - Checkbox: "Round trip (return to start)"
    - 📍 **Option 2: "I have a destination in mind"**
      - "Where do you want to end up?" (address autocomplete)
      - Shows route preview on map

  - **Waypoints** (for multi-day trips only):
    - "Any places you want to visit along the way?" (optional)
    - "+ Add waypoint" button
    - Each waypoint input supports:
      - 🌍 **General locations**: "Germany", "Swiss Alps", "French Riviera"
      - 📍 **Specific spots**: "Legoland Denmark", "Eiffel Tower", "Neuschwanstein Castle"
    - Autocomplete with location type indicator (country/region/city/attraction)
    - Draggable list to reorder waypoints
    - Remove button (×) for each waypoint
    - Example placeholder: "e.g., Belgium, Amsterdam, or Europa-Park"

- **Right Panel**: Live interactive map
  - **Real-time updates** - Map recalculates and redraws instantly on any change:
    - Start/end address typing (debounced)
    - Distance slider adjustment
    - Waypoint add/remove/reorder
    - Planning mode toggle
  - Shows start marker (always visible)
  - For Option 1: Shows radius circle based on max distance (updates as slider moves)
  - For Option 2: Shows start/end markers and estimated route line
  - Waypoint markers (numbered 1, 2, 3...) with connecting route
  - **Draggable markers** - Users can drag waypoints on map to reorder or adjust position
  - Route line with distance segments between points
  - Smooth animations for route changes

**Live Route Stats Panel** (overlays bottom of map or left panel):
```
📏 Total Distance: 450 km (updates in real-time)
⏱️ Estimated Driving: 5.2 hours
📅 Trip Feasibility: ✅ Fits in 3 days | ⚠️ Tight schedule | ❌ Too ambitious
🗺️ Waypoints: 3 stops
```

**Interactive Features**:
- **Auto-optimization**: "Optimize route order" button recalculates best waypoint sequence
- **Feasibility warnings**:
  - "⚠️ This route is 800km - consider adding a day or reducing waypoints"
  - "✅ Comfortable pace - plenty of time for exploration"
- **Smart suggestions**:
  - "💡 Add overnight stop between Amsterdam and Munich? (500km)"
- **Drag-and-drop on map**:
  - Drag waypoint markers to adjust position
  - Drag route line to add intermediate waypoint
- **Real-time validation**:
  - Shows error if addresses can't be geocoded
  - Warns if total distance exceeds selected max distance

**Data Collected**:
- `start_address`: string
- `duration_days`: number (for multi-day trips)
- `duration_hours`: number (for day trips)
- `max_distance_km`: number
- `planning_mode`: "explore" | "destination"
- `is_round_trip`: boolean
- `end_address`: string (optional, only if planning_mode = "destination")
- `waypoints`: array (for multi-day trips, optional)
  - Each waypoint contains:
    - `name`: string (e.g., "Germany" or "Legoland Denmark")
    - `type`: "country" | "region" | "city" | "attraction" | "address"
    - `coordinates`: {lat, lng} (if geocoded)
    - `order`: number (for sequencing)
- `route_stats`: object (calculated in real-time)
  - `total_distance_km`: number
  - `estimated_driving_hours`: number
  - `feasibility_status`: "comfortable" | "tight" | "too_ambitious"

**Technical Implementation Notes for Step 2**:
- **Debouncing**: Address input debounced (300ms) to avoid excessive geocoding API calls
- **Route Calculation**: Use routing API (e.g., OSRM, Google Directions) to calculate actual driving routes
- **State Management**:
  - Local component state for immediate UI updates
  - API calls triggered on state changes to fetch route geometry
- **Loading States**: Show skeleton/spinner on map during route recalculation
- **Error Handling**: Graceful fallback if geocoding or routing fails
- **Performance**:
  - Cache geocoded locations
  - Throttle route recalculations during rapid slider adjustments
  - Use route simplification for initial preview

---

### **Step 3: Interests & Preferences**

**Purpose**: Learn what the user likes

**UI Layout**:
- **Interest Tags** (multi-select chips):
  ```
  🏖️ Beach      🏔️ Mountains    🌲 Nature       🏛️ Culture
  🎨 Art        🍷 Food & Wine  ⚽ Sports       🎪 Events
  🏕️ Camping    🚴 Cycling      🥾 Hiking       📸 Photography
  ```

- **Environment Preferences**:
  ```
  ☀️ Sunny spots    🌊 Coastal      🏔️ Mountains
  🏙️ City life      🌾 Countryside  🌲 Forests
  ```

- **Amenities** (for campers):
  ```
  ⚡ Electricity    💧 Water        🚿 Showers
  📶 WiFi          🚽 Toilets      🍽️ Restaurant
  ```

- **Budget**:
  - Price range slider (€0-100 per night/visit)
  - Toggle: "Show only free locations"

**Additional Options**:
- "Avoid crowded places" checkbox
- Activity level: Low | Moderate | High

**Data Collected**:
- `interests`: string[]
- `preferred_environment`: string[]
- `preferred_amenities`: string[]
- `max_price_per_night`: number
- `avoid_crowded`: boolean
- `activity_level`: string

---

### **Step 4: AI Recommendations**

**Purpose**: Show personalized location suggestions

**UI Layout** (Split Screen):
- **Left Panel**: Scrollable location cards
  - Each card shows:
    - 📸 Location image(s)
    - ⭐ Rating (4.5/5 stars)
    - 📍 Name & location
    - 🏷️ Tags (nature, beach, family-friendly)
    - 💰 Price per night
    - 🚗 Distance from start
    - 📊 Match score (85% match)
    - ℹ️ Brief description
    - ✅ "Add to trip" button
    - 👁️ "View details" button

- **Right Panel**: Interactive map
  - Pins for all recommended locations
  - Color-coded by match score (green = high, yellow = medium)
  - Cluster markers when zoomed out
  - Click pin to see location details
  - Shows route if locations are added

**Features**:
- Real-time filtering:
  - Location type (campsite, parking, attraction, etc.)
  - Price range
  - Rating minimum
  - Distance from route
- Sort by:
  - Match score
  - Rating
  - Price
  - Distance

**Smart Suggestions**:
- "Based on your interests, we found X locations along your route"
- "Travelers like you also enjoyed..."
- Alternative suggestions if not enough matches

**Data Actions**:
- Add locations to trip waypoints
- Save locations to favorites

---

### **Step 5: Customize Route**

**Purpose**: Fine-tune the trip itinerary

**UI Layout** (Split Screen):
- **Left Panel**: Draggable waypoint list
  ```
  📍 Start: Amsterdam
     ↓ 120 km, 1.5 hours
  1. 🏕️ Campsite "De Zeebries"
     Beach | ⭐4.5 | €25/night
     [Remove] [View details] [Move ↑↓]
     ↓ 85 km, 1 hour
  2. 🏛️ Museum District
     Culture | ⭐4.8 | Free
     [Remove] [View details] [Move ↑↓]
     ↓ 95 km, 1.2 hours
  📍 End: Brussels
  ```

- **Right Panel**: Interactive map
  - Full route visualization
  - Draggable waypoint markers
  - Route line with distance labels
  - Shows corridor width (locations within X km of route)

**Features**:
- Drag-and-drop to reorder waypoints
- "Add more stops" button → shows recommendations near route
- Each waypoint shows:
  - Estimated arrival time (if start date set)
  - Suggested stay duration
  - Nearby attractions/events
- "Optimize route" button (auto-reorder for shortest distance)

**Trip Stats Panel** (bottom):
```
📏 Total Distance: 300 km
⏱️ Driving Time: 3.7 hours
📅 Trip Duration: 4 days
💰 Estimated Cost: €75 (accommodations)
```

---

### **Step 6: Review & Finalize**

**Purpose**: Confirm details and save trip

**UI Layout**:
- **Trip Summary Card**:
  - Trip name (editable)
  - Date range picker
  - Overview map thumbnail
  - Key stats

- **Detailed Itinerary** (Timeline view):
  ```
  Day 1 - June 15, 2024
  ├─ 09:00  Depart Amsterdam
  ├─ 11:00  Arrive at Campsite De Zeebries
  │         Stay: 1 night | €25
  │         Activities: Beach walk, seafood dinner
  └─ Nearby: 3 restaurants, 2 attractions

  Day 2 - June 16, 2024
  ├─ 10:00  Check out & depart
  ├─ 12:00  Visit Museum District
  │         Duration: 3 hours | Free
  └─ 15:00  Continue to Brussels
  ```

- **Actions**:
  - 💾 "Save Trip" button
  - 📧 "Email Itinerary"
  - 📱 "Export to Calendar"
  - 🔗 "Share Trip" (generate link)
  - 📄 "Download PDF"

**Optional**:
- Weather forecast for trip dates
- Packing checklist based on destinations
- Event calendar for dates/locations

---

## Component Architecture

### Page Components
```
App.jsx
├─ HomePage.jsx                    // Marketing/landing
├─ TripFlowWizard.jsx             // Main flow container
│  ├─ ProgressBar.jsx             // Shows current step
│  ├─ Step1_TripType.jsx
│  ├─ Step2_Destination.jsx
│  ├─ Step3_Preferences.jsx
│  ├─ Step4_Recommendations.jsx
│  ├─ Step5_CustomizeRoute.jsx
│  └─ Step6_ReviewFinalize.jsx
├─ MyTrips.jsx                     // Saved trips list
└─ TripDetail.jsx                  // View/edit existing trip
```

### Shared Components
```
components/
├─ LocationCard.jsx                // Location display card
├─ LocationDetail.jsx              // Full location info modal
├─ MapView.jsx                     // Leaflet map wrapper
├─ RouteMap.jsx                    // Map with route visualization
├─ InterestPicker.jsx             // Multi-select interest tags
├─ WaypointList.jsx               // Draggable waypoint list
├─ TripStats.jsx                  // Trip statistics display
├─ FilterPanel.jsx                // Location filters
└─ LoadingSpinner.jsx             // Loading states
```

### Services
```
services/
├─ api.js                         // Axios API client
├─ tripService.js                 // Trip CRUD operations
├─ locationService.js             // Location search/recommendations
└─ geocodingService.js            // Address autocomplete
```

### State Management
```
context/
├─ TripContext.jsx                // Current trip being planned
└─ UserContext.jsx                // User preferences & auth
```

---

## Key UI/UX Considerations

### Visual Design
- **Color Scheme**:
  - Primary: Green (#10B981) - represents nature/travel
  - Secondary: Blue (#3B82F6) - represents water/sky
  - Accent: Orange (#F59E0B) - for CTAs
  - Neutral: Grays for text/backgrounds

- **Typography**:
  - Headers: Bold, modern sans-serif (Inter, Poppins)
  - Body: Readable sans-serif (system fonts)

- **Layout**:
  - Split-screen for steps with map
  - Mobile-first responsive design
  - Smooth transitions between steps

### Interactions
- **Progress Indicator**: Always visible at top
- **Navigation**:
  - "Back" and "Next" buttons at bottom
  - Allow jumping to previous steps
  - Auto-save progress
- **Feedback**:
  - Loading states for API calls
  - Success/error toasts
  - Validation messages inline

### Accessibility
- Keyboard navigation
- ARIA labels
- Screen reader friendly
- High contrast mode support

### Performance
- Lazy load location images
- Debounce search inputs
- Cache API responses
- Virtual scrolling for long lists

---

## Mobile Considerations

### Responsive Breakpoints
- Mobile: < 768px (stack vertically, full-width map)
- Tablet: 768px - 1024px (compact split-screen)
- Desktop: > 1024px (full split-screen)

### Mobile-Specific UX
- Bottom sheet for location details (instead of modal)
- Swipeable cards for recommendations
- Simplified map controls
- Touch-friendly drag-and-drop

---

## Technical Implementation Notes

### Libraries/Dependencies
- **React Router**: Page navigation
- **React Leaflet**: Map integration
- **React DnD**: Drag-and-drop waypoints
- **React Hook Form**: Form validation
- **Axios**: API calls
- **Date-fns**: Date formatting
- **Framer Motion**: Smooth animations (optional)

### API Integration Points
1. Step 2: Geocoding API for address autocomplete
2. Step 3: Save user preferences
3. Step 4: GET /recommendations/ endpoint
4. Step 4: GET /trips/{id}/suggest-waypoints
5. Step 5: POST /trips/{id}/waypoints (add/remove)
6. Step 6: POST /trips/{id}/finalize

### Data Flow
```
User Input → React State → API Call → Update State → Re-render UI
                ↓
         localStorage (persist progress)
```

---

## Future Enhancements

### Phase 2
- Real-time weather integration
- Event calendar overlay on map
- Social features (share/like trips)
- Trip collaboration (invite friends)

### Phase 3
- Offline mode (PWA)
- Mobile apps (React Native)
- Voice navigation
- AR location preview

---

## Open Questions for Discussion

1. **Step Order**: Should preferences come before or after seeing initial recommendations?
2. **Map Position**: Left or right panel? Always visible or optional?
3. **Recommendation Algorithm**: Show all matches or pre-filter to top N based on route?
4. **Event Integration**: Where to show events? Separate step or integrated into recommendations?
5. **User Accounts**: Required from start or optional (guest mode)?
6. **Pricing Display**: Always show prices or only for campers?

---

## Implementation Priority

### MVP (Minimum Viable Product)
- Steps 1-4 (basic flow up to recommendations)
- Simple map view (no advanced features)
- Basic location cards
- Core API integration

### Phase 1.5
- Steps 5-6 (route customization & finalization)
- Drag-and-drop waypoints
- Trip stats
- Save/load trips

### Phase 2
- Enhanced filtering
- Events integration
- Social features
- Mobile optimization
