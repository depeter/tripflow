'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  getCurrentPosition,
  getWeather,
  calculateDistance,
  type Position,
  type WeatherData,
} from '@/services/locationService';
import { reverseGeocode, type DiscoverLocation, type DiscoverEvent } from '@/services/discoverService';
import type { DayPlanType, Location } from '@/types/trip';
import { getTrips, type Trip } from '@/services/tripService';
import {
  suggestPlans,
  buildPlanRequest,
  profileToApiPreferences,
  type SuggestedPlanResponse,
  type PlanItemResponse,
} from '@/services/planService';
import { getProfilePreferences, isAuthenticated } from '@/services/authService';

export interface TripState {
  // Current position
  currentPosition: Position | null;
  currentAddress: string;
  isLoadingPosition: boolean;
  positionError: string | null;

  // Active trip and destination (fetched from backend)
  activeTrip: Trip | null;
  destination: {
    name: string;
    coordinates: Position;
  } | null;
  distanceToDestination: number | null;

  // Weather
  weather: WeatherData | null;

  // Driving preferences
  drivingEnvelopeKm: number;
  maxDrivingKm: number;

  // Nearby data (legacy - kept for backward compatibility)
  nearbyEvents: DiscoverEvent[];
  nearbyLocations: DiscoverLocation[];
  isLoadingNearby: boolean;

  // Day plans
  suggestedPlans: DayPlanType[];
  selectedPlanId: string | null;

  // Personalization
  isPersonalized: boolean;
  isLoadingPlans: boolean;
}

