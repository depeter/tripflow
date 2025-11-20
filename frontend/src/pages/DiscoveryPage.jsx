import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import BottomSheet from '../components/BottomSheet';
import EventCard from '../components/EventCard';
import LoadingSpinner from '../components/LoadingSpinner';
import FilterSidebar from '../components/FilterSidebar';
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

// Create custom event marker icon with category color and SVG icon
const createEventIcon = (category) => {
  // Normalize category to lowercase for icon lookup
  const categoryKey = category ? category.toLowerCase() : 'other';

  const iconConfig = {
    festival: {
      color: '#FF6B6B',
      icon: '<path d="M12 2l2 7h7l-6 4 2 7-5-4-5 4 2-7-6-4h7z"/>'
    },
    concert: {
      color: '#4ECDC4',
      icon: '<path d="M12 3v10.5c-.6-.3-1.3-.5-2-.5-2.2 0-4 1.8-4 4s1.8 4 4 4 4-1.8 4-4V7h4V3h-6z"/>'
    },
    sports: {
      color: '#45B7D1',
      icon: '<circle cx="12" cy="12" r="10" fill="none" stroke="white" stroke-width="2"/><path d="M12 2v20M2 12h20M6 4l12 16M18 4L6 20"/>'
    },
    market: {
      color: '#FFA07A',
      icon: '<path d="M4 4h16l-2 4H6L4 4zm0 0v14c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8"/><path d="M8 8v4m4-4v4m4-4v4"/>'
    },
    exhibition: {
      color: '#98D8C8',
      icon: '<rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="white" stroke-width="2"/><path d="M9 9h6m-6 3h6m-6 3h3"/>'
    },
    theater: {
      color: '#C77DFF',
      icon: '<path d="M12 2C7 2 3 6 3 11v8c0 1.1.9 2 2 2h2v-6c0-2.2 1.8-4 4-4h2c2.2 0 4 1.8 4 4v6h2c1.1 0 2-.9 2-2v-8c0-5-4-9-9-9z"/><circle cx="9" cy="8" r="1.5"/><circle cx="15" cy="8" r="1.5"/><path d="M8 13c0-2.2 1.8-4 4-4s4 1.8 4 4"/>'
    },
    cultural: {
      color: '#FF9F1C',
      icon: '<path d="M4 4h16v16H4z" fill="none" stroke="white" stroke-width="2"/><path d="M8 4v16m8-16v16M4 8h16m-16 8h16"/>'
    },
    food: {
      color: '#E63946',
      icon: '<path d="M8 2v8c0 1.1-.9 2-2 2s-2-.9-2-2V2m4 0v8c0 1.1.9 2 2 2s2-.9 2-2V2M6 12v8m6-18v8l4 4v8h-4"/>'
    },
    outdoor: {
      color: '#06D6A0',
      icon: '<path d="M12 2L4 8v4l8 6 8-6V8z"/><path d="M4 12l8 6 8-6"/><path d="M12 14v8"/>'
    },
    camping: {
      color: '#2ECC71',
      icon: '<path d="M12 2L4 8v4l8 6 8-6V8z"/><path d="M4 12l8 6 8-6"/><path d="M12 14v8"/>'
    },
    parking: {
      color: '#3498DB',
      icon: '<circle cx="12" cy="12" r="10" fill="none" stroke="white" stroke-width="2"/><path d="M8 6h4c2.2 0 4 1.8 4 4s-1.8 4-4 4H8V6zm0 0v12"/>'
    },
    other: {
      color: '#95A5A6',
      icon: '<circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 10v6M23 12h-6M7 12H1m17.7-7.7l-4.2 4.2M7.5 16.5l-4.2 4.2m14.4 0l-4.2-4.2M7.5 7.5L3.3 3.3"/>'
    }
  };

  const config = iconConfig[categoryKey] || iconConfig.other;

  const svgIcon = `
    <svg width="40" height="50" viewBox="0 0 40 50" xmlns="http://www.w3.org/2000/svg">
      <!-- Shadow -->
      <ellipse cx="20" cy="47" rx="8" ry="3" fill="rgba(0,0,0,0.2)"/>

      <!-- Pin background -->
      <path d="M20 0 C10 0, 2 8, 2 18 C2 28, 20 45, 20 45 C20 45, 38 28, 38 18 C38 8, 30 0, 20 0 Z"
            fill="${config.color}"
            stroke="white"
            stroke-width="2"/>

      <!-- Icon -->
      <g transform="translate(8, 6)" fill="white" stroke="white" stroke-width="0.5">
        ${config.icon}
      </g>
    </svg>
  `;

  return L.divIcon({
    className: 'custom-event-marker',
    html: svgIcon,
    iconSize: [40, 50],
    iconAnchor: [20, 50],
    popupAnchor: [0, -50]
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
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(false);

  // Filter state
  const [filters, setFilters] = useState({
    showEvents: true,
    showLocations: true,
    selectedCategories: [],
    selectedEventTypes: [],
    searchText: '',
    radiusKm: 25,
    freeOnly: false
  });
  const [filterSidebarOpen, setFilterSidebarOpen] = useState(true); // Open by default on desktop

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

  // Search for events and locations
  const searchEvents = useCallback(async () => {
    // Use the current visible map center, or fall back to user location, or default
    const searchLocation = currentMapCenter || userLocation || {
      lat: defaultCenter[0],
      lng: defaultCenter[1]
    };

    setLoading(true);

    try {
      // Build item_types array based on filters
      const item_types = [];
      if (filters.showEvents) item_types.push('events');
      if (filters.showLocations) item_types.push('locations');

      const response = await discoveryService.searchEvents({
        latitude: searchLocation.lat,
        longitude: searchLocation.lng,
        radius_km: filters.radiusKm,
        item_types: item_types.length > 0 ? item_types : ['events', 'locations'],
        categories: filters.selectedCategories.length > 0 ? filters.selectedCategories : null,
        event_types: filters.selectedEventTypes.length > 0 ? filters.selectedEventTypes : null,
        search_text: filters.searchText.trim() || null,
        free_only: filters.freeOnly,
        limit: 200
      });

      setEvents(response.events || []);
      setLocations(response.locations || []);
      setSheetOpen(true);
    } catch (error) {
      console.error('Error searching:', error);
      setEvents([]);
      setLocations([]);
    } finally {
      setLoading(false);
    }
  }, [currentMapCenter, userLocation, filters, defaultCenter]);

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

  // Auto-search when filters change
  useEffect(() => {
    if (currentMapCenter || userLocation) {
      searchEvents();
    }
  }, [filters]); // Trigger search whenever filters change

  return (
    <div className="discovery-page">
      {/* Filter Sidebar */}
      <FilterSidebar
        filters={filters}
        onFilterChange={setFilters}
        isOpen={filterSidebarOpen}
        onToggle={() => setFilterSidebarOpen(!filterSidebarOpen)}
        eventsCount={events.length + locations.length}
        loading={loading}
      />

      {/* Map Container */}
      <div className={`discovery-map ${filterSidebarOpen ? 'with-sidebar' : ''}`}>
        {/* Center marker to show search location */}
        <div className="map-center-marker">
          <div className="map-center-crosshair">
            <div className="map-center-dot"></div>
          </div>
        </div>

        {/* Location permission banner */}
        {locationError && (
          <div className="location-error-banner">
            ⚠️ {locationError}
            {locationPermission !== 'granted' && (
              <button className="location-retry-btn" onClick={requestLocation}>
                Try Again
              </button>
            )}
          </div>
        )}

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
              key={`event-${event.id}`}
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

          {/* Location markers (places like camping/parking) */}
          {locations.map((location) => (
            <Marker
              key={`location-${location.id}`}
              position={[location.latitude, location.longitude]}
              icon={createEventIcon(location.category || location.location_type)}
              eventHandlers={{
                click: () => setSelectedEvent(location)
              }}
            >
              <Popup>
                <div className="event-popup">
                  <strong>{location.name}</strong>
                  <br />
                  {location.address && <>{location.address}<br /></>}
                  <span className="event-popup-category">
                    {location.category || location.location_type || 'Place'}
                  </span>
                  {location.distance_km && (
                    <><br />{location.distance_km.toFixed(1)} km away</>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="discovery-loading">
          <LoadingSpinner />
        </div>
      )}

      {/* Bottom Sheet with Events and Locations */}
      <BottomSheet isOpen={sheetOpen} onClose={() => setSheetOpen(false)}>
        <div className="events-list">
          <h2 className="events-list-title">
            {events.length + locations.length} Results Found
            {events.length > 0 && locations.length > 0 && (
              <span style={{ fontSize: '0.8em', fontWeight: 'normal', marginLeft: '8px' }}>
                ({events.length} events, {locations.length} places)
              </span>
            )}
          </h2>

          {events.length === 0 && locations.length === 0 && !loading && (
            <div className="no-events">
              <p>No results found in this area.</p>
              <p>Try increasing the search radius or changing filters.</p>
            </div>
          )}

          {events.map((event) => (
            <EventCard
              key={`event-${event.id}`}
              event={event}
              isFavorited={favoriteIds.has(event.id)}
              onFavoriteToggle={handleFavoriteToggle}
              onClick={() => setSelectedEvent(event)}
            />
          ))}

          {locations.map((location) => (
            <EventCard
              key={`location-${location.id}`}
              event={location}
              isFavorited={favoriteIds.has(location.id)}
              onFavoriteToggle={handleFavoriteToggle}
              onClick={() => setSelectedEvent(location)}
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
