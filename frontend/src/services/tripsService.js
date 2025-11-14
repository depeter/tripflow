import apiClient from './api';

/**
 * Trip and Recommendation API Service
 * Connects frontend to TripFlow backend API
 */

// ============ Recommendations API ============

/**
 * Get personalized recommendations based on user preferences
 * @param {Object} params - Recommendation parameters
 * @param {number} params.max_distance_km - Maximum distance from start
 * @param {string[]} params.interests - User interests
 * @param {string[]} params.preferred_environment - Environment preferences
 * @param {string[]} params.preferred_amenities - Amenity preferences
 * @param {number} params.budget_per_day - Budget per day
 * @param {string} params.activity_level - Activity level (relaxed/moderate/active)
 * @param {Object} params.start_coordinates - {lat, lng}
 * @param {number} params.limit - Number of results (default: 20)
 * @returns {Promise} Array of recommended locations
 */
export const getRecommendations = async (params) => {
  try {
    const response = await apiClient.post('/recommendations/', {
      max_distance_km: params.max_distance_km || 500,
      interests: params.interests || [],
      preferred_environment: params.preferred_environment || [],
      preferred_amenities: params.preferred_amenities || [],
      budget_per_day: params.budget_per_day || 50,
      activity_level: params.activity_level || 'moderate',
      start_location: params.start_coordinates,
      limit: params.limit || 20
    });

    return response.data;
  } catch (error) {
    console.error('Failed to get recommendations:', error);
    throw error;
  }
};

/**
 * Index a single location in Qdrant vector database
 * @param {number} locationId - Location ID to index
 */
export const indexLocation = async (locationId) => {
  try {
    const response = await apiClient.post(`/recommendations/index-location/${locationId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to index location:', error);
    throw error;
  }
};

/**
 * Index all locations in Qdrant vector database
 */
export const indexAllLocations = async () => {
  try {
    const response = await apiClient.post('/recommendations/index-all');
    return response.data;
  } catch (error) {
    console.error('Failed to index all locations:', error);
    throw error;
  }
};

// ============ Trips API ============

/**
 * Create a new trip
 * @param {Object} tripData - Trip data
 * @returns {Promise} Created trip object
 */
export const createTrip = async (tripData) => {
  try {
    const response = await apiClient.post('/trips/', {
      name: tripData.tripName || 'My Trip',
      start_location: tripData.start_address,
      start_coordinates: tripData.start_coordinates,
      end_location: tripData.end_address,
      end_coordinates: tripData.end_coordinates,
      is_round_trip: tripData.is_round_trip !== false,
      is_camper: tripData.is_camper || false,
      trip_type: tripData.trip_type || 'multi_day',
      duration_days: tripData.duration_days || 3,
      duration_hours: tripData.duration_hours || 8,
      max_distance_km: tripData.max_distance_km || 500,
      preferences: {
        interests: tripData.interests || [],
        preferred_environment: tripData.preferred_environment || [],
        preferred_amenities: tripData.preferred_amenities || [],
        budget_per_day: tripData.budget_per_day || 50,
        activity_level: tripData.activity_level || 'moderate'
      }
    });

    return response.data;
  } catch (error) {
    console.error('Failed to create trip:', error);
    throw error;
  }
};

/**
 * Get trip by ID
 * @param {number} tripId - Trip ID
 */
export const getTrip = async (tripId) => {
  try {
    const response = await apiClient.get(`/trips/${tripId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to get trip:', error);
    throw error;
  }
};

/**
 * Get all trips for current user
 * @param {number} limit - Number of trips to return
 * @param {number} offset - Offset for pagination
 */
export const getUserTrips = async (limit = 10, offset = 0) => {
  try {
    const response = await apiClient.get('/trips/', {
      params: { limit, offset }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to get user trips:', error);
    throw error;
  }
};

/**
 * Add a waypoint to a trip
 * @param {number} tripId - Trip ID
 * @param {number} locationId - Location ID to add
 * @param {number} order - Order in the trip
 */
export const addWaypoint = async (tripId, locationId, order) => {
  try {
    const response = await apiClient.post(`/trips/${tripId}/waypoints`, {
      location_id: locationId,
      order: order
    });
    return response.data;
  } catch (error) {
    console.error('Failed to add waypoint:', error);
    throw error;
  }
};

/**
 * Remove a waypoint from a trip
 * @param {number} tripId - Trip ID
 * @param {number} locationId - Location ID to remove
 */
export const removeWaypoint = async (tripId, locationId) => {
  try {
    const response = await apiClient.delete(`/trips/${tripId}/waypoints/${locationId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to remove waypoint:', error);
    throw error;
  }
};

/**
 * Get suggested waypoints for a trip
 * @param {number} tripId - Trip ID
 * @param {number} limit - Number of suggestions
 */
export const getSuggestedWaypoints = async (tripId, limit = 10) => {
  try {
    const response = await apiClient.post(`/trips/${tripId}/suggest-waypoints`, { limit });
    return response.data;
  } catch (error) {
    console.error('Failed to get suggested waypoints:', error);
    throw error;
  }
};

/**
 * Get trip statistics
 * @param {number} tripId - Trip ID
 */
export const getTripStats = async (tripId) => {
  try {
    const response = await apiClient.get(`/trips/${tripId}/stats`);
    return response.data;
  } catch (error) {
    console.error('Failed to get trip stats:', error);
    throw error;
  }
};

/**
 * Finalize a trip
 * @param {number} tripId - Trip ID
 * @param {string} startDate - Start date
 */
export const finalizeTrip = async (tripId, startDate) => {
  try {
    const response = await apiClient.post(`/trips/${tripId}/finalize`, {
      start_date: startDate
    });
    return response.data;
  } catch (error) {
    console.error('Failed to finalize trip:', error);
    throw error;
  }
};

// ============ Locations API ============

/**
 * Search locations
 * @param {Object} params - Search parameters
 */
export const searchLocations = async (params) => {
  try {
    const response = await apiClient.get('/locations/search', { params });
    return response.data;
  } catch (error) {
    console.error('Failed to search locations:', error);
    throw error;
  }
};

/**
 * Get location by ID
 * @param {number} locationId - Location ID
 */
export const getLocation = async (locationId) => {
  try {
    const response = await apiClient.get(`/locations/${locationId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to get location:', error);
    throw error;
  }
};

export default {
  // Recommendations
  getRecommendations,
  indexLocation,
  indexAllLocations,

  // Trips
  createTrip,
  getTrip,
  getUserTrips,
  addWaypoint,
  removeWaypoint,
  getSuggestedWaypoints,
  getTripStats,
  finalizeTrip,

  // Locations
  searchLocations,
  getLocation
};