export function useTripState() {
  const [state, setState] = useState<TripState>({
    currentPosition: null,
    currentAddress: 'Locating...',
    isLoadingPosition: true,
    positionError: null,
    activeTrip: null,
    destination: null,
    distanceToDestination: null,
    weather: null,
    drivingEnvelopeKm: 60,
    maxDrivingKm: 600,
    nearbyEvents: [],
    nearbyLocations: [],
    isLoadingNearby: false,
    suggestedPlans: [],
    selectedPlanId: null,
    isPersonalized: false,
    isLoadingPlans: false,
  });

  // Get current position on mount
  useEffect(() => {
    async function fetchPosition() {
      try {
        const position = await getCurrentPosition();

        // Get address for position
        let address = 'Unknown location';
        try {
          const geo = await reverseGeocode(position.latitude, position.longitude);
          address = geo.city ? `${geo.city}, ${geo.country}` : geo.address;
        } catch (e) {
          console.error('Reverse geocode failed:', e);
        }

        // Calculate distance to destination
        let distance: number | null = null;
        if (state.destination) {
          distance = calculateDistance(position, state.destination.coordinates);
        }

        setState((prev) => ({
          ...prev,
          currentPosition: position,
          currentAddress: address,
          distanceToDestination: distance,
          isLoadingPosition: false,
          positionError: null,
        }));
      } catch (error) {
        console.error('Failed to get position:', error);
        // No fallback location - require user to grant permission or set location
        setState((prev) => ({
          ...prev,
          currentPosition: null,
          currentAddress: 'Location unavailable',
          distanceToDestination: null,
          isLoadingPosition: false,
          positionError: 'Location access required. Please enable location services or set your location in Profile.',
        }));
      }
    }

    fetchPosition();
  }, []);

  // Fetch active trip on mount
  useEffect(() => {
    async function fetchActiveTrip() {
      try {
        const trips = await getTrips();
        const activeTrip = trips.find(t => t.status === 'active') || trips[0] || null;

        if (activeTrip && activeTrip.end_latitude && activeTrip.end_longitude) {
          const destination = {
            name: activeTrip.end_address || 'Destination',
            coordinates: {
              latitude: activeTrip.end_latitude,
              longitude: activeTrip.end_longitude
            },
          };

          setState((prev) => ({
            ...prev,
            activeTrip,
            destination,
            distanceToDestination: prev.currentPosition
              ? calculateDistance(prev.currentPosition, destination.coordinates)
              : null,
          }));
        } else {
          setState((prev) => ({
            ...prev,
            activeTrip: activeTrip || null,
            destination: null,
            distanceToDestination: null,
          }));
        }
      } catch (error) {
        console.error('Failed to fetch active trip:', error);
        // No trips - that's fine, user can create one
      }
    }

    fetchActiveTrip();
  }, []);

  // Fetch weather when position changes
  useEffect(() => {
    if (!state.currentPosition) return;

    async function fetchWeather() {
      try {
        const weather = await getWeather(
          state.currentPosition!.latitude,
          state.currentPosition!.longitude
        );
        setState((prev) => ({ ...prev, weather }));
      } catch (error) {
        console.error('Failed to fetch weather:', error);
      }
    }

    fetchWeather();
  }, [state.currentPosition?.latitude, state.currentPosition?.longitude]);

  // Fetch personalized plans from backend when position, destination, or driving envelope changes
  useEffect(() => {
    if (!state.currentPosition) return;

    async function fetchPersonalizedPlans() {
      setState((prev) => ({ ...prev, isLoadingPlans: true, isLoadingNearby: true }));

      try {
        // Try to get user preferences if authenticated
        let preferences = undefined;
        if (isAuthenticated()) {
          try {
            const profilePrefs = await getProfilePreferences();
            preferences = profileToApiPreferences(profilePrefs);
          } catch (e) {
            console.log('Could not fetch user preferences, using defaults');
          }
        }

        // Build request for backend
        const request = buildPlanRequest(
          state.currentPosition!,
          state.drivingEnvelopeKm,
          state.destination,
          preferences
        );

        // Fetch personalized plans from backend
        const response = await suggestPlans(request);

        // Convert API plans to UI format
        const uiPlans: DayPlanType[] = response.plans.map(apiPlanToUIPlan);

        setState((prev) => ({
          ...prev,
          suggestedPlans: uiPlans,
          isPersonalized: response.personalized,
          isLoadingPlans: false,
          isLoadingNearby: false,
        }));
      } catch (error) {
        console.error('Failed to fetch personalized plans:', error);
        // Fall back to empty plans on error
        setState((prev) => ({
          ...prev,
          suggestedPlans: [],
          isPersonalized: false,
          isLoadingPlans: false,
          isLoadingNearby: false,
        }));
      }
    }

    fetchPersonalizedPlans();
  }, [state.currentPosition?.latitude, state.currentPosition?.longitude, state.destination, state.drivingEnvelopeKm]);

  // Set driving envelope
  const setDrivingEnvelope = useCallback((km: number) => {
    setState((prev) => ({ ...prev, drivingEnvelopeKm: km }));
  }, []);

  // Select a plan
  const selectPlan = useCallback((planId: string | null) => {
    setState((prev) => ({ ...prev, selectedPlanId: planId }));
  }, []);

  // Set destination
  const setDestination = useCallback((name: string, coordinates: Position) => {
    setState((prev) => ({
      ...prev,
      destination: { name, coordinates },
      distanceToDestination: prev.currentPosition
        ? calculateDistance(prev.currentPosition, coordinates)
        : null,
    }));
  }, []);

  // Remove an item from a plan (and track the removal)
  const removeItemFromPlan = useCallback((planId: string, itemType: 'event' | 'location', itemId: string) => {
    setState((prev) => {
      const updatedPlans = prev.suggestedPlans.map((plan) => {
        if (plan.id !== planId) return plan;

        // Remove the item from the appropriate array based on itemType
        if (itemType === 'event') {
          return {
            ...plan,
            events: plan.events.filter((e) => e.id !== itemId),
          };
        } else {
          // Location could be in pois or overnight
          return {
            ...plan,
            pois: plan.pois.filter((p) => p.id !== itemId),
            overnight: plan.overnight.filter((o) => o.id !== itemId),
          };
        }
      });

      return { ...prev, suggestedPlans: updatedPlans };
    });
  }, []);

  return {
    ...state,
    setDrivingEnvelope,
    selectPlan,
    setDestination,
    removeItemFromPlan,
  };
}

