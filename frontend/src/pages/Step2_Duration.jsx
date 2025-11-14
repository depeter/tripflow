import React, { useState, useEffect, useCallback } from 'react';
import { useTripContext } from '../context/TripContext';
import MapView from '../components/MapView';
import LoadingSpinner from '../components/LoadingSpinner';
import { geocodeAddress, calculateRoute, calculateFeasibility, debounce } from '../services/geocodingService';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import './Step2_Duration.css';

const Step2_Duration = ({ onNext, onBack }) => {
  const { tripData, updateTripData, addWaypoint, removeWaypoint, reorderWaypoints, updateRouteStats } = useTripContext();

  // Local state
  const [startSearchResults, setStartSearchResults] = useState([]);
  const [endSearchResults, setEndSearchResults] = useState([]);
  const [waypointSearch, setWaypointSearch] = useState('');
  const [waypointSearchResults, setWaypointSearchResults] = useState([]);
  const [isCalculatingRoute, setIsCalculatingRoute] = useState(false);
  const [routeGeometry, setRouteGeometry] = useState([]);

  const isMultiDay = tripData.trip_type === 'multi_day';

  // Debounced geocoding functions
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const searchStart = useCallback(
    debounce(async (query) => {
      if (query.length < 3) {
        setStartSearchResults([]);
        return;
      }
      const results = await geocodeAddress(query);
      setStartSearchResults(results);
    }, 300),
    []
  );

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const searchEnd = useCallback(
    debounce(async (query) => {
      if (query.length < 3) {
        setEndSearchResults([]);
        return;
      }
      const results = await geocodeAddress(query);
      setEndSearchResults(results);
    }, 300),
    []
  );

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const searchWaypoint = useCallback(
    debounce(async (query) => {
      if (query.length < 3) {
        setWaypointSearchResults([]);
        return;
      }
      const results = await geocodeAddress(query);
      setWaypointSearchResults(results);
    }, 300),
    []
  );

  // Calculate route when coordinates change (with debounce to avoid rapid requests)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      calculateFullRoute();
    }, 500); // Wait 500ms after last change before recalculating

    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    tripData.start_coordinates,
    tripData.start_address,
    tripData.end_coordinates,
    tripData.waypoints,
    tripData.planning_mode,
    tripData.is_round_trip,
    tripData.duration_days,
    tripData.duration_hours,
    isMultiDay
  ]);

  const calculateFullRoute = async () => {
      // Build coordinate list
      const coords = [];

      // Only proceed if we have a valid start location set by the user
      if (tripData.start_coordinates && tripData.start_address && tripData.start_address.trim().length > 0) {
        coords.push([tripData.start_coordinates.lat, tripData.start_coordinates.lng]);
      } else {
        // No valid start location yet, reset route display
        setRouteGeometry([]);
        updateRouteStats({
          total_distance_km: 0,
          estimated_driving_hours: 0,
          feasibility_status: 'comfortable'
        });
        return;
      }

      tripData.waypoints.forEach(wp => {
        if (wp.coordinates) {
          coords.push([wp.coordinates.lat, wp.coordinates.lng]);
        }
      });

      if (tripData.planning_mode === 'destination' && tripData.end_coordinates) {
        coords.push([tripData.end_coordinates.lat, tripData.end_coordinates.lng]);
      }

      if (tripData.is_round_trip && tripData.start_coordinates) {
        coords.push([tripData.start_coordinates.lat, tripData.start_coordinates.lng]);
      }

      if (coords.length >= 2) {
        setIsCalculatingRoute(true);
        const route = await calculateRoute(coords);

        if (route) {
          setRouteGeometry(route.geometry);

          const totalDistanceKm = route.distance / 1000;
          const estimatedDrivingHours = route.duration / 3600;
          const feasibility = calculateFeasibility(
            totalDistanceKm,
            tripData.duration_days,
            tripData.duration_hours,
            isMultiDay
          );

          updateRouteStats({
            total_distance_km: Math.round(totalDistanceKm),
            estimated_driving_hours: Math.round(estimatedDrivingHours * 10) / 10,
            feasibility_status: feasibility
          });
        }

        setIsCalculatingRoute(false);
      } else {
        setRouteGeometry([]);
        updateRouteStats({
          total_distance_km: 0,
          estimated_driving_hours: 0,
          feasibility_status: 'comfortable'
        });
      }
  };

  // Build map markers
  const buildMapMarkers = () => {
    const markers = [];

    if (tripData.start_coordinates) {
      markers.push({
        id: 'start',
        position: [tripData.start_coordinates.lat, tripData.start_coordinates.lng],
        popup: `Start: ${tripData.start_address}`,
        numbered: false
      });
    }

    tripData.waypoints.forEach((wp, idx) => {
      if (wp.coordinates) {
        markers.push({
          id: `waypoint-${idx}`,
          position: [wp.coordinates.lat, wp.coordinates.lng],
          popup: wp.name,
          numbered: true,
          number: idx + 1,
          draggable: true
        });
      }
    });

    if (tripData.planning_mode === 'destination' && tripData.end_coordinates) {
      markers.push({
        id: 'end',
        position: [tripData.end_coordinates.lat, tripData.end_coordinates.lng],
        popup: `End: ${tripData.end_address}`,
        numbered: false
      });
    }

    return markers;
  };

  const handleAddWaypoint = (location) => {
    addWaypoint({
      name: location.name,
      type: location.type,
      coordinates: location.coordinates,
      order: tripData.waypoints.length
    });
    setWaypointSearch('');
    setWaypointSearchResults([]);
  };

  const handleDragEnd = (result) => {
    if (!result.destination) return;

    const items = Array.from(tripData.waypoints);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    reorderWaypoints(items);
  };

  const getFeasibilityMessage = () => {
    const { feasibility_status, total_distance_km } = tripData.route_stats;

    if (feasibility_status === 'comfortable') {
      return { text: '✅ Comfortable pace - plenty of time for exploration', color: 'success' };
    } else if (feasibility_status === 'tight') {
      return { text: `⚠️ Tight schedule - ${total_distance_km}km in ${isMultiDay ? tripData.duration_days + ' days' : tripData.duration_hours + ' hours'}`, color: 'warning' };
    } else {
      return { text: `❌ Too ambitious - consider adding ${isMultiDay ? 'more days' : 'more time'} or reducing waypoints`, color: 'error' };
    }
  };

  const markers = buildMapMarkers();
  const mapCenter = tripData.start_coordinates
    ? [tripData.start_coordinates.lat, tripData.start_coordinates.lng]
    : [51.505, -0.09];

  const mapCircle = tripData.planning_mode === 'explore' && tripData.start_coordinates
    ? {
        center: [tripData.start_coordinates.lat, tripData.start_coordinates.lng],
        radius: tripData.max_distance_km * 1000
      }
    : null;

  const feasibility = getFeasibilityMessage();

  return (
    <div className="step2-container">
      <div className="split-screen">
        {/* Left Panel - Form Inputs */}
        <div className="left-panel">
          <div className="panel-content">
            <h2>Plan Your Route</h2>
            <p className="section-subtitle">Define your journey's starting point and duration</p>

            {/* Starting Location */}
            <div className="form-group">
              <label>Where are you starting?</label>
              <input
                type="text"
                placeholder="Enter city, address, or landmark"
                value={tripData.start_address}
                onChange={(e) => {
                  updateTripData({ start_address: e.target.value });
                  searchStart(e.target.value);
                }}
                className="location-input"
              />
              {startSearchResults.length > 0 && (
                <div className="search-results">
                  {startSearchResults.map((result, idx) => (
                    <div
                      key={idx}
                      className="search-result-item"
                      onClick={() => {
                        updateTripData({
                          start_address: result.name,
                          start_coordinates: result.coordinates
                        });
                        setStartSearchResults([]);
                      }}
                    >
                      <span className="result-icon">{result.type === 'city' ? '🏙️' : '📍'}</span>
                      <div>
                        <div className="result-name">{result.name}</div>
                        <div className="result-type">{result.type}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Duration */}
            <div className="form-group">
              <label>
                {isMultiDay ? 'How many days?' : 'How many hours?'}
              </label>
              <div className="duration-input">
                <input
                  type="range"
                  min={isMultiDay ? 1 : 2}
                  max={isMultiDay ? 30 : 12}
                  value={isMultiDay ? tripData.duration_days : tripData.duration_hours}
                  onChange={(e) => {
                    const value = parseInt(e.target.value);
                    updateTripData(
                      isMultiDay
                        ? { duration_days: value }
                        : { duration_hours: value }
                    );
                  }}
                  className="slider"
                />
                <span className="duration-value">
                  {isMultiDay ? tripData.duration_days : tripData.duration_hours} {isMultiDay ? 'days' : 'hours'}
                </span>
              </div>
            </div>

            {/* Max Distance */}
            <div className="form-group">
              <label>How far are you willing to travel?</label>
              <div className="duration-input">
                <input
                  type="range"
                  min="50"
                  max="1000"
                  step="50"
                  value={tripData.max_distance_km}
                  onChange={(e) => updateTripData({ max_distance_km: parseInt(e.target.value) })}
                  className="slider"
                />
                <span className="duration-value">{tripData.max_distance_km} km</span>
              </div>
            </div>

            {/* Planning Mode */}
            <div className="form-group">
              <label>Planning Mode</label>
              <div className="planning-mode-options">
                <div
                  className={`mode-option ${tripData.planning_mode === 'explore' ? 'active' : ''}`}
                  onClick={() => updateTripData({ planning_mode: 'explore' })}
                >
                  <span className="mode-icon">🎯</span>
                  <div>
                    <div className="mode-title">Explore based on duration</div>
                    <div className="mode-desc">Let us suggest destinations</div>
                  </div>
                </div>
                <div
                  className={`mode-option ${tripData.planning_mode === 'destination' ? 'active' : ''}`}
                  onClick={() => updateTripData({ planning_mode: 'destination' })}
                >
                  <span className="mode-icon">📍</span>
                  <div>
                    <div className="mode-title">I have a destination</div>
                    <div className="mode-desc">Specify where to end</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Round Trip Option */}
            {tripData.planning_mode === 'explore' && (
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={tripData.is_round_trip}
                    onChange={(e) => updateTripData({ is_round_trip: e.target.checked })}
                  />
                  <span>Round trip (return to start)</span>
                </label>
              </div>
            )}

            {/* End Address (if destination mode) */}
            {tripData.planning_mode === 'destination' && (
              <div className="form-group">
                <label>Where do you want to end up?</label>
                <input
                  type="text"
                  placeholder="Enter destination"
                  value={tripData.end_address}
                  onChange={(e) => {
                    updateTripData({ end_address: e.target.value });
                    searchEnd(e.target.value);
                  }}
                  className="location-input"
                />
                {endSearchResults.length > 0 && (
                  <div className="search-results">
                    {endSearchResults.map((result, idx) => (
                      <div
                        key={idx}
                        className="search-result-item"
                        onClick={() => {
                          updateTripData({
                            end_address: result.name,
                            end_coordinates: result.coordinates
                          });
                          setEndSearchResults([]);
                        }}
                      >
                        <span className="result-icon">{result.type === 'city' ? '🏙️' : '📍'}</span>
                        <div>
                          <div className="result-name">{result.name}</div>
                          <div className="result-type">{result.type}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Waypoints (for multi-day trips) */}
            {isMultiDay && (
              <div className="form-group waypoints-section">
                <label>Places to visit along the way (optional)</label>
                <p className="field-hint">Add countries, regions, cities, or specific attractions</p>

                {/* Waypoint List */}
                {tripData.waypoints.length > 0 && (
                  <DragDropContext onDragEnd={handleDragEnd}>
                    <Droppable droppableId="waypoints">
                      {(provided) => (
                        <div
                          className="waypoints-list"
                          {...provided.droppableProps}
                          ref={provided.innerRef}
                        >
                          {tripData.waypoints.map((wp, index) => (
                            <Draggable key={index} draggableId={`wp-${index}`} index={index}>
                              {(provided) => (
                                <div
                                  className="waypoint-item"
                                  ref={provided.innerRef}
                                  {...provided.draggableProps}
                                  {...provided.dragHandleProps}
                                >
                                  <span className="waypoint-number">{index + 1}</span>
                                  <div className="waypoint-info">
                                    <div className="waypoint-name">{wp.name}</div>
                                    <div className="waypoint-type">{wp.type}</div>
                                  </div>
                                  <button
                                    className="remove-btn"
                                    onClick={() => removeWaypoint(index)}
                                  >
                                    ×
                                  </button>
                                </div>
                              )}
                            </Draggable>
                          ))}
                          {provided.placeholder}
                        </div>
                      )}
                    </Droppable>
                  </DragDropContext>
                )}

                {/* Add Waypoint Input */}
                <div className="add-waypoint">
                  <input
                    type="text"
                    placeholder="e.g., Belgium, Amsterdam, or Europa-Park"
                    value={waypointSearch}
                    onChange={(e) => {
                      setWaypointSearch(e.target.value);
                      searchWaypoint(e.target.value);
                    }}
                    className="location-input"
                  />
                  {waypointSearchResults.length > 0 && (
                    <div className="search-results">
                      {waypointSearchResults.map((result, idx) => (
                        <div
                          key={idx}
                          className="search-result-item"
                          onClick={() => handleAddWaypoint(result)}
                        >
                          <span className="result-icon">
                            {result.type === 'country' ? '🌍' : result.type === 'city' ? '🏙️' : '📍'}
                          </span>
                          <div>
                            <div className="result-name">{result.name}</div>
                            <div className="result-type">{result.type}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Map */}
        <div className="right-panel">
          <div className="map-container">
            {isCalculatingRoute && (
              <div className="map-overlay">
                <LoadingSpinner size="small" message="Calculating route..." />
              </div>
            )}
            <MapView
              center={mapCenter}
              zoom={6}
              markers={markers}
              route={routeGeometry}
              circle={mapCircle}
            />
          </div>

          {/* Route Stats */}
          {tripData.route_stats.total_distance_km > 0 && (
            <div className="route-stats">
              <div className="stat-item">
                <span className="stat-icon">📏</span>
                <div>
                  <div className="stat-label">Total Distance</div>
                  <div className="stat-value">{tripData.route_stats.total_distance_km} km</div>
                </div>
              </div>
              <div className="stat-item">
                <span className="stat-icon">⏱️</span>
                <div>
                  <div className="stat-label">Estimated Driving</div>
                  <div className="stat-value">{tripData.route_stats.estimated_driving_hours} hours</div>
                </div>
              </div>
              <div className="stat-item">
                <span className="stat-icon">🗺️</span>
                <div>
                  <div className="stat-label">Waypoints</div>
                  <div className="stat-value">{tripData.waypoints.length} stops</div>
                </div>
              </div>
              <div className={`feasibility-message ${feasibility.color}`}>
                {feasibility.text}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Step2_Duration;
