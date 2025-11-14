import React from 'react';
import { useTripContext } from '../context/TripContext';
import './Step3_Preferences.css';

const INTERESTS = [
  { id: 'beach', label: 'Beach', icon: '🏖️' },
  { id: 'mountains', label: 'Mountains', icon: '🏔️' },
  { id: 'nature', label: 'Nature', icon: '🌲' },
  { id: 'culture', label: 'Culture', icon: '🏛️' },
  { id: 'art', label: 'Art', icon: '🎨' },
  { id: 'food_wine', label: 'Food & Wine', icon: '🍷' },
  { id: 'sports', label: 'Sports', icon: '⚽' },
  { id: 'events', label: 'Events', icon: '🎪' },
  { id: 'camping', label: 'Camping', icon: '🏕️' },
  { id: 'cycling', label: 'Cycling', icon: '🚴' },
  { id: 'hiking', label: 'Hiking', icon: '🥾' },
  { id: 'photography', label: 'Photography', icon: '📸' }
];

const ENVIRONMENTS = [
  { id: 'sunny', label: 'Sunny spots', icon: '☀️' },
  { id: 'coastal', label: 'Coastal', icon: '🌊' },
  { id: 'mountains', label: 'Mountains', icon: '🏔️' },
  { id: 'city', label: 'City life', icon: '🏙️' },
  { id: 'countryside', label: 'Countryside', icon: '🌾' },
  { id: 'forests', label: 'Forests', icon: '🌲' }
];

const AMENITIES = [
  { id: 'electricity', label: 'Electricity', icon: '⚡' },
  { id: 'water', label: 'Water', icon: '💧' },
  { id: 'showers', label: 'Showers', icon: '🚿' },
  { id: 'wifi', label: 'WiFi', icon: '📶' },
  { id: 'toilets', label: 'Toilets', icon: '🚽' },
  { id: 'restaurant', label: 'Restaurant', icon: '🍽️' }
];

const ACTIVITY_LEVELS = [
  { id: 'low', label: 'Low', description: 'Relaxed and easy-going' },
  { id: 'moderate', label: 'Moderate', description: 'Balanced mix of activity' },
  { id: 'high', label: 'High', description: 'Active and adventurous' }
];