// Helper functions to convert API types to UI types
function eventToLocation(event: DiscoverEvent): Location {
  return {
    id: `event-${event.id}`,
    name: event.name,
    coordinates: { lat: event.latitude, lng: event.longitude },
    type: 'event',
    distance_km: event.distance_km,
    time: event.start_datetime
      ? new Date(event.start_datetime).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
        })
      : undefined,
    description: event.description || undefined,
    price: event.free ? 'Free' : event.price ? `€${event.price}` : undefined,
    image: event.images?.[0] || undefined,
    city: event.city || undefined,
    address: event.address || event.venue_name || undefined,
    website: event.website || undefined,
    category: event.category || event.event_type || undefined,
  };
}

function locationToPOI(location: DiscoverLocation): Location {
  return {
    id: `loc-${location.id}`,
    name: location.name,
    coordinates: { lat: location.latitude, lng: location.longitude },
    type: 'poi',
    distance_km: location.distance_km,
    description: location.description || undefined,
    rating: location.rating || undefined,
    image: location.main_image_url || location.images?.[0] || undefined,
    city: location.city || undefined,
    address: location.address || undefined,
    website: location.website || undefined,
    category: location.location_type || undefined,
  };
}

function locationToOvernightLocation(location: DiscoverLocation): Location {
  return {
    id: `overnight-${location.id}`,
    name: location.name,
    coordinates: { lat: location.latitude, lng: location.longitude },
    type: 'overnight',
    distance_km: location.distance_km,
    price: location.price_type === 'free'
      ? 'Free'
      : location.price_min
      ? `€${location.price_min}${location.price_max ? `-${location.price_max}` : ''}`
      : undefined,
    amenities: location.tags?.slice(0, 3),
    rating: location.rating || undefined,
    image: location.main_image_url || location.images?.[0] || undefined,
    city: location.city || undefined,
    address: location.address || undefined,
    website: location.website || undefined,
    category: location.location_type || undefined,
  };
}

// Convert API plan item to UI Location type
function apiItemToLocation(item: PlanItemResponse): Location {
  const isEvent = item.item_type === 'event';
  const isOvernight = item.location_type && ['CAMPSITE', 'PARKING', 'REST_AREA', 'HOTEL'].includes(item.location_type);

  return {
    id: item.id,
    name: item.name,
    coordinates: { lat: item.latitude, lng: item.longitude },
    type: isEvent ? 'event' : isOvernight ? 'overnight' : 'poi',
    distance_km: item.distance_km,
    description: item.description || undefined,
    time: item.start_datetime
      ? new Date(item.start_datetime).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
        })
      : undefined,
    price: item.free
      ? 'Free'
      : item.price
      ? `€${item.price}`
      : item.price_type === 'free'
      ? 'Free'
      : undefined,
    rating: item.rating || undefined,
    image: item.image || undefined,
    city: item.city || undefined,
    address: item.address || undefined,
    website: item.website || undefined,
    category: item.category || item.event_type || item.location_type || undefined,
    amenities: item.tags?.slice(0, 3),
  };
}

// Convert API plan response to UI DayPlanType
function apiPlanToUIPlan(plan: SuggestedPlanResponse): DayPlanType {
  // Map plan_type to UI type
  let uiType: 'exploration' | 'transit' | 'zero' = 'exploration';
  if (plan.plan_type === 'transit' || plan.is_transit_plan) {
    uiType = 'transit';
  } else if (plan.total_km === 0) {
    uiType = 'zero';
  }

  return {
    id: plan.id,
    type: uiType,
    title: `${plan.icon} ${plan.title}`,
    total_km: plan.total_km,
    description: plan.description,
    pois: plan.stops.map(apiItemToLocation),
    events: plan.events.map(apiItemToLocation),
    overnight: plan.overnight.map(apiItemToLocation),
  };
}
