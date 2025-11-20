import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import BottomSheet from '../components/BottomSheet';
import EventCard from '../components/EventCard';
import LoadingSpinner from '../components/LoadingSpinner';
import discoveryService from '../services/discoveryService';
import { useAuth } from '../context/AuthContext';
import './DiscoveryPage.css';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Create custom event marker icon with category color
const createEventIcon = (category) => {
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

  const color = colors[category] || colors.other;

  return L.divIcon({
    className: 'event-marker',
    html: `<div class="marker-pin" style="background-color: ${color}"></div>`,
    iconSize: [24, 32],
    iconAnchor: [12, 32],
    popupAnchor: [0, -32]
  });
};

// Component to recenter map when location changes
const MapRecenter = ({ center }) => {
  const map = useMap();

  useEffect(() => {
    if (center) {
      map.setView(center, map.getZoom());
    }
  }, [center, map]);

  return null;
};

// Component to track map center when user moves the map
const MapCenterTracker = ({ onCenterChange }) => {
  const map = useMap();

  useEffect(() => {
    const handleMoveEnd = () => {
      const center = map.getCenter();
      onCenterChange({ lat: center.lat, lng: center.lng });
    };

    // Track initial center
    handleMoveEnd();

    // Listen for map movement
    map.on('moveend', handleMoveEnd);

    return () => {
      map.off('moveend', handleMoveEnd);
    };
  }, [map, onCenterChange]);

  return null;
};

