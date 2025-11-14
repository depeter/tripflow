/**
 * Mock Recommendations Service
 * In production, this would call the backend API
 * For now, generates realistic mock data based on user preferences
 */

const MOCK_LOCATIONS = [
  {
    id: 1,
    name: 'Camping De Zeebries',
    type: 'campsite',
    rating: 4.5,
    price_per_night: 25,
    coordinates: { lat: 51.2093, lng: 2.7437 },
    tags: ['beach', 'family-friendly', 'nature'],
    description: 'Beautiful beachside campsite with modern facilities and stunning sea views.',
    interests: ['beach', 'camping', 'nature'],
    environments: ['coastal', 'sunny'],
    amenities: ['electricity', 'water', 'showers', 'wifi', 'toilets']
  },
  {
    id: 2,
    name: 'Neuschwanstein Castle',
    type: 'attraction',
    rating: 4.8,
    price_per_night: 0,
    coordinates: { lat: 47.5576, lng: 10.7498 },
    tags: ['culture', 'historic', 'photography'],
    description: 'Iconic fairy-tale castle in the Bavarian Alps, a must-see attraction.',
    interests: ['culture', 'photography', 'hiking'],
    environments: ['mountains']
  },
  {
    id: 3,
    name: 'Black Forest Camping',
    type: 'campsite',
    rating: 4.6,
    price_per_night: 30,
    coordinates: { lat: 48.3668, lng: 8.2333 },
    tags: ['nature', 'hiking', 'forests'],
    description: 'Peaceful campsite nestled in the heart of the Black Forest.',
    interests: ['nature', 'camping', 'hiking'],
    environments: ['forests', 'mountains'],
    amenities: ['electricity', 'water', 'showers', 'restaurant']
  },
  {
    id: 4,
    name: 'Côte d\'Azur Beach Resort',
    type: 'campsite',
    rating: 4.7,
    price_per_night: 45,
    coordinates: { lat: 43.5528, lng: 7.0174 },
    tags: ['beach', 'luxury', 'sunny'],
    description: 'Premium beachside location on the French Riviera with excellent amenities.',
    interests: ['beach', 'food_wine'],
    environments: ['coastal', 'sunny'],
    amenities: ['electricity', 'water', 'showers', 'wifi', 'toilets', 'restaurant']
  },
  {
    id: 5,
    name: 'Louvre Museum',
    type: 'attraction',
    rating: 4.9,
    price_per_night: 0,
    coordinates: { lat: 48.8606, lng: 2.3376 },
    tags: ['art', 'culture', 'city'],
    description: 'World\'s largest art museum and historic monument in Paris.',
    interests: ['art', 'culture', 'photography'],
    environments: ['city']
  },
  {
    id: 6,
    name: 'Alpine Adventure Camp',
    type: 'campsite',
    rating: 4.4,
    price_per_night: 35,
    coordinates: { lat: 46.5197, lng: 6.6323 },
    tags: ['mountains', 'sports', 'adventure'],
    description: 'Perfect base for mountain sports and hiking in the Swiss Alps.',
    interests: ['hiking', 'sports', 'camping'],
    environments: ['mountains'],
    amenities: ['electricity', 'water', 'showers', 'wifi']
  },
  {
    id: 7,
    name: 'Tuscany Vineyard Camping',
    type: 'campsite',
    rating: 4.5,
    price_per_night: 28,
    coordinates: { lat: 43.7696, lng: 11.2558 },
    tags: ['wine', 'countryside', 'food'],
    description: 'Charming campsite among vineyards with wine tasting experiences.',
    interests: ['food_wine', 'nature'],
    environments: ['countryside', 'sunny'],
    amenities: ['electricity', 'water', 'toilets', 'restaurant']
  },
  {
    id: 8,
    name: 'Plitvice Lakes National Park',
    type: 'nature',
    rating: 4.9,
    price_per_night: 0,
    coordinates: { lat: 44.8654, lng: 15.5820 },
    tags: ['nature', 'hiking', 'photography'],
    description: 'Stunning waterfalls and crystal-clear lakes in a pristine natural setting.',
    interests: ['nature', 'hiking', 'photography'],
    environments: ['forests']
  },
  {
    id: 9,
    name: 'Barcelona Beach Camping',
    type: 'campsite',
    rating: 4.3,
    price_per_night: 32,
    coordinates: { lat: 41.3851, lng: 2.1734 },
    tags: ['beach', 'city', 'culture'],
    description: 'Urban beach camping close to Barcelona\'s attractions and nightlife.',
    interests: ['beach', 'culture', 'events'],
    environments: ['coastal', 'city', 'sunny'],
    amenities: ['electricity', 'water', 'showers', 'wifi', 'toilets']
  },
  {
    id: 10,
    name: 'Rhine Valley Cycling Route',
    type: 'attraction',
    rating: 4.6,
    price_per_night: 0,
    coordinates: { lat: 50.3569, lng: 7.5890 },
    tags: ['cycling', 'nature', 'scenic'],
    description: 'Spectacular cycling route through castles and vineyards along the Rhine.',
    interests: ['cycling', 'nature', 'photography'],
    environments: ['countryside']
  },
  {
    id: 11,
    name: 'Norwegian Fjords Campsite',
    type: 'campsite',
    rating: 4.8,
    price_per_night: 40,
    coordinates: { lat: 60.3913, lng: 5.3221 },
    tags: ['nature', 'mountains', 'scenic'],
    description: 'Breathtaking fjord views with excellent hiking opportunities.',
    interests: ['nature', 'hiking', 'camping', 'photography'],
    environments: ['mountains', 'coastal'],
    amenities: ['electricity', 'water', 'showers', 'toilets']
  },
  {
    id: 12,
    name: 'Amsterdam Canal District',
    type: 'city',
    rating: 4.7,
    price_per_night: 0,
    coordinates: { lat: 52.3676, lng: 4.9041 },
    tags: ['culture', 'city', 'art'],
    description: 'Historic canal district with museums, cafes, and vibrant culture.',
    interests: ['culture', 'art', 'photography'],
    environments: ['city']
  }
];

