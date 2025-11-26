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

  const handleTypeChange = (type) => {
    onFilterChange({ ...filters, selectedType: type });
  };

  return (
    <div className="shared-filters">
      {/* Search Box */}
      <div className="filter-section">
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

      {/* Radius - inline label */}
      <div className="filter-section filter-section-inline">
        <label className="filter-inline-label">Distance</label>
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

      {/* Type Tabs (Events/Locations) */}
      <div className="filter-section">
        <div className="filter-tabs">
          <button
            type="button"
            className={`filter-tab ${filters.selectedType === 'events' ? 'active' : ''}`}
            onClick={() => handleTypeChange('events')}
          >
            🎉 Events
          </button>
          <button
            type="button"
            className={`filter-tab ${filters.selectedType === 'locations' ? 'active' : ''}`}
            onClick={() => handleTypeChange('locations')}
          >
            📍 Places
          </button>
        </div>
      </div>
    </div>
  );
};

export default SharedFilters;
