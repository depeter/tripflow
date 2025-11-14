import axios from 'axios';

const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org';

// Rate limiting for OSRM API
let lastRouteRequestTime = 0;
const MIN_REQUEST_INTERVAL = 1000; // Minimum 1 second between requests

// Cache for route calculations to avoid duplicate API calls
const routeCache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Debounce helper
export const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

// Helper to generate cache key from coordinates
const getRouteCacheKey = (coordinates) => {
  return coordinates.map(c => `${c[0].toFixed(4)},${c[1].toFixed(4)}`).join('|');
};

/**
 * Search for locations by query string
 * @param {string} query - The search query
 * @returns {Promise<Array>} Array of location results
 */
export const geocodeAddress = async (query) => {
  if (!query || query.trim().length < 3) {
    return [];
  }

  try {
    const response = await axios.get(`${NOMINATIM_BASE_URL}/search`, {
      params: {
        q: query,
        format: 'json',
        addressdetails: 1,
        limit: 5,
        'accept-language': 'en'
      },
      headers: {
        'User-Agent': 'TripFlow/1.0'
      }
    });

    return response.data.map(item => ({
      name: item.display_name,
      address: item.display_name,
      coordinates: {
        lat: parseFloat(item.lat),
        lng: parseFloat(item.lon)
      },
      type: determineLocationType(item),
      boundingBox: item.boundingbox,
      osm_id: item.osm_id,
      osm_type: item.osm_type
    }));
  } catch (error) {
    console.error('Geocoding error:', error);
    return [];
  }
};

/**
 * Reverse geocode coordinates to get address
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @returns {Promise<Object>} Location object
 */
export const reverseGeocode = async (lat, lng) => {
  try {
    const response = await axios.get(`${NOMINATIM_BASE_URL}/reverse`, {
      params: {
        lat,
        lon: lng,
        format: 'json',
        addressdetails: 1
      },
      headers: {
        'User-Agent': 'TripFlow/1.0'
      }
    });

    const data = response.data;
    return {
      name: data.display_name,
      address: data.display_name,
      coordinates: {
        lat: parseFloat(data.lat),
        lng: parseFloat(data.lon)
      },
      type: determineLocationType(data)
    };
  } catch (error) {
    console.error('Reverse geocoding error:', error);
    return null;
  }
};

/**
 * Determine location type from OSM data
 * @param {Object} osmData - OSM location data
 * @returns {string} Location type
 */
const determineLocationType = (osmData) => {
  const type = osmData.type || '';
  const addressType = osmData.addresstype || '';

  // Check for countries
  if (type === 'administrative' && osmData.address?.country) {
    if (osmData.address.country === osmData.display_name.split(',')[0].trim()) {
      return 'country';
    }
    return 'region';
  }

  // Check for cities
  if (['city', 'town', 'village', 'municipality'].includes(addressType)) {
    return 'city';
  }

  // Check for attractions/POIs
  if (['tourism', 'attraction', 'museum', 'monument'].includes(type)) {
    return 'attraction';
  }

  // Default to address
  return 'address';
};

/**
 * Calculate driving route between points using OSRM
 * @param {Array} coordinates - Array of [lng, lat] coordinates
 * @returns {Promise<Object>} Route data with geometry and stats
 */
export const calculateRoute = async (coordinates) => {
  if (!coordinates || coordinates.length < 2) {
    return null;
  }

  // Check cache first
  const cacheKey = getRouteCacheKey(coordinates);
  const cached = routeCache.get(cacheKey);
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    console.log('📦 Using cached route data');
    return cached.data;
  }

  // Rate limiting: ensure minimum time between requests
  const now = Date.now();
  const timeSinceLastRequest = now - lastRouteRequestTime;
  if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
    const waitTime = MIN_REQUEST_INTERVAL - timeSinceLastRequest;
    console.log(`⏳ Rate limiting: waiting ${waitTime}ms before next request`);
    await new Promise(resolve => setTimeout(resolve, waitTime));
  }

  try {
    lastRouteRequestTime = Date.now();

    // Convert to OSRM format: lng,lat;lng,lat
    const coordString = coordinates
      .map(coord => `${coord[1]},${coord[0]}`) // OSRM uses lng,lat
      .join(';');

    const response = await axios.get(
      `https://router.project-osrm.org/route/v1/driving/${coordString}`,
      {
        params: {
          overview: 'full',
          geometries: 'geojson',
          steps: false
        },
        timeout: 10000 // 10 second timeout
      }
    );

    if (response.data.code !== 'Ok') {
      throw new Error('Route calculation failed');
    }

    const route = response.data.routes[0];

    const routeData = {
      distance: route.distance, // meters
      duration: route.duration, // seconds
      geometry: route.geometry.coordinates.map(coord => [coord[1], coord[0]]), // Convert back to [lat, lng]
      legs: route.legs.map(leg => ({
        distance: leg.distance,
        duration: leg.duration
      }))
    };

    // Cache the result
    routeCache.set(cacheKey, {
      data: routeData,
      timestamp: Date.now()
    });

    // Clean old cache entries (keep cache size manageable)
    if (routeCache.size > 50) {
      const entries = Array.from(routeCache.entries());
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
      for (let i = 0; i < 10; i++) {
        routeCache.delete(entries[i][0]);
      }
    }

    return routeData;
  } catch (error) {
    // Handle CORS errors gracefully
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.warn('⚠️ Route calculation unavailable (CORS/Network issue). Route display disabled.');
      console.info('ℹ️ To enable routing, consider setting up a backend proxy for OSRM API calls.');
    } else if (error.response && error.response.status === 429) {
      console.error('🚫 Rate limit exceeded. Please wait before making more requests.');
    } else {
      console.error('Route calculation error:', error.message || error);
    }
    return null;
  }
};

/**
 * Calculate route feasibility based on distance and duration
 * @param {number} totalDistanceKm - Total distance in kilometers
 * @param {number} durationDays - Trip duration in days
 * @param {number} durationHours - Trip duration in hours (for day trips)
 * @param {boolean} isMultiDay - Whether it's a multi-day trip
 * @returns {string} Feasibility status
 */
export const calculateFeasibility = (totalDistanceKm, durationDays, durationHours, isMultiDay) => {
  if (isMultiDay) {
    // For multi-day trips: comfortable = <300km/day, tight = 300-500km/day, too_ambitious = >500km/day
    const kmPerDay = totalDistanceKm / durationDays;

    if (kmPerDay <= 300) {
      return 'comfortable';
    } else if (kmPerDay <= 500) {
      return 'tight';
    } else {
      return 'too_ambitious';
    }
  } else {
    // For day trips: comfortable = <200km, tight = 200-400km, too_ambitious = >400km
    if (totalDistanceKm <= 200) {
      return 'comfortable';
    } else if (totalDistanceKm <= 400) {
      return 'tight';
    } else {
      return 'too_ambitious';
    }
  }
};
