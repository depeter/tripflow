/**
 * Plan Service - API calls for personalized plan suggestions
 */

import api from './api';

// ============ Types ============

export interface UserPreferencesInput {
  interests: string[];
  preferred_environment: string[];
  accommodation_types: string[];
  travel_pace: 'slow' | 'moderate' | 'fast';
  budget: 'budget' | 'mid-range' | 'comfort';
}

export interface PlanSuggestRequest {
  latitude: number;
  longitude: number;
  destination_latitude?: number;
  destination_longitude?: number;
  destination_name?: string;
  driving_envelope_km: number;
  preferences?: UserPreferencesInput;
  date_start?: string;
  date_end?: string;
  max_plans?: number;
  max_items_per_plan?: number;
}

export interface PlanItemResponse {
  id: string;
  item_type: 'event' | 'location';
  name: string;
  description?: string;
  latitude: number;
  longitude: number;
  distance_km: number;

  // Event-specific
  start_datetime?: string;
  end_datetime?: string;
  price?: number;
  free?: boolean;
  category?: string;
  event_type?: string;
  themes: string[];

  // Location-specific
  location_type?: string;
  rating?: number;
  price_type?: string;
  tags: string[];
  amenities?: Record<string, unknown>;

  // Common
  city?: string;
  address?: string;
  website?: string;
  image?: string;

  // Scoring
  preference_score: number;
  match_reasons: string[];
}

export interface SuggestedPlanResponse {
  id: string;
  plan_type: 'themed' | 'environment' | 'distance' | 'transit';
  title: string;
  description: string;
  icon: string;

  total_km: number;
  estimated_hours: number;

  events: PlanItemResponse[];
  stops: PlanItemResponse[];
  overnight: PlanItemResponse[];

  preference_score: number;
  match_reasons: string[];

  is_transit_plan: boolean;
  progress_toward_destination?: number;
}

export interface PlanSuggestResponse {
  plans: SuggestedPlanResponse[];
  total_plans: number;
  current_location: { latitude: number; longitude: number };
  destination?: {
    latitude: number;
    longitude: number;
    name?: string;
  };
  driving_envelope_km: number;
  personalized: boolean;
  preferences_applied?: UserPreferencesInput;
}

export interface InterestOption {
  id: string;
  name: string;
  icon: string;
}

export interface AvailablePreferences {
  interests: InterestOption[];
  environments: InterestOption[];
  accommodation_types: InterestOption[];
  travel_paces: { id: string; name: string; description: string }[];
  budgets: { id: string; name: string; description: string }[];
}

// ============ API Functions ============

/**
 * Get personalized plan suggestions based on user preferences and location
 */
export async function suggestPlans(
  request: PlanSuggestRequest
): Promise<PlanSuggestResponse> {
  const response = await api.post<PlanSuggestResponse>('/plans/suggest', request);
  return response.data;
}

/**
 * Quick plan suggestions without preferences (simpler endpoint)
 */
export async function suggestPlansQuick(
  latitude: number,
  longitude: number,
  drivingEnvelopeKm: number = 100
): Promise<PlanSuggestResponse> {
  const response = await api.post<PlanSuggestResponse>(
    `/plans/suggest/quick?latitude=${latitude}&longitude=${longitude}&driving_envelope_km=${drivingEnvelopeKm}`
  );
  return response.data;
}

/**
 * Get available interest categories for personalization
 */
export async function getAvailablePreferences(): Promise<AvailablePreferences> {
  const response = await api.get<AvailablePreferences>('/plans/interests');
  return response.data;
}

// ============ Helper Functions ============

/**
 * Convert profile preferences to API format
 */
export function profileToApiPreferences(
  profilePreferences: {
    interests?: { id: string; selected: boolean }[];
    travelStyle?: {
      pace: string;
      environment: string[];
      budget: string;
      accommodation: string[];
    };
  } | null
): UserPreferencesInput | undefined {
  if (!profilePreferences) {
    return undefined;
  }

  // Extract selected interests
  const selectedInterests = (profilePreferences.interests || [])
    .filter((i) => i.selected)
    .map((i) => i.id);

  const style = profilePreferences.travelStyle;

  // Only return preferences if something is selected
  if (
    selectedInterests.length === 0 &&
    (!style || (style.environment.length === 0 && style.accommodation.length === 0))
  ) {
    return undefined;
  }

  return {
    interests: selectedInterests,
    preferred_environment: style?.environment || [],
    accommodation_types: style?.accommodation || [],
    travel_pace: (style?.pace as 'slow' | 'moderate' | 'fast') || 'moderate',
    budget: (style?.budget as 'budget' | 'mid-range' | 'comfort') || 'mid-range',
  };
}

/**
 * Build request from current trip state
 */
export function buildPlanRequest(
  currentPosition: { latitude: number; longitude: number },
  drivingEnvelopeKm: number,
  destination?: { name: string; coordinates: { latitude: number; longitude: number } } | null,
  preferences?: UserPreferencesInput
): PlanSuggestRequest {
  const request: PlanSuggestRequest = {
    latitude: currentPosition.latitude,
    longitude: currentPosition.longitude,
    driving_envelope_km: drivingEnvelopeKm,
    preferences,
  };

  // Add destination for transit mode
  if (destination) {
    request.destination_latitude = destination.coordinates.latitude;
    request.destination_longitude = destination.coordinates.longitude;
    request.destination_name = destination.name;
  }

  // Set date range (next 7 days)
  const now = new Date();
  const nextWeek = new Date(now);
  nextWeek.setDate(nextWeek.getDate() + 7);

  request.date_start = now.toISOString();
  request.date_end = nextWeek.toISOString();

  return request;
}
