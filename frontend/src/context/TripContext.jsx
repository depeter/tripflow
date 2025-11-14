import React, { createContext, useContext, useState, useEffect } from 'react';

const TripContext = createContext();

export const useTripContext = () => {
  const context = useContext(TripContext);
  if (!context) {
    throw new Error('useTripContext must be used within a TripProvider');
  }
  return context;
};

export const TripProvider = ({ children }) => {
  // Load saved trip data from localStorage
  const loadSavedTrip = () => {
    try {
      const saved = localStorage.getItem('tripflow_current_trip');
      if (!saved) return null;

      const parsed = JSON.parse(saved);

      // Validate that current_step is within valid range
      if (parsed.current_step < 1 || parsed.current_step > 6) {
        console.warn('Invalid current_step in saved data, resetting');
        localStorage.removeItem('tripflow_current_trip');
        return null;
      }

      // Ensure completed_steps is an array
      if (!Array.isArray(parsed.completed_steps)) {
        parsed.completed_steps = [];
      }

      // Ensure completed_steps doesn't include invalid steps
      parsed.completed_steps = parsed.completed_steps.filter(step => step >= 1 && step <= 6);

      return parsed;
    } catch (error) {
      console.error('Error loading saved trip:', error);
      localStorage.removeItem('tripflow_current_trip');
      return null;
    }
  };

  const initialState = loadSavedTrip() || {
    // Step 1: Trip Type
    is_camper: false,
    trip_type: 'day_trip', // 'multi_day' | 'day_trip'

    // Step 2: Start & Duration
    start_address: '',
    start_coordinates: null,
    duration_days: 3,
    duration_hours: 8,
    max_distance_km: 500,
    planning_mode: 'explore', // 'explore' | 'destination'
    is_round_trip: true,
    end_address: '',
    end_coordinates: null,
    waypoints: [],
    route_stats: {
      total_distance_km: 0,
      estimated_driving_hours: 0,
      feasibility_status: 'comfortable' // 'comfortable' | 'tight' | 'too_ambitious'
    },

    // Step 3: Preferences
    interests: [],
    preferred_environment: [],
    preferred_amenities: [],
    max_price_per_night: 50,
    avoid_crowded: false,
    activity_level: 'moderate',

    // Step 4+: Recommendations and route
    recommended_locations: [],
    selected_waypoints: [],

    // Meta
    current_step: 1,
    completed_steps: []
  };

  const [tripData, setTripData] = useState(initialState);

  // Auto-save to localStorage whenever tripData changes
  useEffect(() => {
    try {
      localStorage.setItem('tripflow_current_trip', JSON.stringify(tripData));
    } catch (error) {
      console.error('Error saving trip:', error);
    }
  }, [tripData]);

  const updateTripData = (updates) => {
    setTripData(prev => ({
      ...prev,
      ...updates
    }));
  };

  const updateWaypoint = (index, waypoint) => {
    setTripData(prev => ({
      ...prev,
      waypoints: prev.waypoints.map((wp, i) => i === index ? waypoint : wp)
    }));
  };

  const addWaypoint = (waypoint) => {
    setTripData(prev => ({
      ...prev,
      waypoints: [...prev.waypoints, { ...waypoint, order: prev.waypoints.length }]
    }));
  };

  const removeWaypoint = (index) => {
    setTripData(prev => ({
      ...prev,
      waypoints: prev.waypoints.filter((_, i) => i !== index).map((wp, i) => ({ ...wp, order: i }))
    }));
  };

  const reorderWaypoints = (newWaypoints) => {
    setTripData(prev => ({
      ...prev,
      waypoints: newWaypoints.map((wp, i) => ({ ...wp, order: i }))
    }));
  };

  const updateRouteStats = (stats) => {
    setTripData(prev => ({
      ...prev,
      route_stats: { ...prev.route_stats, ...stats }
    }));
  };

  const goToStep = (step) => {
    setTripData(prev => ({
      ...prev,
      current_step: step
    }));
  };

  const completeStep = (step) => {
    setTripData(prev => ({
      ...prev,
      completed_steps: [...new Set([...prev.completed_steps, step])]
    }));
  };

  const resetTrip = () => {
    localStorage.removeItem('tripflow_current_trip');
    const freshState = {
      is_camper: false,
      trip_type: 'day_trip',
      start_address: '',
      start_coordinates: null,
      duration_days: 3,
      duration_hours: 8,
      max_distance_km: 500,
      planning_mode: 'explore',
      is_round_trip: true,
      end_address: '',
      end_coordinates: null,
      waypoints: [],
      route_stats: {
        total_distance_km: 0,
        estimated_driving_hours: 0,
        feasibility_status: 'comfortable'
      },
      interests: [],
      preferred_environment: [],
      preferred_amenities: [],
      max_price_per_night: 50,
      avoid_crowded: false,
      activity_level: 'moderate',
      recommended_locations: [],
      selected_waypoints: [],
      current_step: 1,
      completed_steps: []
    };
    setTripData(freshState);
  };

  const value = {
    tripData,
    updateTripData,
    updateWaypoint,
    addWaypoint,
    removeWaypoint,
    reorderWaypoints,
    updateRouteStats,
    goToStep,
    completeStep,
    resetTrip
  };

  return (
    <TripContext.Provider value={value}>
      {children}
    </TripContext.Provider>
  );
};
