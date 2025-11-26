import React, { useState } from 'react';
import './EventFilters.css';

const EventFilters = ({
  filters,
  onFilterChange
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

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
    { value: 'OTHER', label: 'Other', icon: '📍' }
  ];


  // Time of day options
  const timeOfDayOptions = [
    { value: 'morning', label: 'Morning (6am-12pm)', icon: '🌅' },
    { value: 'afternoon', label: 'Afternoon (12pm-6pm)', icon: '☀️' },
    { value: 'evening', label: 'Evening (6pm-12am)', icon: '🌆' },
    { value: 'night', label: 'Night (12am-6am)', icon: '🌙' }
  ];

  // Date preset options
  const datePresets = [
    { value: 'today', label: 'Today' },
    { value: 'weekend', label: 'This Weekend' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' }
  ];

  const handleCategoryToggle = (categoryValue) => {
    const currentCategories = filters.eventFilters?.categories || [];
    const newCategories = currentCategories.includes(categoryValue)
      ? currentCategories.filter(c => c !== categoryValue)
      : [...currentCategories, categoryValue];

    onFilterChange({
      ...filters,
      eventFilters: {
        ...filters.eventFilters,
        categories: newCategories
      }
    });
  };


  const handleTimeOfDayToggle = (timeValue) => {
    const currentTimes = filters.eventFilters?.timeOfDay || [];
    const newTimes = currentTimes.includes(timeValue)
      ? currentTimes.filter(t => t !== timeValue)
      : [...currentTimes, timeValue];

    onFilterChange({
      ...filters,
      eventFilters: {
        ...filters.eventFilters,
        timeOfDay: newTimes
      }
    });
  };

  const handleDatePresetChange = (preset) => {
    const now = new Date();
    let dateStart = null;
    let dateEnd = null;

    switch (preset) {
      case 'today':
        dateStart = new Date(now.setHours(0, 0, 0, 0));
        dateEnd = new Date(now.setHours(23, 59, 59, 999));
        break;
      case 'weekend':
        // Find next Saturday
        const daysUntilSaturday = (6 - now.getDay() + 7) % 7 || 0;
        dateStart = new Date(now);
        dateStart.setDate(now.getDate() + daysUntilSaturday);
        dateStart.setHours(0, 0, 0, 0);
        dateEnd = new Date(dateStart);
        dateEnd.setDate(dateStart.getDate() + 1);
        dateEnd.setHours(23, 59, 59, 999);
        break;
      case 'week':
        dateStart = new Date(now.setHours(0, 0, 0, 0));
        dateEnd = new Date(now);
        dateEnd.setDate(now.getDate() + 7);
        dateEnd.setHours(23, 59, 59, 999);
        break;
      case 'month':
        dateStart = new Date(now.setHours(0, 0, 0, 0));
        dateEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);
        break;
      default:
        break;
    }

    onFilterChange({
      ...filters,
      eventFilters: {
        ...filters.eventFilters,
        dateStart: dateStart?.toISOString(),
        dateEnd: dateEnd?.toISOString(),
        datePreset: preset
      }
    });
  };

  const handleCustomDateChange = (field, value) => {
    onFilterChange({
      ...filters,
      eventFilters: {
        ...filters.eventFilters,
        [field]: value,
        datePreset: null // Clear preset when custom date is set
      }
    });
  };

  const handleFreeOnlyChange = (checked) => {
    onFilterChange({
      ...filters,
      eventFilters: {
        ...filters.eventFilters,
        freeOnly: checked
      }
    });
  };

  const handlePriceRangeChange = (field, value) => {
    onFilterChange({
      ...filters,
      eventFilters: {
        ...filters.eventFilters,
        [field]: value ? parseFloat(value) : null
      }
    });
  };

  // Count active filters
  const activeFilterCount = [
    (filters.eventFilters?.categories?.length || 0),
    (filters.eventFilters?.timeOfDay?.length || 0),
    (filters.eventFilters?.freeOnly ? 1 : 0),
    (filters.eventFilters?.dateStart ? 1 : 0),
    (filters.eventFilters?.priceMin || filters.eventFilters?.priceMax ? 1 : 0)
  ].reduce((a, b) => a + b, 0);

  return (
    <div className="event-filters">
      <div className="filter-section-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>
          🎭 Event Filters
          {activeFilterCount > 0 && (
            <span className="filter-count-badge">{activeFilterCount}</span>
          )}
        </h3>
        <span className="filter-expand-icon">{isExpanded ? '▼' : '▶'}</span>
      </div>

      {isExpanded && (
        <div className="filter-section-content">
          {/* Date Presets */}
          <div className="filter-subsection">
            <h4>📅 When</h4>
            <div className="filter-date-presets">
              {datePresets.map(preset => (
                <button
                  key={preset.value}
                  className={`filter-preset-btn ${
                    filters.eventFilters?.datePreset === preset.value ? 'active' : ''
                  }`}
                  onClick={() => handleDatePresetChange(preset.value)}
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {/* Custom Date Range */}
            <div className="filter-custom-date">
              <label className="filter-date-label">
                <span>From:</span>
                <input
                  type="date"
                  value={filters.eventFilters?.dateStart?.split('T')[0] || ''}
                  onChange={(e) => handleCustomDateChange('dateStart', e.target.value ? new Date(e.target.value).toISOString() : null)}
                  className="filter-date-input"
                />
              </label>
              <label className="filter-date-label">
                <span>To:</span>
                <input
                  type="date"
                  value={filters.eventFilters?.dateEnd?.split('T')[0] || ''}
                  onChange={(e) => handleCustomDateChange('dateEnd', e.target.value ? new Date(e.target.value).toISOString() : null)}
                  className="filter-date-input"
                />
              </label>
            </div>
          </div>

          {/* Categories */}
          <div className="filter-subsection">
            <h4>🎭 Category</h4>
            <div className="filter-chips">
              {categories.map(category => (
                <button
                  key={category.value}
                  className={`filter-chip ${
                    (filters.eventFilters?.categories || []).includes(category.value)
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

          {/* Time of Day */}
          <div className="filter-subsection">
            <h4>🕒 Time of Day</h4>
            <div className="filter-checkboxes">
              {timeOfDayOptions.map(time => (
                <label key={time.value} className="filter-checkbox-label">
                  <input
                    type="checkbox"
                    checked={(filters.eventFilters?.timeOfDay || []).includes(time.value)}
                    onChange={() => handleTimeOfDayToggle(time.value)}
                    className="filter-checkbox"
                  />
                  <span className="filter-checkbox-text">
                    {time.icon} {time.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Price */}
          <div className="filter-subsection">
            <h4>💰 Price</h4>
            <label className="filter-checkbox-label filter-free-only">
              <input
                type="checkbox"
                checked={filters.eventFilters?.freeOnly || false}
                onChange={(e) => handleFreeOnlyChange(e.target.checked)}
                className="filter-checkbox"
              />
              <span className="filter-checkbox-text">Free events only</span>
            </label>

            {!filters.eventFilters?.freeOnly && (
              <div className="filter-price-range">
                <label className="filter-price-label">
                  <span>Min (€):</span>
                  <input
                    type="number"
                    min="0"
                    step="5"
                    placeholder="0"
                    value={filters.eventFilters?.priceMin || ''}
                    onChange={(e) => handlePriceRangeChange('priceMin', e.target.value)}
                    className="filter-price-input"
                  />
                </label>
                <label className="filter-price-label">
                  <span>Max (€):</span>
                  <input
                    type="number"
                    min="0"
                    step="5"
                    placeholder="100"
                    value={filters.eventFilters?.priceMax || ''}
                    onChange={(e) => handlePriceRangeChange('priceMax', e.target.value)}
                    className="filter-price-input"
                  />
                </label>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EventFilters;