const DiscoveryPage = () => {
  const { user } = useAuth();

  // Location state
  const [userLocation, setUserLocation] = useState(null);
  const [locationPermission, setLocationPermission] = useState('prompt'); // 'prompt', 'granted', 'denied'
  const [locationError, setLocationError] = useState(null);

  // Discovery state
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchRadius, setSearchRadius] = useState(25); // km
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [freeOnly, setFreeOnly] = useState(false);

  // UI state
  const [sheetOpen, setSheetOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [favoriteIds, setFavoriteIds] = useState(new Set());

  // Map state
  const defaultCenter = [51.0543, 3.7174]; // Ghent, Belgium
  const [mapCenter, setMapCenter] = useState(defaultCenter);
  const [currentMapCenter, setCurrentMapCenter] = useState(null); // Track the current visible map center

  // Handle map center changes when user moves the map
  const handleMapCenterChange = useCallback((center) => {
    setCurrentMapCenter(center);
  }, []);

  // Request location permission
  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser');
      setLocationPermission('denied');
      return;
    }

    setLocationPermission('prompt');
    setLocationError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        setUserLocation(location);
        setMapCenter([location.lat, location.lng]);
        setLocationPermission('granted');
        setLocationError(null);
      },
      (error) => {
        console.error('Geolocation error:', error);
        setLocationPermission('denied');

        switch (error.code) {
          case error.PERMISSION_DENIED:
            setLocationError('Location permission denied. Please enable location access in your browser settings.');
            break;
          case error.POSITION_UNAVAILABLE:
            setLocationError('Location information unavailable');
            break;
          case error.TIMEOUT:
            setLocationError('Location request timed out');
            break;
          default:
            setLocationError('An unknown error occurred');
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    );
  }, []);

  // Search for events
  const searchEvents = useCallback(async () => {
    // Use the current visible map center, or fall back to user location, or default
    const searchLocation = currentMapCenter || userLocation || {
      lat: defaultCenter[0],
      lng: defaultCenter[1]
    };

    setLoading(true);

    try {
      const response = await discoveryService.searchEvents({
        latitude: searchLocation.lat,
        longitude: searchLocation.lng,
        radius_km: searchRadius,
        categories: selectedCategories.length > 0 ? selectedCategories : null,
        free_only: freeOnly,
        limit: 100
      });

      setEvents(response.events || []);
      setSheetOpen(true);
    } catch (error) {
      console.error('Error searching events:', error);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [currentMapCenter, userLocation, searchRadius, selectedCategories, freeOnly, defaultCenter]);

  // Load favorite IDs
  const loadFavorites = useCallback(async () => {
    if (!user) return;

    try {
      const ids = await discoveryService.getFavoriteIds();
      setFavoriteIds(new Set(ids));
    } catch (error) {
      console.error('Error loading favorites:', error);
    }
  }, [user]);

  // Toggle favorite
  const handleFavoriteToggle = async (eventId) => {
    if (!user) {
      alert('Please sign in to save favorites');
      return;
    }

    try {
      if (favoriteIds.has(eventId)) {
        await discoveryService.removeFavorite(eventId);
        setFavoriteIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(eventId);
          return newSet;
        });
      } else {
        await discoveryService.addFavorite(eventId);
        setFavoriteIds(prev => new Set([...prev, eventId]));
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      alert('Failed to update favorite. Please try again.');
    }
  };

  // Initial location request
  useEffect(() => {
    requestLocation();
  }, [requestLocation]);

  // Load favorites when user logs in
  useEffect(() => {
    if (user) {
      loadFavorites();
    } else {
      setFavoriteIds(new Set());
    }
  }, [user, loadFavorites]);

  // Auto-search when location is granted
  useEffect(() => {
    if (locationPermission === 'granted' && userLocation) {
      searchEvents();
    }
  }, [locationPermission, userLocation]); // Don't include searchEvents to avoid loop

  return (
    <div className="discovery-page">
      {/* Map Container */}
      <div className="discovery-map">
        {/* Center marker to show search location */}
        <div className="map-center-marker">
          <div className="map-center-crosshair">
            <div className="map-center-dot"></div>
          </div>
        </div>

        <MapContainer
          center={mapCenter}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapRecenter center={mapCenter} />
          <MapCenterTracker onCenterChange={handleMapCenterChange} />

          {/* User location marker */}
          {userLocation && (
            <Marker position={[userLocation.lat, userLocation.lng]}>
              <Popup>
                <strong>Your Location</strong>
              </Popup>
            </Marker>
          )}

          {/* Event markers */}
          {events.map((event) => (
            <Marker
              key={event.id}
              position={[event.latitude, event.longitude]}
              icon={createEventIcon(event.category)}
              eventHandlers={{
                click: () => setSelectedEvent(event)
              }}
            >
              <Popup>
                <div className="event-popup">
                  <strong>{event.name}</strong>
                  <br />
                  {event.venue_name && <>{event.venue_name}<br /></>}
                  <span className="event-popup-category">{event.category}</span>
                  {event.distance_km && (
                    <><br />{event.distance_km.toFixed(1)} km away</>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Control Panel */}
      <div className="discovery-controls">
        <div className="controls-header">
          <h2>🔍 Discover Events</h2>

          {locationPermission !== 'granted' && (
            <button className="location-btn" onClick={requestLocation}>
              📍 Enable Location
            </button>
          )}
        </div>

        <div className="controls-filters">
          <div className="filter-group">
            <label>Radius:</label>
            <select
              value={searchRadius}
              onChange={(e) => setSearchRadius(Number(e.target.value))}
            >
              <option value={10}>10 km</option>
              <option value={25}>25 km</option>
              <option value={50}>50 km</option>
              <option value={100}>100 km</option>
            </select>
          </div>

          <div className="filter-group">
            <label>
              <input
                type="checkbox"
                checked={freeOnly}
                onChange={(e) => setFreeOnly(e.target.checked)}
              />
              Free events only
            </label>
          </div>

          <button
            className="search-btn"
            onClick={searchEvents}
            disabled={loading}
          >
            {loading ? 'Searching...' : '🔎 Search'}
          </button>
        </div>

        {locationError && (
          <div className="location-error">
            ⚠️ {locationError}
          </div>
        )}

        {events.length > 0 && (
          <div className="events-summary">
            Found {events.length} events nearby
          </div>
        )}
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="discovery-loading">
          <LoadingSpinner />
        </div>
      )}

      {/* Bottom Sheet with Events */}
      <BottomSheet isOpen={sheetOpen} onClose={() => setSheetOpen(false)}>
        <div className="events-list">
          <h2 className="events-list-title">
            {events.length} Events Found
          </h2>

          {events.length === 0 && !loading && (
            <div className="no-events">
              <p>No events found in this area.</p>
              <p>Try increasing the search radius or changing filters.</p>
            </div>
          )}

          {events.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              isFavorited={favoriteIds.has(event.id)}
              onFavoriteToggle={handleFavoriteToggle}
              onClick={() => setSelectedEvent(event)}
            />
          ))}
        </div>
      </BottomSheet>

      {/* Event Detail Modal (optional - can be implemented later) */}
      {selectedEvent && (
        <div className="event-detail-overlay" onClick={() => setSelectedEvent(null)}>
          <div className="event-detail-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedEvent(null)}>
              ✕
            </button>
            <EventCard
              event={selectedEvent}
              isFavorited={favoriteIds.has(selectedEvent.id)}
              onFavoriteToggle={handleFavoriteToggle}
              onClick={() => {}}
            />
            {selectedEvent.website && (
              <a
                href={selectedEvent.website}
                target="_blank"
                rel="noopener noreferrer"
                className="event-website-btn"
              >
                Visit Website
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DiscoveryPage;
