import React, { useState, useEffect, useCallback } from 'react';
import { useTripContext } from '../context/TripContext';
import LocationCard from '../components/LocationCard';
import EventCard from '../components/EventCard';
import MapView from '../components/MapView';
import LoadingSpinner from '../components/LoadingSpinner';
import { getRecommendations, getNearbyLocations, discoverEvents } from '../services/tripsService';
import { geocodeAddress, reverseGeocode, debounce } from '../services/geocodingService';
import './Step4_Recommendations.css';

const Step4_Recommendations = ({ onNext, onBack }) => {
  const { tripData, updateTripData } = useTripContext();

  // Tab system: 'locations' or 'events'
  const [activeTab, setActiveTab] = useState('locations');

  // Locations data
  const [recommendations, setRecommendations] = useState([]);
  const [park4nightLocations, setPark4nightLocations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingPark4Night, setIsLoadingPark4Night] = useState(true);

  // Events data
  const [events, setEvents] = useState([]);
  const [isLoadingEvents, setIsLoadingEvents] = useState(true);

  // Advanced filters
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [locationFilters, setLocationFilters] = useState({
    types: [],
    amenities: [],
    priceRange: 'all', // 'free', 'low', 'medium', 'high', 'all'
    minRating: 0
  });
  const [eventFilters, setEventFilters] = useState({
    categories: [],
    freeOnly: false,
    dateRange: 'upcoming' // 'upcoming', 'this_week', 'this_month', 'custom'
  });

  // Legacy filters (for backwards compatibility)
  const [filters, setFilters] = useState({
    type: '',
    minRating: 0
  });
  const [sortBy, setSortBy] = useState('match');

  const [selectedLocations, setSelectedLocations] = useState(
    tripData.selected_waypoints || []
  );

  // Location search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [customLocations, setCustomLocations] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);

  useEffect(() => {
    if (activeTab === 'locations') {
      loadRecommendations();
      loadPark4NightLocations();
    } else if (activeTab === 'events') {
      loadEvents();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, sortBy, activeTab, locationFilters, eventFilters]);

  const loadRecommendations = async () => {
    setIsLoading(true);
    try {
      // Format parameters for the backend API
      const params = {
        max_distance_km: tripData.max_distance_km || 500,
        interests: tripData.interests || [],
        preferred_environment: tripData.preferred_environment || [],
        preferred_amenities: tripData.preferred_amenities || [],
        budget_per_day: tripData.budget_per_day || 50,
        activity_level: tripData.activity_level || 'moderate',
        start_coordinates: tripData.start_coordinates,
        limit: 20
      };

      const results = await getRecommendations(params);
      setRecommendations(results);
    } catch (error) {
      console.error('Error loading recommendations:', error);
      // On error, show empty results
      setRecommendations([]);
    }
    setIsLoading(false);
  };

  const loadPark4NightLocations = async () => {
    if (!tripData.start_coordinates) {
      setIsLoadingPark4Night(false);
      return;
    }

    setIsLoadingPark4Night(true);
    try {
      // Fetch park4night locations near the start point
      const params = {
        latitude: tripData.start_coordinates.lat,
        longitude: tripData.start_coordinates.lng,
        radius_km: tripData.max_distance_km || 100,
        location_types: filters.type ? [filters.type] : [],
        limit: 100
      };

      const results = await getNearbyLocations(params);

      // Transform backend location format to frontend format
      const transformedResults = results.map(loc => ({
        id: loc.id,
        name: loc.name,
        type: loc.location_type,
        location_type: loc.location_type,
        coordinates: {
          lat: loc.latitude,
          lng: loc.longitude
        },
        rating: loc.rating || 0,
        match_score: 80, // Default match score for park4night
        description: loc.description || '',
        tags: loc.tags || [],
        price_per_night: loc.price || 0,
        amenities: loc.amenities || [],
        source: loc.source || 'park4night',
        distance_km: loc.distance_km || 0
      }));

      setPark4nightLocations(transformedResults);
    } catch (error) {
      console.error('Error loading park4night locations:', error);
      setPark4nightLocations([]);
    }
    setIsLoadingPark4Night(false);
  };

  const loadEvents = async () => {
    if (!tripData.start_coordinates) {
      setIsLoadingEvents(false);
      return;
    }

    setIsLoadingEvents(true);
    try {
      // Fetch events near the start point
      const params = {
        latitude: tripData.start_coordinates.lat,
        longitude: tripData.start_coordinates.lng,
        radius_km: tripData.max_distance_km || 50,
        categories: eventFilters.categories.length > 0 ? eventFilters.categories : null,
        free_only: eventFilters.freeOnly,
        limit: 100
      };

      // Add date range filtering
      if (eventFilters.dateRange !== 'upcoming') {
        const now = new Date();
        if (eventFilters.dateRange === 'this_week') {
          params.end_date = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
        } else if (eventFilters.dateRange === 'this_month') {
          params.end_date = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        }
      }

      const response = await discoverEvents(params);

      // Transform events to include required fields for cards
      const transformedEvents = response.events.map(evt => ({
        ...evt,
        id: evt.id,
        coordinates: {
          lat: evt.latitude,
          lng: evt.longitude
        },
        type: 'event',
        match_score: 85 // Default match score for events
      }));

      setEvents(transformedEvents);
    } catch (error) {
      console.error('Error loading events:', error);
      setEvents([]);
    }
    setIsLoadingEvents(false);
  };

  // Search for locations
  const handleSearch = useCallback(
    debounce(async (query) => {
      if (!query || query.length < 2) {
        setSearchResults([]);
        setShowSearchResults(false);
        return;
      }

      setIsSearching(true);
      setShowSearchResults(true);

      try {
        const results = await geocodeAddress(query);
        setSearchResults(results.slice(0, 5)); // Show top 5 results
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      }

      setIsSearching(false);
    }, 300),
    []
  );

  const handleSearchInputChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    handleSearch(value);
  };

  const handleSelectSearchResult = (result) => {
    const customLocation = {
      id: `custom-${Date.now()}`,
      name: result.name,
      type: 'custom',
      coordinates: {
        lat: result.coordinates.lat,
        lng: result.coordinates.lng
      },
      rating: 0,
      match_score: 100,
      description: 'Custom location',
      tags: ['custom'],
      price_per_night: 0
    };

    setCustomLocations([...customLocations, customLocation]);
    setSearchQuery('');
    setSearchResults([]);
    setShowSearchResults(false);

    // Auto-add to trip
    handleAddToTrip(customLocation);
  };

  // Handle map click to add custom location
  const handleMapClick = async (coordinates) => {
    try {
      const result = await reverseGeocode(coordinates.lat, coordinates.lng);

      const customLocation = {
        id: `custom-${Date.now()}`,
        name: result.name || 'Custom Location',
        type: 'custom',
        coordinates: {
          lat: coordinates.lat,
          lng: coordinates.lng
        },
        rating: 0,
        match_score: 100,
        description: 'Added from map',
        tags: ['custom'],
        price_per_night: 0
      };

      setCustomLocations([...customLocations, customLocation]);

      // Auto-add to trip
      handleAddToTrip(customLocation);
    } catch (error) {
      console.error('Error reverse geocoding:', error);
    }
  };

  const handleAddToTrip = (location) => {
    const isAlreadySelected = selectedLocations.some(loc => loc.id === location.id);

    let newSelected;
    if (isAlreadySelected) {
      newSelected = selectedLocations.filter(loc => loc.id !== location.id);
    } else {
      newSelected = [...selectedLocations, location];
    }

    setSelectedLocations(newSelected);
    updateTripData({ selected_waypoints: newSelected });
  };

  const isLocationSelected = (locationId) => {
    return selectedLocations.some(loc => loc.id === locationId);
  };

  const handleContinue = () => {
    onNext();
  };

  // Build map markers
  const buildMapMarkers = () => {
    const markers = [];

    // Start marker
    if (tripData.start_coordinates) {
      markers.push({
        id: 'start',
        position: [tripData.start_coordinates.lat, tripData.start_coordinates.lng],
        popup: `Start: ${tripData.start_address}`
      });
    }

    // Combine recommendations, park4night locations, custom locations, and events
    const allLocations = [...recommendations, ...park4nightLocations, ...customLocations];
    const allItems = activeTab === 'locations' ? allLocations : [...allLocations, ...events];

    // Location and event markers with type-specific icons
    allItems.forEach((item, idx) => {
      const isSelected = isLocationSelected(item.id);
      const locationType = item.location_type || item.type;

      // Create popup content with more details
      let popupContent = item.name;

      if (item.type === 'event') {
        // Event popup
        popupContent += ` (${item.category})`;
        if (item.start_datetime) {
          const date = new Date(item.start_datetime);
          popupContent += `<br/>📅 ${date.toLocaleDateString()}`;
        }
        if (item.free) {
          popupContent += `<br/>💰 FREE`;
        } else if (item.price) {
          popupContent += `<br/>💰 ${item.currency}${item.price}`;
        }
      } else {
        // Location popup
        if (item.source === 'park4night') {
          popupContent += ' (Park4Night)';
        } else if (item.type === 'custom') {
          popupContent += ' (Custom)';
        } else if (item.match_score) {
          popupContent += ` - ${item.match_score}% match`;
        }
        if (item.rating) {
          popupContent += `<br/>⭐ ${item.rating.toFixed(1)}`;
        }
      }

      if (item.distance_km) {
        popupContent += `<br/>📍 ${item.distance_km.toFixed(1)} km away`;
      }

      markers.push({
        id: `loc-${item.id}`,
        position: [item.coordinates.lat, item.coordinates.lng],
        popup: popupContent,
        locationType: item.type === 'event' ? 'event_venue' : (locationType === 'custom' ? 'custom' : locationType),
        isSelected: isSelected,
        selectionNumber: isSelected ? selectedLocations.findIndex(l => l.id === item.id) + 1 : undefined,
        draggable: false
      });
    });

    return markers;
  };

  const markers = buildMapMarkers();
  const mapCenter = tripData.start_coordinates
    ? [tripData.start_coordinates.lat, tripData.start_coordinates.lng]
    : [50.8503, 4.3517]; // Default to Brussels

  return (
    <div className="step4-container">
      <div className="split-screen">
        {/* Left Panel - Recommendations List */}
        <div className="left-panel">
          <div className="panel-header">
            <div>
              <h2>Discover</h2>
              <p className="recommendations-subtitle">
                Find {activeTab === 'locations' ? 'campsites, parking, and attractions' : 'events and activities'} near your route
              </p>
            </div>
          </div>

          {/* Discovery Tabs */}
          <div className="discovery-tabs">
            <button
              className={`discovery-tab ${activeTab === 'locations' ? 'active' : ''}`}
              onClick={() => setActiveTab('locations')}
            >
              <span className="tab-icon">📍</span>
              Locations
              <span className="tab-count">{recommendations.length + park4nightLocations.length + customLocations.length}</span>
            </button>
            <button
              className={`discovery-tab ${activeTab === 'events' ? 'active' : ''}`}
              onClick={() => setActiveTab('events')}
            >
              <span className="tab-icon">🎉</span>
              Events
              <span className="tab-count">{events.length}</span>
            </button>
          </div>

          {/* Location Search */}
          <div className="search-bar">
            <div className="search-input-wrapper">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                className="search-input"
                placeholder="Search for a city, address, or landmark..."
                value={searchQuery}
                onChange={handleSearchInputChange}
                onFocus={() => searchResults.length > 0 && setShowSearchResults(true)}
              />
              {isSearching && <span className="search-loading">⏳</span>}
            </div>

            {/* Search Results Dropdown */}
            {showSearchResults && searchResults.length > 0 && (
              <div className="search-results-dropdown">
                {searchResults.map((result, idx) => (
                  <div
                    key={idx}
                    className="search-result-item"
                    onClick={() => handleSelectSearchResult(result)}
                  >
                    <span className="result-icon">📍</span>
                    <div className="result-info">
                      <div className="result-name">{result.name}</div>
                      {result.type && (
                        <div className="result-type">{result.type}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {showSearchResults && !isSearching && searchResults.length === 0 && searchQuery.length >= 2 && (
              <div className="search-results-dropdown">
                <div className="search-result-item no-results">
                  <span>No results found for "{searchQuery}"</span>
                </div>
              </div>
            )}
          </div>

          <div className="map-hint">
            <span className="hint-icon">💡</span>
            <span>Tip: Click anywhere on the map to add a custom location</span>
          </div>

          {/* Filters & Sort */}
          <div className="filters-bar">
            <div className="filter-group">
              <label>Type</label>
              <select
                value={filters.type}
                onChange={(e) => setFilters({ ...filters, type: e.target.value })}
              >
                <option value="">All types</option>
                <option value="campsite">Campsite</option>
                <option value="attraction">Attraction</option>
                <option value="nature">Nature</option>
                <option value="city">City</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Min. Rating</label>
              <select
                value={filters.minRating}
                onChange={(e) => setFilters({ ...filters, minRating: parseFloat(e.target.value) })}
              >
                <option value="0">Any rating</option>
                <option value="4.0">4.0+</option>
                <option value="4.5">4.5+</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Sort by</label>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                <option value="match">Best match</option>
                <option value="rating">Highest rated</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
                <option value="distance">Distance</option>
              </select>
            </div>
          </div>

          {/* Recommendations List */}
          <div className="recommendations-list">
            {(activeTab === 'locations' && (isLoading || isLoadingPark4Night)) || (activeTab === 'events' && isLoadingEvents) ? (
              <div className="loading-container">
                <LoadingSpinner message={activeTab === 'locations' ? "Finding perfect locations for you..." : "Discovering events near you..."} />
              </div>
            ) : (
              <>
                {/* Custom Locations */}
                {customLocations.length > 0 && (
                  <>
                    <div className="section-divider">
                      <span className="divider-text">Your Custom Locations ({customLocations.length})</span>
                    </div>
                    {customLocations.map(location => (
                      <LocationCard
                        key={location.id}
                        location={location}
                        onAddToTrip={handleAddToTrip}
                        isSelected={isLocationSelected(location.id)}
                      />
                    ))}
                  </>
                )}

                {/* Park4Night Locations */}
                {park4nightLocations.length > 0 && (
                  <>
                    <div className="section-divider">
                      <span className="divider-text">Park4Night Locations ({park4nightLocations.length})</span>
                    </div>
                    {park4nightLocations.slice(0, 20).map(location => (
                      <LocationCard
                        key={location.id}
                        location={location}
                        onAddToTrip={handleAddToTrip}
                        isSelected={isLocationSelected(location.id)}
                      />
                    ))}
                  </>
                )}

                {/* Recommendations */}
                {recommendations.length > 0 && (
                  <>
                    <div className="section-divider">
                      <span className="divider-text">Recommended Locations ({recommendations.length})</span>
                    </div>
                    {recommendations.map(location => (
                      <LocationCard
                        key={location.id}
                        location={location}
                        onAddToTrip={handleAddToTrip}
                        isSelected={isLocationSelected(location.id)}
                      />
                    ))}
                  </>
                )}

                {/* Events */}
                {activeTab === 'events' && events.length > 0 && (
                  <>
                    <div className="section-divider">
                      <span className="divider-text">Events Near You ({events.length})</span>
                    </div>
                    {events.slice(0, 30).map(event => (
                      <EventCard
                        key={event.id}
                        event={event}
                        onAddToTrip={handleAddToTrip}
                        isSelected={isLocationSelected(event.id)}
                      />
                    ))}
                  </>
                )}

                {/* No Results */}
                {activeTab === 'locations' && recommendations.length === 0 && park4nightLocations.length === 0 && customLocations.length === 0 && (
                  <div className="no-results">
                    <span className="no-results-icon">🔍</span>
                    <h3>No locations found</h3>
                    <p>Search for a location, click on the map, or adjust your filters</p>
                  </div>
                )}
                {activeTab === 'events' && events.length === 0 && (
                  <div className="no-results">
                    <span className="no-results-icon">🎉</span>
                    <h3>No events found</h3>
                    <p>Try adjusting your search radius or date range</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Right Panel - Map */}
        <div className="right-panel">
          <div className="map-container">
            <MapView
              center={mapCenter}
              zoom={6}
              markers={markers}
              onMapClick={handleMapClick}
              showLegend={true}
            />
          </div>

          {/* Selected Locations Summary */}
          {selectedLocations.length > 0 && (
            <div className="selected-summary">
              <div className="summary-header">
                <h3>Selected Locations</h3>
                <span className="selected-count">{selectedLocations.length}</span>
              </div>
              <div className="selected-list">
                {selectedLocations.map((location, idx) => (
                  <div key={location.id} className="selected-item">
                    <span className="selected-number">{idx + 1}</span>
                    <div className="selected-info">
                      <span className="selected-name">{location.name}</span>
                      <span className="selected-type">{location.type}</span>
                    </div>
                    <button
                      className="remove-selected"
                      onClick={() => handleAddToTrip(location)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer Navigation */}
      <div className="step4-footer">
        <button className="btn btn-outline" onClick={onBack}>
          ← Back
        </button>
        <div className="footer-info">
          {selectedLocations.length > 0 ? (
            <span className="info-text">
              ✓ {selectedLocations.length} location{selectedLocations.length > 1 ? 's' : ''} selected
            </span>
          ) : (
            <span className="info-text hint">
              Add locations to your trip to continue
            </span>
          )}
        </div>
        <button
          className="btn btn-primary"
          onClick={handleContinue}
          disabled={selectedLocations.length === 0}
        >
          Continue to Route Planning →
        </button>
      </div>
    </div>
  );
};

export default Step4_Recommendations;
