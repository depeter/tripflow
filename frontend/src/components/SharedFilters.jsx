import React, { useState, useEffect } from 'react';
import './SharedFilters.css';

const SharedFilters = ({
  filters,
  onFilterChange,
  loading = false
}) => {
  const [localSearchText, setLocalSearchText] = useState(filters.searchText || '');
  const [searchDebounceTimer, setSearchDebounceTimer] = useState(null);

  // Sync with parent filters
  useEffect(() => {
    setLocalSearchText(filters.searchText || '');
  }, [filters.searchText]);

  const handleSearchChange = (e) => {
    const newValue = e.target.value;
    setLocalSearchText(newValue);

    // Clear existing timer
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }

    // Set new timer to trigger search after 500ms of no typing
    const timer = setTimeout(() => {
      onFilterChange({ ...filters, searchText: newValue });
    }, 500);
    setSearchDebounceTimer(timer);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    // Clear debounce timer and trigger immediately
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }
    onFilterChange({ ...filters, searchText: localSearchText });
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (searchDebounceTimer) {
        clearTimeout(searchDebounceTimer);
      }
    };
  }, [searchDebounceTimer]);

  const handleRadiusChange = (e) => {
    onFilterChange({ ...filters, radiusKm: Number(e.target.value) });
  };

  const handleShowToggle = (type) => {
    if (type === 'events') {
      onFilterChange({ ...filters, showEvents: !filters.showEvents });
    } else if (type === 'locations') {
      onFilterChange({ ...filters, showLocations: !filters.showLocations });
    }
  };

  return (
    <div className="shared-filters">
      {/* Show Filter (Events/Locations/Both) */}
      <div className="filter-section">
        <h3>Show</h3>
        <div className="filter-show-options">
          <label className="filter-checkbox-label">
            <input
              type="checkbox"
              checked={filters.showEvents !== false}
              onChange={() => handleShowToggle('events')}
              className="filter-checkbox"
            />
            <span className="filter-checkbox-text">🎉 Events</span>
          </label>
          <label className="filter-checkbox-label">
            <input
              type="checkbox"
              checked={filters.showLocations !== false}
              onChange={() => handleShowToggle('locations')}
              className="filter-checkbox"
            />
            <span className="filter-checkbox-text">📍 Places</span>
          </label>
        </div>
      </div>

      {/* Search Box */}
      <div className="filter-section">
        <h3>Search</h3>
        <form onSubmit={handleSearchSubmit} className="filter-search-form">
          <input
            type="text"
            placeholder="Search events and places..."
            value={localSearchText}
            onChange={handleSearchChange}
            className="filter-search-input"
          />
          <button
            type="submit"
            className="filter-search-btn"
            disabled={loading}
          >
            🔎
          </button>
        </form>
      </div>

      {/* Radius */}
      <div className="filter-section">
        <h3>Distance</h3>
        <div className="filter-radius">
          <select
            value={filters.radiusKm}
            onChange={handleRadiusChange}
            className="filter-select"
          >
            <option value={5}>5 km</option>
            <option value={10}>10 km</option>
            <option value={25}>25 km</option>
            <option value={50}>50 km</option>
            <option value={100}>100 km</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default SharedFilters;
