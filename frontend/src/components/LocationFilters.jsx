import React, { useState } from 'react';
import './LocationFilters.css';

const LocationFilters = ({
  filters,
  onFilterChange
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  // Location types with icons
  const locationTypes = [
    { value: 'CAMPSITE', label: 'Campsite', icon: '⛺' },
    { value: 'PARKING', label: 'Parking', icon: '🅿️' },
    { value: 'REST_AREA', label: 'Rest Area', icon: '🛑' },
    { value: 'SERVICE_AREA', label: 'Service', icon: '🔧' },
    { value: 'POI', label: 'POI', icon: '📍' },
    { value: 'RESTAURANT', label: 'Restaurant', icon: '🍽️' },
    { value: 'HOTEL', label: 'Hotel', icon: '🏨' },
    { value: 'ATTRACTION', label: 'Attraction', icon: '🎡' },
    { value: 'ACTIVITY', label: 'Activity', icon: '🎯' }
  ];

  // Common amenities
  const amenities = [
    { value: 'wifi', label: 'WiFi', icon: '📶' },
    { value: 'electricity', label: 'Electricity', icon: '⚡' },
    { value: 'showers', label: 'Showers', icon: '🚿' },
    { value: 'toilets', label: 'Toilets', icon: '🚽' },
    { value: 'water', label: 'Water', icon: '💧' },
    { value: 'waste_disposal', label: 'Waste', icon: '🗑️' },
    { value: 'pet_friendly', label: 'Pets', icon: '🐕' },
    { value: 'family_friendly', label: 'Family', icon: '👨‍👩‍👧' }
  ];

  // Facilities
  const facilities = [
    { value: 'restaurant', label: 'Restaurant', icon: '🍽️' },
    { value: 'shop', label: 'Shop', icon: '🏪' },
    { value: 'laundry', label: 'Laundry', icon: '🧺' },
    { value: 'playground', label: 'Playground', icon: '🎪' },
    { value: 'swimming_pool', label: 'Pool', icon: '🏊' }
  ];

  // Price tiers
  const priceTiers = [
    { value: 'free', label: 'Free', icon: '🆓' },
    { value: 'paid_low', label: '€ (€0-€10)', icon: '💰' },
    { value: 'paid_medium', label: '€€ (€10-€25)', icon: '💰💰' },
    { value: 'paid_high', label: '€€€ (€25-€50)', icon: '💰💰💰' },
    { value: 'paid_premium', label: '€€€€ (€50+)', icon: '💎' }
  ];

  const handleLocationTypeToggle = (typeValue) => {
    const currentTypes = filters.locationFilters?.locationTypes || [];
    const newTypes = currentTypes.includes(typeValue)
      ? currentTypes.filter(t => t !== typeValue)
      : [...currentTypes, typeValue];

    onFilterChange({
      ...filters,
      locationFilters: {
        ...filters.locationFilters,
        locationTypes: newTypes
      }
    });
  };

  const handleAmenityToggle = (amenityValue) => {
    const currentAmenities = filters.locationFilters?.amenities || [];
    const newAmenities = currentAmenities.includes(amenityValue)
      ? currentAmenities.filter(a => a !== amenityValue)
      : [...currentAmenities, amenityValue];

    onFilterChange({
      ...filters,
      locationFilters: {
        ...filters.locationFilters,
        amenities: newAmenities
      }
    });
  };

  const handleFacilityToggle = (facilityValue) => {
    const currentFacilities = filters.locationFilters?.features || [];
    const newFacilities = currentFacilities.includes(facilityValue)
      ? currentFacilities.filter(f => f !== facilityValue)
      : [...currentFacilities, facilityValue];

    onFilterChange({
      ...filters,
      locationFilters: {
        ...filters.locationFilters,
        features: newFacilities
      }
    });
  };

  const handleRatingChange = (value) => {
    onFilterChange({
      ...filters,
      locationFilters: {
        ...filters.locationFilters,
        minRating: value
      }
    });
  };

  const handlePriceTierToggle = (tier) => {
    const currentTiers = filters.locationFilters?.priceTypes || [];
    const newTiers = currentTiers.includes(tier)
      ? currentTiers.filter(t => t !== tier)
      : [...currentTiers, tier];

    onFilterChange({
      ...filters,
      locationFilters: {
        ...filters.locationFilters,
        priceTypes: newTiers
      }
    });
  };

  const handleBooleanFilterChange = (field, value) => {
    onFilterChange({
      ...filters,
      locationFilters: {
        ...filters.locationFilters,
        [field]: value
      }
    });
  };

  const handleCapacityChange = (value) => {
    onFilterChange({
      ...filters,
      locationFilters: {
        ...filters.locationFilters,
        minCapacity: value ? parseInt(value) : null
      }
    });
  };

  // Count active filters
  const activeFilterCount = [
    (filters.locationFilters?.locationTypes?.length || 0),
    (filters.locationFilters?.amenities?.length || 0),
    (filters.locationFilters?.features?.length || 0),
    (filters.locationFilters?.priceTypes?.length || 0),
    (filters.locationFilters?.minRating ? 1 : 0),
    (filters.locationFilters?.openNow ? 1 : 0),
    (filters.locationFilters?.is24_7 ? 1 : 0),
    (filters.locationFilters?.noBookingRequired ? 1 : 0),
    (filters.locationFilters?.minCapacity ? 1 : 0)
  ].reduce((a, b) => a + b, 0);

  return (
    <div className="location-filters">
      <div className="filter-section-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>
          📍 Location Filters
          {activeFilterCount > 0 && (
            <span className="filter-count-badge">{activeFilterCount}</span>
          )}
        </h3>
        <span className="filter-expand-icon">{isExpanded ? '▼' : '▶'}</span>
      </div>

      {isExpanded && (
        <div className="filter-section-content">
          {/* Location Types */}
          <div className="filter-subsection">
            <h4>📍 Location Type</h4>
            <div className="filter-chips">
              {locationTypes.map(type => (
                <button
                  key={type.value}
                  className={`filter-chip ${
                    (filters.locationFilters?.locationTypes || []).includes(type.value)
                      ? 'active'
                      : ''
                  }`}
                  onClick={() => handleLocationTypeToggle(type.value)}
                >
                  <span className="filter-chip-icon">{type.icon}</span>
                  <span className="filter-chip-label">{type.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Rating */}
          <div className="filter-subsection">
            <h4>⭐ Rating</h4>
            <div className="filter-rating-options">
              <label className="filter-radio-label">
                <input
                  type="radio"
                  name="rating"
                  checked={!filters.locationFilters?.minRating}
                  onChange={() => handleRatingChange(null)}
                  className="filter-radio"
                />
                <span className="filter-radio-text">Any rating</span>
              </label>
              <label className="filter-radio-label">
                <input
                  type="radio"
                  name="rating"
                  checked={filters.locationFilters?.minRating === 2}
                  onChange={() => handleRatingChange(2)}
                  className="filter-radio"
                />
                <span className="filter-radio-text">⭐⭐ 2+ stars</span>
              </label>
              <label className="filter-radio-label">
                <input
                  type="radio"
                  name="rating"
                  checked={filters.locationFilters?.minRating === 3}
                  onChange={() => handleRatingChange(3)}
                  className="filter-radio"
                />
                <span className="filter-radio-text">⭐⭐⭐ 3+ stars</span>
              </label>
              <label className="filter-radio-label">
                <input
                  type="radio"
                  name="rating"
                  checked={filters.locationFilters?.minRating === 4}
                  onChange={() => handleRatingChange(4)}
                  className="filter-radio"
                />
                <span className="filter-radio-text">⭐⭐⭐⭐ 4+ stars</span>
              </label>
            </div>
          </div>

          {/* Price Tiers */}
          <div className="filter-subsection">
            <h4>💰 Price Range</h4>
            <div className="filter-price-tiers">
              {priceTiers.map(tier => (
                <label key={tier.value} className="filter-checkbox-label">
                  <input
                    type="checkbox"
                    checked={(filters.locationFilters?.priceTypes || []).includes(tier.value)}
                    onChange={() => handlePriceTierToggle(tier.value)}
                    className="filter-checkbox"
                  />
                  <span className="filter-checkbox-text">
                    {tier.icon} {tier.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Amenities */}
          <div className="filter-subsection">
            <h4>🏕️ Amenities</h4>
            <div className="filter-amenities-grid">
              {amenities.map(amenity => (
                <label key={amenity.value} className="filter-amenity-label">
                  <input
                    type="checkbox"
                    checked={(filters.locationFilters?.amenities || []).includes(amenity.value)}
                    onChange={() => handleAmenityToggle(amenity.value)}
                    className="filter-checkbox"
                  />
                  <span className="filter-amenity-content">
                    <span className="filter-amenity-icon">{amenity.icon}</span>
                    <span className="filter-amenity-text">{amenity.label}</span>
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Facilities */}
          <div className="filter-subsection">
            <h4>🚿 Facilities</h4>
            <div className="filter-amenities-grid">
              {facilities.map(facility => (
                <label key={facility.value} className="filter-amenity-label">
                  <input
                    type="checkbox"
                    checked={(filters.locationFilters?.features || []).includes(facility.value)}
                    onChange={() => handleFacilityToggle(facility.value)}
                    className="filter-checkbox"
                  />
                  <span className="filter-amenity-content">
                    <span className="filter-amenity-icon">{facility.icon}</span>
                    <span className="filter-amenity-text">{facility.label}</span>
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Availability */}
          <div className="filter-subsection">
            <h4>🕐 Availability</h4>
            <div className="filter-checkboxes">
              <label className="filter-checkbox-label">
                <input
                  type="checkbox"
                  checked={filters.locationFilters?.openNow || false}
                  onChange={(e) => handleBooleanFilterChange('openNow', e.target.checked)}
                  className="filter-checkbox"
                />
                <span className="filter-checkbox-text">Open now</span>
              </label>
              <label className="filter-checkbox-label">
                <input
                  type="checkbox"
                  checked={filters.locationFilters?.is24_7 || false}
                  onChange={(e) => handleBooleanFilterChange('is24_7', e.target.checked)}
                  className="filter-checkbox"
                />
                <span className="filter-checkbox-text">24/7 access</span>
              </label>
              <label className="filter-checkbox-label">
                <input
                  type="checkbox"
                  checked={filters.locationFilters?.noBookingRequired || false}
                  onChange={(e) => handleBooleanFilterChange('noBookingRequired', e.target.checked)}
                  className="filter-checkbox"
                />
                <span className="filter-checkbox-text">No booking required</span>
              </label>
            </div>
          </div>

          {/* Capacity */}
          <div className="filter-subsection">
            <h4>👥 Capacity</h4>
            <label className="filter-capacity-label">
              <span>Minimum spots available:</span>
              <input
                type="number"
                min="1"
                step="1"
                placeholder="Any"
                value={filters.locationFilters?.minCapacity || ''}
                onChange={(e) => handleCapacityChange(e.target.value)}
                className="filter-capacity-input"
              />
            </label>
          </div>
        </div>
      )}
    </div>
  );
};

export default LocationFilters;
