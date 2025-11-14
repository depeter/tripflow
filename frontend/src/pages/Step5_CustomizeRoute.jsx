import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { useTripContext } from '../context/TripContext';
import MapView from '../components/MapView';
import LoadingSpinner from '../components/LoadingSpinner';
import { calculateRoute } from '../services/geocodingService';
import './Step5_CustomizeRoute.css';

const Step5_CustomizeRoute = ({ onNext, onBack }) => {
  const { tripData, updateTripData } = useTripContext();
  const [waypoints, setWaypoints] = useState(tripData.selected_waypoints || []);
  const [routeGeometry, setRouteGeometry] = useState([]);
  const [isCalculating, setIsCalculating] = useState(false);
  const [routeStats, setRouteStats] = useState({
    totalDistance: 0,
    totalTime: 0
  });

  // Debounced route calculation to avoid rapid API requests
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      calculateFullRoute();
    }, 500); // Wait 500ms after last change before recalculating

    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [waypoints]);

  const calculateFullRoute = async () => {
    const coords = [];

    // Only proceed if we have a valid start location
    if (tripData.start_coordinates && tripData.start_address && tripData.start_address.trim().length > 0) {
      coords.push([tripData.start_coordinates.lat, tripData.start_coordinates.lng]);
    } else {
      // No valid start location, reset route display
      setRouteGeometry([]);
      setRouteStats({
        totalDistance: 0,
        totalTime: 0
      });
      return;
    }

    waypoints.forEach(wp => {
      if (wp.coordinates) {
        coords.push([wp.coordinates.lat, wp.coordinates.lng]);
      }
    });

    if (tripData.is_round_trip && tripData.start_coordinates) {
      coords.push([tripData.start_coordinates.lat, tripData.start_coordinates.lng]);
    }

    if (coords.length >= 2) {
      setIsCalculating(true);
      const route = await calculateRoute(coords);

      if (route) {
        setRouteGeometry(route.geometry);
        setRouteStats({
          totalDistance: Math.round(route.distance / 1000),
          totalTime: Math.round(route.duration / 3600 * 10) / 10
        });
      }

      setIsCalculating(false);
    } else {
      // Not enough coordinates for a route
      setRouteGeometry([]);
      setRouteStats({
        totalDistance: 0,
        totalTime: 0
      });
    }
  };

  const handleDragEnd = (result) => {
    if (!result.destination) return;

    const items = Array.from(waypoints);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    setWaypoints(items);
    updateTripData({ selected_waypoints: items });
  };

  const handleRemoveWaypoint = (index) => {
    const newWaypoints = waypoints.filter((_, i) => i !== index);
    setWaypoints(newWaypoints);
    updateTripData({ selected_waypoints: newWaypoints });
  };

  const handleOptimizeRoute = async () => {
    // Simple optimization: sort by distance from start
    if (!tripData.start_coordinates || waypoints.length < 2) return;

    setIsCalculating(true);

    const calculateDistance = (lat1, lon1, lat2, lon2) => {
      const R = 6371;
      const dLat = (lat2 - lat1) * Math.PI / 180;
      const dLon = (lon2 - lon1) * Math.PI / 180;
      const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return R * c;
    };

    // Sort waypoints by distance from start
    const sorted = [...waypoints].sort((a, b) => {
      const distA = calculateDistance(
        tripData.start_coordinates.lat,
        tripData.start_coordinates.lng,
        a.coordinates.lat,
        a.coordinates.lng
      );
      const distB = calculateDistance(
        tripData.start_coordinates.lat,
        tripData.start_coordinates.lng,
        b.coordinates.lat,
        b.coordinates.lng
      );
      return distA - distB;
    });

    setWaypoints(sorted);
    updateTripData({ selected_waypoints: sorted });

    await new Promise(resolve => setTimeout(resolve, 500));
    setIsCalculating(false);
  };

  const handleContinue = () => {
    onNext();
  };

  // Build map markers
  const buildMapMarkers = () => {
    const markers = [];

    if (tripData.start_coordinates) {
      markers.push({
        id: 'start',
        position: [tripData.start_coordinates.lat, tripData.start_coordinates.lng],
        popup: `Start: ${tripData.start_address}`
      });
    }

    waypoints.forEach((wp, idx) => {
      markers.push({
        id: `wp-${idx}`,
        position: [wp.coordinates.lat, wp.coordinates.lng],
        popup: wp.name,
        numbered: true,
        number: idx + 1
      });
    });

    return markers;
  };

  const markers = buildMapMarkers();
  const mapCenter = tripData.start_coordinates
    ? [tripData.start_coordinates.lat, tripData.start_coordinates.lng]
    : [50.8503, 4.3517];

  return (
    <div className="step5-container">
      <div className="split-screen">
        {/* Left Panel - Waypoint List */}
        <div className="left-panel">
          <div className="panel-header">
            <h2>Customize Your Route</h2>
            <p className="section-subtitle">
              Drag to reorder stops or remove locations from your trip
            </p>
          </div>

          <div className="route-actions">
            <button className="btn btn-secondary" onClick={handleOptimizeRoute} disabled={isCalculating}>
              🎯 Optimize Route
            </button>
            <span className="hint-text">Reorder for shortest distance</span>
          </div>

          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="route-waypoints">
              {(provided) => (
                <div
                  className="waypoints-list"
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                >
                  {/* Start Location */}
                  <div className="route-item start-item">
                    <div className="route-marker start-marker">📍</div>
                    <div className="route-info">
                      <div className="route-title">Start</div>
                      <div className="route-subtitle">{tripData.start_address}</div>
                    </div>
                  </div>

                  {waypoints.map((waypoint, index) => (
                    <React.Fragment key={waypoint.id}>
                      <div className="route-connector">
                        <div className="connector-line"></div>
                        <div className="connector-info">
                          {/* Distance info could go here */}
                        </div>
                      </div>

                      <Draggable draggableId={`waypoint-${waypoint.id}`} index={index}>
                        {(provided, snapshot) => (
                          <div
                            className={`route-item waypoint-item ${snapshot.isDragging ? 'dragging' : ''}`}
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                          >
                            <div className="route-marker">{index + 1}</div>
                            <div className="route-info">
                              <div className="route-title">{waypoint.name}</div>
                              <div className="route-subtitle">
                                {waypoint.type} • ⭐{waypoint.rating}
                                {waypoint.price_per_night > 0 && ` • €${waypoint.price_per_night}/night`}
                              </div>
                              {waypoint.tags && (
                                <div className="route-tags">
                                  {waypoint.tags.slice(0, 2).map((tag, idx) => (
                                    <span key={idx} className="mini-tag">{tag}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                            <button
                              className="remove-waypoint-btn"
                              onClick={() => handleRemoveWaypoint(index)}
                            >
                              ×
                            </button>
                          </div>
                        )}
                      </Draggable>
                    </React.Fragment>
                  ))}

                  {provided.placeholder}

                  {/* End Location (if not round trip) */}
                  {!tripData.is_round_trip && tripData.end_address && (
                    <>
                      <div className="route-connector">
                        <div className="connector-line"></div>
                      </div>
                      <div className="route-item end-item">
                        <div className="route-marker end-marker">🏁</div>
                        <div className="route-info">
                          <div className="route-title">End</div>
                          <div className="route-subtitle">{tripData.end_address}</div>
                        </div>
                      </div>
                    </>
                  )}

                  {tripData.is_round_trip && waypoints.length > 0 && (
                    <>
                      <div className="route-connector">
                        <div className="connector-line"></div>
                      </div>
                      <div className="route-item end-item">
                        <div className="route-marker end-marker">🔄</div>
                        <div className="route-info">
                          <div className="route-title">Return</div>
                          <div className="route-subtitle">Back to {tripData.start_address}</div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}
            </Droppable>
          </DragDropContext>

          {/* Trip Stats */}
          <div className="trip-stats-panel">
            <div className="stat-box">
              <span className="stat-icon">📏</span>
              <div>
                <div className="stat-label">Total Distance</div>
                <div className="stat-value">{routeStats.totalDistance} km</div>
              </div>
            </div>
            <div className="stat-box">
              <span className="stat-icon">⏱️</span>
              <div>
                <div className="stat-label">Driving Time</div>
                <div className="stat-value">{routeStats.totalTime} hours</div>
              </div>
            </div>
            <div className="stat-box">
              <span className="stat-icon">📅</span>
              <div>
                <div className="stat-label">Trip Duration</div>
                <div className="stat-value">
                  {tripData.trip_type === 'multi_day' ? `${tripData.duration_days} days` : `${tripData.duration_hours} hours`}
                </div>
              </div>
            </div>
            <div className="stat-box">
              <span className="stat-icon">🗺️</span>
              <div>
                <div className="stat-label">Stops</div>
                <div className="stat-value">{waypoints.length}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Map */}
        <div className="right-panel">
          <div className="map-container">
            {isCalculating && (
              <div className="map-overlay">
                <LoadingSpinner size="small" message="Recalculating route..." />
              </div>
            )}
            <MapView
              center={mapCenter}
              zoom={6}
              markers={markers}
              route={routeGeometry}
            />
          </div>
        </div>
      </div>

      {/* Footer Navigation */}
      <div className="step5-footer">
        <button className="btn btn-outline" onClick={onBack}>
          ← Back
        </button>
        <div className="footer-info">
          <span className="info-text">
            Your route is ready!
          </span>
        </div>
        <button className="btn btn-primary" onClick={handleContinue}>
          Review & Finalize →
        </button>
      </div>
    </div>
  );
};

export default Step5_CustomizeRoute;
