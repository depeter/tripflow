import api from './api';
import type { DiscoverLocation } from './discoverService';

export interface Trip {
  id: number;
  user_id: number;
  name: string | null;
  status: 'planning' | 'active' | 'completed' | 'cancelled';
  start_address: string;
  start_latitude: number;
  start_longitude: number;
  end_address: string | null;
  end_latitude: number | null;
  end_longitude: number | null;
  max_distance_km: number | null;
  duration_days: number | null;
  start_date: string | null;
  end_date: string | null;
  waypoints: TripWaypoint[];
  trip_preferences: TripPreferences | null;
  created_at: string;
  updated_at: string;
}

export interface TripWaypoint {
  location_id: number;
  order: number;
  arrival_date?: string;
  departure_date?: string;
  location?: DiscoverLocation;
}

export interface TripPreferences {
  interests: string[];
  activity_level?: 'low' | 'moderate' | 'high';
  budget?: 'budget' | 'mid-range' | 'comfort';
  accommodation_types?: string[];
}

export interface TripStats {
  total_distance_km: number;
  num_stops: number;
  estimated_driving_hours: number;
  estimated_driving_days: number;
}

export interface CreateTripData {
  name?: string;
  start_address: string;
  end_address?: string;
  max_distance_km?: number;
  duration_days?: number;
  trip_preferences?: TripPreferences;
}

export interface WaypointSuggestion {
  id: number;
  name: string;
  location_type: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  score: number;
}

// Create a new trip
export async function createTrip(data: CreateTripData): Promise<Trip> {
  const response = await api.post<Trip>('/trips/', data);
  return response.data;
}

// Get user's trips
export async function getTrips(): Promise<Trip[]> {
  const response = await api.get<Trip[]>('/trips/');
  return response.data;
}

// Get trip by ID
export async function getTrip(tripId: number): Promise<Trip> {
  const response = await api.get<Trip>(`/trips/${tripId}`);
  return response.data;
}

// Add waypoint to trip
export async function addWaypoint(
  tripId: number,
  locationId: number,
  order?: number
): Promise<Trip> {
  const response = await api.post<Trip>(`/trips/${tripId}/waypoints`, {
    location_id: locationId,
    order,
  });
  return response.data;
}

// Remove waypoint from trip
export async function removeWaypoint(
  tripId: number,
  locationId: number
): Promise<Trip> {
  const response = await api.delete<Trip>(`/trips/${tripId}/waypoints/${locationId}`);
  return response.data;
}

// Get waypoint suggestions
export async function suggestWaypoints(
  tripId: number,
  numStops: number = 5
): Promise<WaypointSuggestion[]> {
  const response = await api.post<WaypointSuggestion[]>(
    `/trips/${tripId}/suggest-waypoints`,
    { num_stops: numStops }
  );
  return response.data;
}

// Get trip statistics
export async function getTripStats(tripId: number): Promise<TripStats> {
  const response = await api.get<TripStats>(`/trips/${tripId}/stats`);
  return response.data;
}

// Finalize trip
export async function finalizeTrip(tripId: number, startDate: string): Promise<Trip> {
  const response = await api.post<Trip>(`/trips/${tripId}/finalize`, {
    start_date: startDate,
  });
  return response.data;
}

// Get AI recommendations
export async function getRecommendations(params: {
  near_latitude: number;
  near_longitude: number;
  radius_km: number;
  interests: string[];
  limit?: number;
}): Promise<DiscoverLocation[]> {
  // user_id is extracted from auth token on the backend
  const response = await api.post<DiscoverLocation[]>('/recommendations/', params);
  return response.data;
}

// Delete a trip
export async function deleteTrip(tripId: number): Promise<void> {
  await api.delete(`/trips/${tripId}`);
}
