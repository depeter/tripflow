import api from './api';

export interface DiscoverLocation {
  id: number;
  name: string;
  description: string | null;
  location_type: string;
  latitude: number;
  longitude: number;
  address: string | null;
  city: string | null;
  country: string | null;
  rating: number | null;
  rating_count: number | null;
  price_type: string | null;
  price_min: number | null;
  price_max: number | null;
  price_currency: string | null;
  website: string | null;
  main_image_url: string | null;
  images: string[];
  tags: string[];
  source: string;
  distance_km: number;
  amenities?: Record<string, boolean>;
  features?: Record<string, boolean>;
}

export interface DiscoverEvent {
  id: number;
  name: string;
  description: string | null;
  category: string;
  start_datetime: string;
  end_datetime: string | null;
  all_day: boolean;
  venue_name: string | null;
  address: string | null;
  city: string | null;
  country: string | null;
  latitude: number;
  longitude: number;
  price: number | null;
  currency: string | null;
  free: boolean;
  website: string | null;
  images: string[];
  tags: string[];
  organizer: string | null;
  event_type: string | null;
  themes: string[];
  source: string;
  distance_km: number;
  score: number | null;  // Quality/relevance score (0-1, higher is better)
}

export interface DiscoverResponse {
  events: DiscoverEvent[];
  locations: DiscoverLocation[];
  total_count: number;
  search_center: {
    latitude: number;
    longitude: number;
  };
  radius_km: number;
}

export interface DiscoverFilters {
  latitude: number;
  longitude: number;
  radius_km: number;
  item_types?: ('events' | 'locations')[];
  search_text?: string;
  limit?: number;
  // Route-based search (corridor mode)
  destination_latitude?: number;
  destination_longitude?: number;
  corridor_width_km?: number;
  max_distance_km?: number;
  // Filters
  event_filters?: {
    categories?: string[];
    date_start?: string;
    date_end?: string;
    free_only?: boolean;
    price_min?: number;
    price_max?: number;
    time_of_day?: string[];
  };
  location_filters?: {
    location_types?: string[];
    min_rating?: number;
    price_types?: string[];
    amenities?: string[];
    features?: string[];
    is_24_7?: boolean;
    no_booking_required?: boolean;
    min_capacity?: number;
  };
}

export interface NearbyFilters {
  latitude: number;
  longitude: number;
  radius_km: number;
  location_types?: string[];
  limit?: number;
}

// Discover events and locations in an area
export async function discover(filters: DiscoverFilters): Promise<DiscoverResponse> {
  const response = await api.post<DiscoverResponse>('/discover', filters);
  return response.data;
}

// Get nearby locations
export async function getNearbyLocations(filters: NearbyFilters): Promise<DiscoverLocation[]> {
  const response = await api.post<DiscoverLocation[]>('/locations/nearby', filters);
  return response.data;
}

// Get location by ID
export async function getLocation(locationId: number): Promise<DiscoverLocation> {
  const response = await api.get<DiscoverLocation>(`/locations/${locationId}`);
  return response.data;
}

// Search locations
export async function searchLocations(params: {
  query?: string;
  location_types?: string[];
  amenities?: string[];
  min_rating?: number;
  max_price?: number;
  limit?: number;
}): Promise<DiscoverLocation[]> {
  const response = await api.post<DiscoverLocation[]>('/locations/search', params);
  return response.data;
}

// Geocode address to coordinates
export async function geocodeAddress(address: string): Promise<{
  latitude: number;
  longitude: number;
  display_name: string;
}> {
  const response = await api.post('/locations/geocode', { address });
  return response.data;
}

// Reverse geocode coordinates to address
export async function reverseGeocode(latitude: number, longitude: number): Promise<{
  address: string;
  city: string;
  country: string;
}> {
  const response = await api.get('/locations/reverse-geocode', {
    params: { latitude, longitude },
  });
  return response.data;
}

// Get discovery categories
export async function getCategories(): Promise<string[]> {
  const response = await api.get<string[]>('/discover/categories');
  return response.data;
}

// Get discovery statistics
export async function getDiscoverStats(): Promise<{
  total_events: number;
  total_locations: number;
  by_category: Record<string, number>;
}> {
  const response = await api.get('/discover/stats');
  return response.data;
}
