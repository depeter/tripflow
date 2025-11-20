import React from 'react';
import SharedFilters from './SharedFilters';
import EventFilters from './EventFilters';
import LocationFilters from './LocationFilters';
import './FilterSidebar.css';

const FilterSidebar = ({
  filters,
  onFilterChange,
  isOpen,
  onToggle,
  eventsCount = 0,
  loading = false
}) => {
  // Count total active filters
  const countActiveFilters = () => {
    let count = 0;

    // Count search text
    if (filters.searchText?.trim()) count++;

    // Count event filters
    if (filters.showEvents) {
      count += filters.eventFilters?.categories?.length || 0;
      count += filters.eventFilters?.eventTypes?.length || 0;
      count += filters.eventFilters?.timeOfDay?.length || 0;
      if (filters.eventFilters?.freeOnly) count++;
      if (filters.eventFilters?.dateStart) count++;
      if (filters.eventFilters?.priceMin || filters.eventFilters?.priceMax) count++;
    }

    // Count location filters
    if (filters.showLocations) {
      count += filters.locationFilters?.locationTypes?.length || 0;
      count += filters.locationFilters?.amenities?.length || 0;
      count += filters.locationFilters?.features?.length || 0;
      count += filters.locationFilters?.priceTypes?.length || 0;
      if (filters.locationFilters?.minRating) count++;
      if (filters.locationFilters?.openNow) count++;
      if (filters.locationFilters?.is24_7) count++;
      if (filters.locationFilters?.noBookingRequired) count++;
      if (filters.locationFilters?.minCapacity) count++;
    }

    return count;
  };

  const handleClearFilters = () => {
    onFilterChange({
      showEvents: true,
      showLocations: true,
      searchText: '',
      radiusKm: filters.radiusKm, // Keep radius

      eventFilters: {
        categories: [],
        eventTypes: [],
        dateStart: null,
        dateEnd: null,
        datePreset: null,
        priceMin: null,
        priceMax: null,
        freeOnly: false,
        timeOfDay: []
      },

      locationFilters: {
        locationTypes: [],
        minRating: null,
        priceTypes: [],
        amenities: [],
        features: [],
        openNow: false,
        is24_7: false,
        noBookingRequired: false,
        minCapacity: null
      }
    });
  };

  const activeFilterCount = countActiveFilters();
  const hasActiveFilters = activeFilterCount > 0;

  // Determine which filter sections to show
  const showBoth = filters.showEvents && filters.showLocations;
  const showOnlyEvents = filters.showEvents && !filters.showLocations;
  const showOnlyLocations = !filters.showEvents && filters.showLocations;

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
        {hasActiveFilters && (
          <span className="filter-badge">{activeFilterCount}</span>
        )}
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
          {/* Shared Filters - Always visible */}
          <SharedFilters
            filters={filters}
            onFilterChange={onFilterChange}
            loading={loading}
          />

          {/* Conditional Rendering based on selected types */}
          {showOnlyEvents && (
            <EventFilters
              filters={filters}
              onFilterChange={onFilterChange}
            />
          )}

          {showOnlyLocations && (
            <LocationFilters
              filters={filters}
              onFilterChange={onFilterChange}
            />
          )}

          {showBoth && (
            <>
              <EventFilters
                filters={filters}
                onFilterChange={onFilterChange}
              />
              <LocationFilters
                filters={filters}
                onFilterChange={onFilterChange}
              />
            </>
          )}

          {/* Results Summary */}
          <div className="filter-results">
            <p className="filter-results-count">
              {loading ? 'Searching...' : `${eventsCount} result${eventsCount !== 1 ? 's' : ''} found`}
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
                Clear All Filters
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
