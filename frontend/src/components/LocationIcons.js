import L from 'leaflet';

// Icon configuration for each location type
const iconConfig = {
  campsite: {
    emoji: '⛺',
    color: '#10B981', // Green
    label: 'Campsite'
  },
  parking: {
    emoji: '🅿️',
    color: '#3B82F6', // Blue
    label: 'Parking'
  },
  service_area: {
    emoji: '🚰',
    color: '#8B5CF6', // Purple
    label: 'Service Area'
  },
  rest_area: {
    emoji: '🛋️',
    color: '#F59E0B', // Amber
    label: 'Rest Area'
  },
  attraction: {
    emoji: '🎯',
    color: '#EF4444', // Red
    label: 'Attraction'
  },
  poi: {
    emoji: '📍',
    color: '#EC4899', // Pink
    label: 'Point of Interest'
  },
  event_venue: {
    emoji: '🎪',
    color: '#6366F1', // Indigo
    label: 'Event Venue'
  },
  custom: {
    emoji: '⭐',
    color: '#FBBF24', // Yellow
    label: 'Custom Location'
  }
};

/**
 * Create a custom Leaflet icon for a location type
 * @param {string} locationType - The type of location (campsite, parking, etc.)
 * @param {boolean} isSelected - Whether the location is selected
 * @param {number|null} number - Optional number to display (for selected locations)
 * @returns {L.DivIcon} Leaflet DivIcon
 */
export const createLocationIcon = (locationType, isSelected = false, number = null) => {
  const config = iconConfig[locationType] || iconConfig.poi;

  // If location is selected and has a number, show numbered marker
  if (isSelected && number !== null) {
    return L.divIcon({
      className: 'location-marker selected',
      html: `
        <div class="marker-pin" style="background-color: ${config.color}">
          <span class="marker-number">${number}</span>
        </div>
      `,
      iconSize: [36, 48],
      iconAnchor: [18, 48],
      popupAnchor: [0, -48]
    });
  }

  // Regular location marker with emoji
  return L.divIcon({
    className: `location-marker ${locationType} ${isSelected ? 'selected' : ''}`,
    html: `
      <div class="marker-pin" style="background-color: ${config.color}">
        <span class="marker-emoji">${config.emoji}</span>
      </div>
      ${isSelected ? '<div class="marker-ring"></div>' : ''}
    `,
    iconSize: [32, 42],
    iconAnchor: [16, 42],
    popupAnchor: [0, -42]
  });
};

/**
 * Create a numbered marker icon (for route waypoints)
 * @param {number} number - The waypoint number
 * @returns {L.DivIcon} Leaflet DivIcon
 */
export const createNumberedIcon = (number) => {
  return L.divIcon({
    className: 'numbered-marker',
    html: `<div class="marker-pin"><span>${number}</span></div>`,
    iconSize: [30, 42],
    iconAnchor: [15, 42],
    popupAnchor: [0, -42]
  });
};

/**
 * Get icon configuration for a location type
 * @param {string} locationType - The type of location
 * @returns {object} Icon configuration
 */
export const getIconConfig = (locationType) => {
  return iconConfig[locationType] || iconConfig.poi;
};

/**
 * Create a legend for the map showing all location types
 * @returns {Array} Array of legend items {type, emoji, color, label}
 */
export const createLegendItems = () => {
  return Object.entries(iconConfig).map(([type, config]) => ({
    type,
    ...config
  }));
};

export default {
  createLocationIcon,
  createNumberedIcon,
  getIconConfig,
  createLegendItems
};