const Step3_Preferences = ({ onNext, onBack }) => {
  const { tripData, updateTripData } = useTripContext();
  const isMultiDay = tripData.trip_type === 'multi_day';

  const toggleInterest = (interestId) => {
    const interests = tripData.interests || [];
    if (interests.includes(interestId)) {
      updateTripData({ interests: interests.filter(id => id !== interestId) });
    } else {
      updateTripData({ interests: [...interests, interestId] });
    }
  };

  const toggleEnvironment = (envId) => {
    const environments = tripData.preferred_environment || [];
    if (environments.includes(envId)) {
      updateTripData({ preferred_environment: environments.filter(id => id !== envId) });
    } else {
      updateTripData({ preferred_environment: [...environments, envId] });
    }
  };

  const toggleAmenity = (amenityId) => {
    const amenities = tripData.preferred_amenities || [];
    if (amenities.includes(amenityId)) {
      updateTripData({ preferred_amenities: amenities.filter(id => id !== amenityId) });
    } else {
      updateTripData({ preferred_amenities: [...amenities, amenityId] });
    }
  };

  const handleContinue = () => {
    onNext();
  };

  return (
    <div className="step3-container">
      <div className="step3-content">
        <div className="step3-header">
          <h2>Tell us what you love</h2>
          <p className="section-subtitle">
            Help us personalize your trip by selecting your interests and preferences
          </p>
        </div>

        <div className="preferences-sections">
          {/* Interests Section */}
          <section className="preference-section">
            <h3>What are your interests?</h3>
            <p className="section-hint">Select all that apply - the more we know, the better!</p>
            <div className="chip-grid">
              {INTERESTS.map(interest => (
                <button
                  key={interest.id}
                  className={`chip ${tripData.interests?.includes(interest.id) ? 'selected' : ''}`}
                  onClick={() => toggleInterest(interest.id)}
                >
                  <span className="chip-icon">{interest.icon}</span>
                  <span className="chip-label">{interest.label}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Environment Preferences */}
          <section className="preference-section">
            <h3>Preferred environments</h3>
            <p className="section-hint">Where do you feel most at home?</p>
            <div className="chip-grid">
              {ENVIRONMENTS.map(env => (
                <button
                  key={env.id}
                  className={`chip ${tripData.preferred_environment?.includes(env.id) ? 'selected' : ''}`}
                  onClick={() => toggleEnvironment(env.id)}
                >
                  <span className="chip-icon">{env.icon}</span>
                  <span className="chip-label">{env.label}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Amenities (for multi-day trips) */}
          {isMultiDay && (
            <section className="preference-section">
              <h3>Essential amenities</h3>
              <p className="section-hint">What facilities are important to you?</p>
              <div className="chip-grid">
                {AMENITIES.map(amenity => (
                  <button
                    key={amenity.id}
                    className={`chip ${tripData.preferred_amenities?.includes(amenity.id) ? 'selected' : ''}`}
                    onClick={() => toggleAmenity(amenity.id)}
                  >
                    <span className="chip-icon">{amenity.icon}</span>
                    <span className="chip-label">{amenity.label}</span>
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* Budget Section */}
          <section className="preference-section">
            <h3>Budget</h3>
            <p className="section-hint">
              {isMultiDay ? 'What\'s your budget per night?' : 'How much are you willing to spend per visit?'}
            </p>

            <div className="budget-controls">
              <div className="price-range">
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={tripData.max_price_per_night || 50}
                  onChange={(e) => updateTripData({ max_price_per_night: parseInt(e.target.value) })}
                  className="slider"
                />
                <div className="price-display">
                  <span className="price-label">Up to:</span>
                  <span className="price-value">€{tripData.max_price_per_night || 50}</span>
                  <span className="price-unit">{isMultiDay ? 'per night' : 'per visit'}</span>
                </div>
              </div>

              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={tripData.max_price_per_night === 0}
                  onChange={(e) => {
                    if (e.target.checked) {
                      updateTripData({ max_price_per_night: 0 });
                    } else {
                      updateTripData({ max_price_per_night: 50 });
                    }
                  }}
                />
                <span>Show only free locations</span>
              </label>
            </div>
          </section>

          {/* Additional Preferences */}
          <section className="preference-section">
            <h3>Additional preferences</h3>

            <div className="additional-options">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={tripData.avoid_crowded || false}
                  onChange={(e) => updateTripData({ avoid_crowded: e.target.checked })}
                />
                <div className="option-content">
                  <span className="option-title">Avoid crowded places</span>
                  <span className="option-description">Prefer quieter, less touristy spots</span>
                </div>
              </label>

              <div className="activity-level-section">
                <label className="section-label">Activity level</label>
                <div className="activity-level-options">
                  {ACTIVITY_LEVELS.map(level => (
                    <button
                      key={level.id}
                      className={`activity-level-btn ${(tripData.activity_level || 'moderate') === level.id ? 'selected' : ''}`}
                      onClick={() => updateTripData({ activity_level: level.id })}
                    >
                      <span className="level-label">{level.label}</span>
                      <span className="level-description">{level.description}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Summary */}
          <div className="preferences-summary">
            <div className="summary-item">
              <span className="summary-icon">✨</span>
              <span className="summary-text">
                {tripData.interests?.length || 0} interests selected
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-icon">🌍</span>
              <span className="summary-text">
                {tripData.preferred_environment?.length || 0} environments chosen
              </span>
            </div>
            {isMultiDay && (
              <div className="summary-item">
                <span className="summary-icon">🏕️</span>
                <span className="summary-text">
                  {tripData.preferred_amenities?.length || 0} amenities selected
                </span>
              </div>
            )}
          </div>

          {/* Continue Button */}
          <div className="step3-actions">
            <button className="btn btn-outline" onClick={onBack}>
              ← Back
            </button>
            <button
              className="btn btn-primary"
              onClick={handleContinue}
              disabled={(tripData.interests?.length || 0) === 0}
            >
              Continue to Recommendations →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Step3_Preferences;
