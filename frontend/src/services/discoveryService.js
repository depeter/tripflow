import apiClient from './api';

/**
 * Discovery Service
 * Handles event discovery and favorites functionality
 */

const discoveryService = {
  /**
   * Search for events near a location
   * @param {Object} params - Search parameters
   * @param {number} params.latitude - Latitude
   * @param {number} params.longitude - Longitude
   * @param {number} params.radius_km - Search radius in kilometers (default: 25)
   * @param {Array<string>} params.item_types - Filter by item types: 'events', 'locations' (optional)
   * @param {Array<string>} params.categories - Filter by categories (optional)
   * @param {Array<string>} params.event_types - Filter by event types (optional)
   * @param {string} params.search_text - Search text for name/description (optional)
   * @param {string} params.start_date - ISO datetime string for start filter (optional)
   * @param {string} params.end_date - ISO datetime string for end filter (optional)
   * @param {boolean} params.free_only - Only show free events (optional)
   * @param {number} params.limit - Maximum number of results (default: 50)
   * @returns {Promise} Discovery response with events
   */
  searchEvents: async (params) => {
    try {
      // Build the request payload with proper structure
      const payload = {
        latitude: params.latitude,
        longitude: params.longitude,
        radius_km: params.radius_km || 25,
        item_types: params.item_types || null,
        search_text: params.search_text || null,
        limit: params.limit || 50,
      };

      // Add nested event_filters if provided
      if (params.event_filters) {
        payload.event_filters = params.event_filters;
      }

      // Add nested location_filters if provided
      if (params.location_filters) {
        payload.location_filters = params.location_filters;
      }

      // Legacy support for flat parameters (will be removed eventually)
      if (params.categories) payload.categories = params.categories;
      if (params.event_types) payload.event_types = params.event_types;
      if (params.start_date) payload.start_date = params.start_date;
      if (params.end_date) payload.end_date = params.end_date;
      if (params.free_only !== undefined) payload.free_only = params.free_only;

      const response = await apiClient.post('/discover', payload);
      return response.data;
    } catch (error) {
      console.error('Error searching events:', error);
      throw error;
    }
  },

  /**
   * Get available event categories
   * @returns {Promise<Array<string>>} List of category names
   */
  getCategories: async () => {
    try {
      const response = await apiClient.get('/discover/categories');
      return response.data;
    } catch (error) {
      console.error('Error fetching categories:', error);
      throw error;
    }
  },

  /**
   * Get discovery statistics
   * @returns {Promise} Statistics object
   */
  getStats: async () => {
    try {
      const response = await apiClient.get('/discover/stats');
      return response.data;
    } catch (error) {
      console.error('Error fetching stats:', error);
      throw error;
    }
  },

  /**
   * Add event to favorites
   * @param {number} eventId - Event ID to favorite
   * @returns {Promise} Favorite object
   */
  addFavorite: async (eventId) => {
    try {
      const response = await apiClient.post('/favorites', {
        event_id: eventId,
      });
      return response.data;
    } catch (error) {
      console.error('Error adding favorite:', error);
      throw error;
    }
  },

  /**
   * Remove event from favorites
   * @param {number} eventId - Event ID to unfavorite
   * @returns {Promise}
   */
  removeFavorite: async (eventId) => {
    try {
      await apiClient.delete(`/favorites/${eventId}`);
    } catch (error) {
      console.error('Error removing favorite:', error);
      throw error;
    }
  },

  /**
   * Get all favorited events for current user
   * @returns {Promise<Array>} List of favorited events
   */
  getFavorites: async () => {
    try {
      const response = await apiClient.get('/favorites');
      return response.data;
    } catch (error) {
      console.error('Error fetching favorites:', error);
      throw error;
    }
  },

  /**
   * Check if an event is favorited
   * @param {number} eventId - Event ID to check
   * @returns {Promise<boolean>} True if favorited
   */
  checkFavorite: async (eventId) => {
    try {
      const response = await apiClient.get(`/favorites/check/${eventId}`);
      return response.data;
    } catch (error) {
      console.error('Error checking favorite:', error);
      return false;
    }
  },

  /**
   * Get list of favorited event IDs
   * @returns {Promise<Array<number>>} List of event IDs
   */
  getFavoriteIds: async () => {
    try {
      const response = await apiClient.get('/favorites/ids');
      return response.data;
    } catch (error) {
      console.error('Error fetching favorite IDs:', error);
      return [];
    }
  },
};

export default discoveryService;
