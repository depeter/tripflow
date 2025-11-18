import React, { useState } from 'react';
import './EventCard.css';

/**
 * EventCard Component
 * Displays event information in a card format for the discovery bottom sheet
 */
const EventCard = ({ event, onFavoriteToggle, isFavorited, onClick }) => {
  const [imageError, setImageError] = useState(false);

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const options = {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
  };

  // Format date range
  const formatDateRange = () => {
    if (!event.start_datetime) return '';

    const start = formatDate(event.start_datetime);

    if (event.end_datetime && event.end_datetime !== event.start_datetime) {
      const end = formatDate(event.end_datetime);
      return `${start} - ${end}`;
    }

    return start;
  };

  // Get category color
  const getCategoryColor = (category) => {
    const colors = {
      festival: '#FF6B6B',
      concert: '#4ECDC4',
      sports: '#45B7D1',
      market: '#FFA07A',
      exhibition: '#98D8C8',
      theater: '#C77DFF',
      cultural: '#FF9F1C',
      food: '#E63946',
      outdoor: '#06D6A0',
      other: '#95A5A6'
    };
    return colors[category] || colors.other;
  };

  // Get category icon
  const getCategoryIcon = (category) => {
    const icons = {
      festival: '🎪',
      concert: '🎵',
      sports: '⚽',
      market: '🏪',
      exhibition: '🖼️',
      theater: '🎭',
      cultural: '🏛️',
      food: '🍴',
      outdoor: '🌳',
      other: '📍'
    };
    return icons[category] || icons.other;
  };

  const primaryImage = event.images && event.images.length > 0 && !imageError
    ? event.images[0]
    : null;

  return (
    <div className="event-card" onClick={onClick}>
      <div className="event-card-header">
        {primaryImage ? (
          <img
            src={primaryImage}
            alt={event.name}
            className="event-card-image"
            onError={() => setImageError(true)}
          />
        ) : (
          <div
            className="event-card-placeholder"
            style={{ backgroundColor: getCategoryColor(event.category) }}
          >
            <span className="event-card-icon">{getCategoryIcon(event.category)}</span>
          </div>
        )}

        <button
          className={`event-card-favorite ${isFavorited ? 'favorited' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            onFavoriteToggle(event.id);
          }}
          aria-label={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
        >
          {isFavorited ? '❤️' : '🤍'}
        </button>
      </div>

      <div className="event-card-body">
        <div className="event-card-category">
          <span
            className="category-badge"
            style={{ backgroundColor: getCategoryColor(event.category) }}
          >
            {event.category}
          </span>
          {event.distance_km !== null && event.distance_km !== undefined && (
            <span className="event-distance">
              📍 {event.distance_km.toFixed(1)} km away
            </span>
          )}
        </div>

        <h3 className="event-card-title">{event.name}</h3>

        {event.venue_name && (
          <div className="event-venue">
            <span className="venue-icon">📍</span>
            {event.venue_name}
          </div>
        )}

        <div className="event-datetime">
          <span className="datetime-icon">📅</span>
          {formatDateRange()}
        </div>

        {event.description && (
          <p className="event-description">
            {event.description.length > 120
              ? `${event.description.substring(0, 120)}...`
              : event.description}
          </p>
        )}

        <div className="event-card-footer">
          <div className="event-price">
            {event.free ? (
              <span className="price-free">FREE</span>
            ) : event.price ? (
              <span className="price-paid">
                {event.currency} {event.price.toFixed(2)}
              </span>
            ) : (
              <span className="price-unknown">Price TBD</span>
            )}
          </div>

          {event.tags && event.tags.length > 0 && (
            <div className="event-tags">
              {event.tags.slice(0, 3).map((tag, index) => (
                <span key={index} className="event-tag">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventCard;
