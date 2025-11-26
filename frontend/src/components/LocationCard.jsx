import React from 'react';
import './LocationCard.css';
import SafeHtml from './SafeHtml';

const LocationCard = ({ location, onAddToTrip, onViewDetails, isSelected = false }) => {
  const { name, type, rating, price_per_night, distance_from_start, match_score, tags, image_url, description } = location;

  const handleAddClick = (e) => {
    e.stopPropagation();
    onAddToTrip(location);
  };

  const handleViewClick = (e) => {
    e.stopPropagation();
    if (onViewDetails) {
      onViewDetails(location);
    }
  };

  return (
    <div className={`location-card ${isSelected ? 'selected' : ''}`}>
      {/* Image */}
      <div className="card-image">
        {image_url ? (
          <img src={image_url} alt={name} />
        ) : (
          <div className="placeholder-image">
            <span className="placeholder-icon">{getTypeIcon(type)}</span>
          </div>
        )}
        <div className="match-badge">
          <span className="match-score">{match_score}%</span>
          <span className="match-label">match</span>
        </div>
      </div>

      {/* Content */}
      <div className="card-content">
        <div className="card-header">
          <h3 className="location-name">{name}</h3>
          <div className="rating">
            <span className="star">⭐</span>
            <span className="rating-value">{rating.toFixed(1)}</span>
          </div>
        </div>

        <div className="location-meta">
          <span className="meta-item">
            <span className="meta-icon">📍</span>
            {type}
          </span>
          {distance_from_start && (
            <span className="meta-item">
              <span className="meta-icon">🚗</span>
              {distance_from_start}km
            </span>
          )}
          {price_per_night !== undefined && (
            <span className="meta-item">
              <span className="meta-icon">💰</span>
              {price_per_night === 0 ? 'Free' : `€${price_per_night}/night`}
            </span>
          )}
        </div>

        {tags && tags.length > 0 && (
          <div className="location-tags">
            {tags.slice(0, 3).map((tag, idx) => (
              <span key={idx} className="tag">{tag}</span>
            ))}
            {tags.length > 3 && (
              <span className="tag-more">+{tags.length - 3}</span>
            )}
          </div>
        )}

        {description && (
          <SafeHtml html={description} className="location-description" />
        )}

        <div className="card-actions">
          <button
            className={`btn btn-sm ${isSelected ? 'btn-secondary' : 'btn-primary'}`}
            onClick={handleAddClick}
          >
            {isSelected ? '✓ Added' : '+ Add to trip'}
          </button>
          <button className="btn btn-sm btn-outline" onClick={handleViewClick}>
            👁️ Details
          </button>
        </div>
      </div>
    </div>
  );
};

const getTypeIcon = (type) => {
  const icons = {
    campsite: '🏕️',
    parking: '🅿️',
    attraction: '🎭',
    restaurant: '🍽️',
    museum: '🏛️',
    nature: '🌲',
    beach: '🏖️',
    city: '🏙️',
    default: '📍'
  };
  return icons[type] || icons.default;
};

export default LocationCard;
