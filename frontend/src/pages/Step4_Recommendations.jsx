import React, { useState, useEffect, useCallback } from 'react';
import { useTripContext } from '../context/TripContext';
import LocationCard from '../components/LocationCard';
import MapView from '../components/MapView';
import LoadingSpinner from '../components/LoadingSpinner';
import { getRecommendations } from '../services/tripsService';
import { geocodeAddress, reverseGeocode, debounce } from '../services/geocodingService';
import './Step4_Recommendations.css';

const Step4_Recommendations = ({ onNext, onBack }) => {
  const { tripData, updateTripData } = useTripContext();
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
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
    loadRecommendations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, sortBy]);

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

    // Combine recommendations and custom locations
    const allLocations = [...recommendations, ...customLocations];

    // Location markers
    allLocations.forEach((location, idx) => {
      const isSelected = isLocationSelected(location.id);
      markers.push({
        id: `loc-${location.id}`,
        position: [location.coordinates.lat, location.coordinates.lng],
        popup: location.type === 'custom'
          ? `${location.name} (Custom)`
          : `${location.name} - ${location.match_score}% match`,
        numbered: isSelected,
        number: isSelected ? selectedLocations.findIndex(l => l.id === location.id) + 1 : undefined,
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
              <h2>Find Locations</h2>
              <p className="recommendations-subtitle">
                Search for a place, click on the map, or browse <strong>{recommendations.length} recommendations</strong>
              </p>
            </div>
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
            {isLoading ? (
              <div className="loading-container">
                <LoadingSpinner message="Finding perfect locations for you..." />
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

                {/* Recommendations */}
                {recommendations.length > 0 && (
                  <>
                    {customLocations.length > 0 && (
                      <div className="section-divider">
                        <span className="divider-text">Recommended Locations ({recommendations.length})</span>
                      </div>
                    )}
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

                {/* No Results */}
                {recommendations.length === 0 && customLocations.length === 0 && (
                  <div className="no-results">
                    <span className="no-results-icon">🔍</span>
                    <h3>No locations found</h3>
                    <p>Search for a location, click on the map, or adjust your filters</p>
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
