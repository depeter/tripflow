import React, { useState, useEffect } from 'react';
import './FilterSidebar.css';

const FilterSidebar = ({
  filters,
  onFilterChange,
  isOpen,
  onToggle,
  eventsCount = 0,
  loading = false
}) => {
  const [localFilters, setLocalFilters] = useState(filters);

  // Sync with parent filters
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Available categories with icons (values match database UPPERCASE format)
  const categories = [
    { value: 'FESTIVAL', label: 'Festival', icon: '🎉' },
    { value: 'CONCERT', label: 'Concert', icon: '🎵' },
    { value: 'SPORTS', label: 'Sports', icon: '⚽' },
    { value: 'MARKET', label: 'Market', icon: '🛍️' },
    { value: 'EXHIBITION', label: 'Exhibition', icon: '🖼️' },
    { value: 'THEATER', label: 'Theater', icon: '🎭' },
    { value: 'CULTURAL', label: 'Cultural', icon: '🏛️' },
    { value: 'FOOD', label: 'Food & Drink', icon: '🍽️' },
    { value: 'OUTDOOR', label: 'Outdoor', icon: '🏕️' },
    { value: 'CAMPING', label: 'Camping', icon: '⛺' },
    { value: 'PARKING', label: 'Parking', icon: '🅿️' },
    { value: 'OTHER', label: 'Other', icon: '📍' }
  ];

  // Event types (can be expanded based on your data)
  const eventTypes = [
    'festival',
    'workshop',
    'exhibition',
    'performance',
    'conference',
    'market',
    'sports',
    'concert',
    'party'
  ];

  const handleCategoryToggle = (categoryValue) => {
    const newCategories = localFilters.selectedCategories.includes(categoryValue)
      ? localFilters.selectedCategories.filter(c => c !== categoryValue)
      : [...localFilters.selectedCategories, categoryValue];

    const newFilters = { ...localFilters, selectedCategories: newCategories };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleEventTypeToggle = (eventType) => {
    const newEventTypes = localFilters.selectedEventTypes.includes(eventType)
      ? localFilters.selectedEventTypes.filter(t => t !== eventType)
      : [...localFilters.selectedEventTypes, eventType];

    const newFilters = { ...localFilters, selectedEventTypes: newEventTypes };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  // Debounce timer for search text
  const [searchDebounceTimer, setSearchDebounceTimer] = useState(null);

  const handleSearchChange = (e) => {
    const newValue = e.target.value;
    const newFilters = { ...localFilters, searchText: newValue };
    setLocalFilters(newFilters);

    // Clear existing timer
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }

    // Set new timer to trigger search after 500ms of no typing
    const timer = setTimeout(() => {
      onFilterChange(newFilters);
    }, 500);
    setSearchDebounceTimer(timer);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    // Clear debounce timer and trigger immediately
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }
    onFilterChange(localFilters);
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
    const newFilters = { ...localFilters, radiusKm: Number(e.target.value) };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleFreeOnlyChange = (e) => {
    const newFilters = { ...localFilters, freeOnly: e.target.checked };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleClearFilters = () => {
    const clearedFilters = {
      selectedCategories: [],
      selectedEventTypes: [],
      searchText: '',
      radiusKm: localFilters.radiusKm,
      freeOnly: false
    };
    setLocalFilters(clearedFilters);
    onFilterChange(clearedFilters);
    // Search will trigger automatically via useEffect in parent
  };

  const hasActiveFilters =
    localFilters.selectedCategories.length > 0 ||
    localFilters.selectedEventTypes.length > 0 ||
    localFilters.searchText.trim() !== '' ||
    localFilters.freeOnly;

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        className="filter-toggle-mobile"
        onClick={onToggle}
        aria-label="Toggle filters"
      >
        <span className="filter-icon">⚙️</span>
        <span>Filters</span>
        {hasActiveFilters && <span className="filter-badge">{
          localFilters.selectedCategories.length +
          localFilters.selectedEventTypes.length +
          (localFilters.freeOnly ? 1 : 0) +
          (localFilters.searchText.trim() ? 1 : 0)
        }</span>}
      </button>

      {/* Sidebar */}
      <div className={`filter-sidebar ${isOpen ? 'open' : ''}`}>
        <div className="filter-sidebar-header">
          <h2>🔍 Filters</h2>
          <button
            className="filter-close-btn"
            onClick={onToggle}
            aria-label="Close filters"
          >
            ✕
          </button>
        </div>

        <div className="filter-sidebar-content">
          {/* Show Filter (Events/Locations/Both) */}
          <div className="filter-section">
            <h3>Show</h3>
            <div className="filter-show-options">
              <label className="filter-checkbox-label">
                <input
                  type="checkbox"
                  checked={localFilters.showEvents !== false}
                  onChange={(e) => {
                    const newFilters = { ...localFilters, showEvents: e.target.checked };
                    setLocalFilters(newFilters);
                    onFilterChange(newFilters);
                  }}
                  className="filter-checkbox"
                />
                <span className="filter-checkbox-text">🎉 Events</span>
              </label>
              <label className="filter-checkbox-label">
                <input
                  type="checkbox"
                  checked={localFilters.showLocations !== false}
                  onChange={(e) => {
                    const newFilters = { ...localFilters, showLocations: e.target.checked };
                    setLocalFilters(newFilters);
                    onFilterChange(newFilters);
                  }}
                  className="filter-checkbox"
                />
                <span className="filter-checkbox-text">📍 Places (Camping/Parking)</span>
              </label>
            </div>
          </div>

          {/* Search Box */}
          <div className="filter-section">
            <h3>Search</h3>
            <form onSubmit={handleSearchSubmit} className="filter-search-form">
              <input
                type="text"
                placeholder="e.g., christmas, jazz, food..."
                value={localFilters.searchText}
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
                value={localFilters.radiusKm}
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

          {/* Categories */}
          <div className="filter-section">
            <h3>Categories</h3>
            <div className="filter-chips">
              {categories.map(category => (
                <button
                  key={category.value}
                  className={`filter-chip ${
                    localFilters.selectedCategories.includes(category.value)
                      ? 'active'
                      : ''
                  }`}
                  onClick={() => handleCategoryToggle(category.value)}
                >
                  <span className="filter-chip-icon">{category.icon}</span>
                  <span className="filter-chip-label">{category.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Event Types */}
          <div className="filter-section">
            <h3>Event Types</h3>
            <div className="filter-checkboxes">
              {eventTypes.map(type => (
                <label key={type} className="filter-checkbox-label">
                  <input
                    type="checkbox"
                    checked={localFilters.selectedEventTypes.includes(type)}
                    onChange={() => handleEventTypeToggle(type)}
                    className="filter-checkbox"
                  />
                  <span className="filter-checkbox-text">
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Price Filter */}
          <div className="filter-section">
            <h3>Price</h3>
            <label className="filter-checkbox-label filter-free-only">
              <input
                type="checkbox"
                checked={localFilters.freeOnly}
                onChange={handleFreeOnlyChange}
                className="filter-checkbox"
              />
              <span className="filter-checkbox-text">Free events only</span>
            </label>
          </div>

          {/* Results Summary */}
          <div className="filter-results">
            <p className="filter-results-count">
              {loading ? 'Searching...' : `${eventsCount} results found`}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="filter-actions">
            {hasActiveFilters && (
              <button
                className="filter-clear-btn"
                onClick={handleClearFilters}
                disabled={loading}
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Overlay for mobile - outside sidebar so it sits behind */}
      {isOpen && (
        <div
          className="filter-sidebar-overlay"
          onClick={onToggle}
        />
      )}
    </>
  );
};

export default FilterSidebar;