/**
 * Calculate match score based on user preferences
 */
const calculateMatchScore = (location, preferences) => {
  let score = 70; // Base score

  // Interest matching (30 points possible)
  const interestMatches = location.interests?.filter(interest =>
    preferences.interests?.includes(interest)
  ).length || 0;
  score += Math.min(interestMatches * 10, 30);

  // Environment matching (10 points possible)
  const envMatches = location.environments?.filter(env =>
    preferences.preferred_environment?.includes(env)
  ).length || 0;
  score += Math.min(envMatches * 5, 10);

  // Price matching (10 points possible)
  if (preferences.max_price_per_night === 0) {
    score += location.price_per_night === 0 ? 10 : 0;
  } else if (location.price_per_night <= preferences.max_price_per_night) {
    score += 10;
  }

  // Rating bonus (5 points possible)
  score += location.rating >= 4.5 ? 5 : 0;

  return Math.min(Math.round(score), 99);
};

/**
 * Filter locations based on preferences
 */
const filterLocations = (locations, preferences, filters = {}) => {
  return locations.filter(location => {
    // Price filter
    if (preferences.max_price_per_night === 0 && location.price_per_night > 0) {
      return false;
    }
    if (location.price_per_night > preferences.max_price_per_night) {
      return false;
    }

    // Type filter
    if (filters.type && location.type !== filters.type) {
      return false;
    }

    // Rating filter
    if (filters.minRating && location.rating < filters.minRating) {
      return false;
    }

    // Amenities filter (for campsites)
    if (preferences.preferred_amenities?.length > 0 && location.amenities) {
      const hasRequiredAmenities = preferences.preferred_amenities.every(amenity =>
        location.amenities.includes(amenity)
      );
      if (!hasRequiredAmenities) {
        return false;
      }
    }

    return true;
  });
};

/**
 * Sort locations by different criteria
 */
const sortLocations = (locations, sortBy = 'match') => {
  const sorted = [...locations];

  switch (sortBy) {
    case 'match':
      return sorted.sort((a, b) => b.match_score - a.match_score);
    case 'rating':
      return sorted.sort((a, b) => b.rating - a.rating);
    case 'price_low':
      return sorted.sort((a, b) => a.price_per_night - b.price_per_night);
    case 'price_high':
      return sorted.sort((a, b) => b.price_per_night - a.price_per_night);
    case 'distance':
      return sorted.sort((a, b) => (a.distance_from_start || 0) - (b.distance_from_start || 0));
    default:
      return sorted;
  }
};

/**
 * Calculate distance from a point
 */
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Radius of Earth in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return Math.round(R * c);
};

/**
 * Get location recommendations
 */
export const getRecommendations = async (tripData, filters = {}, sortBy = 'match') => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 800));

  let locations = [...MOCK_LOCATIONS];

  // Calculate distance from start if we have coordinates
  if (tripData.start_coordinates) {
    locations = locations.map(location => ({
      ...location,
      distance_from_start: calculateDistance(
        tripData.start_coordinates.lat,
        tripData.start_coordinates.lng,
        location.coordinates.lat,
        location.coordinates.lng
      )
    }));
  }

  // Filter locations
  locations = filterLocations(locations, tripData, filters);

  // Calculate match scores
  locations = locations.map(location => ({
    ...location,
    match_score: calculateMatchScore(location, tripData)
  }));

  // Sort locations
  locations = sortLocations(locations, sortBy);

  return locations;
};

/**
 * Get a single location by ID
 */
export const getLocationById = async (id) => {
  await new Promise(resolve => setTimeout(resolve, 300));
  return MOCK_LOCATIONS.find(loc => loc.id === id);
};
