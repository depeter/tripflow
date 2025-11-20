import React from 'react';
import EventCard from './EventCard';
import './ResultsPanel.css';

const ResultsPanel = ({
  events,
  locations,
  loading,
  favoriteIds,
  onFavoriteToggle,
  onEventClick,
  onEventHover,
  selectedEventId,
  isOpen,
  onToggle
}) => {
  const totalResults = events.length + locations.length;

  return (
    <div className={`results-panel ${isOpen ? 'open' : 'closed'}`}>
      {/* Toggle button for mobile */}
      <button className="results-panel-toggle" onClick={onToggle}>
        {isOpen ? '→' : '←'}
      </button>

      {/* Panel content */}
      <div className="results-panel-content">
        <div className="results-panel-header">
          <div className="results-header-content">
            <h2 className="results-count">
              {totalResults} Result{totalResults !== 1 ? 's' : ''} Found
            </h2>
            {events.length > 0 && locations.length > 0 && (
              <p className="results-breakdown">
                {events.length} event{events.length !== 1 ? 's' : ''}, {locations.length} place{locations.length !== 1 ? 's' : ''}
              </p>
            )}
          </div>
          <button className="results-close-btn" onClick={onToggle} aria-label="Close results">
            ✕
          </button>
        </div>

        {/* No results message */}
        {totalResults === 0 && !loading && (
          <div className="no-results">
            <div className="no-results-icon">📍</div>
            <p className="no-results-title">No results found</p>
            <p className="no-results-text">
              Try increasing the search radius or changing your filters.
            </p>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="results-loading">
            <div className="loading-spinner"></div>
            <p>Searching for events and places...</p>
          </div>
        )}

        {/* Results list */}
        <div className="results-list">
          {events.map((event) => (
            <div
              key={`event-${event.id}`}
              className={`result-item ${selectedEventId === event.id ? 'selected' : ''}`}
              onMouseEnter={() => onEventHover && onEventHover(event)}
              onMouseLeave={() => onEventHover && onEventHover(null)}
            >
              <EventCard
                event={event}
                isFavorited={favoriteIds.has(event.id)}
                onFavoriteToggle={onFavoriteToggle}
                onClick={() => onEventClick(event)}
              />
            </div>
          ))}

          {locations.map((location) => (
            <div
              key={`location-${location.id}`}
              className={`result-item ${selectedEventId === location.id ? 'selected' : ''}`}
              onMouseEnter={() => onEventHover && onEventHover(location)}
              onMouseLeave={() => onEventHover && onEventHover(null)}
            >
              <EventCard
                event={location}
                isFavorited={favoriteIds.has(location.id)}
                onFavoriteToggle={onFavoriteToggle}
                onClick={() => onEventClick(location)}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ResultsPanel;
