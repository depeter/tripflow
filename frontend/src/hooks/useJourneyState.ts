'use client';

import { useState, useEffect, useCallback } from 'react';
import { getTrips, getTrip, getTripStats, deleteTrip as deleteTripApi, type Trip, type TripStats } from '@/services/tripService';
import { getCurrentPosition, type Position } from '@/services/locationService';
import type { Journey, JourneyWaypoint, JourneyStats } from '@/types/journey';

export interface JourneyState {
  journey: Journey | null;
  stats: JourneyStats | null;
  currentPosition: Position | null;
  isLoading: boolean;
  error: string | null;
  trips: Trip[];
  activeTripId: number | null;
}

// Convert Trip from API to Journey for display
function tripToJourney(trip: Trip, currentPosition: Position | null): Journey {
  // Calculate progress based on current position
  let progressKm = 0;
  if (currentPosition && trip.start_latitude && trip.start_longitude) {
    // Simple distance calculation from start
    const R = 6371;
    const dLat = toRad(currentPosition.latitude - trip.start_latitude);
    const dLon = toRad(currentPosition.longitude - trip.start_longitude);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(trip.start_latitude)) *
        Math.cos(toRad(currentPosition.latitude)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    progressKm = Math.round(R * c);
  }

  // Calculate current day
  const startDate = trip.start_date ? new Date(trip.start_date) : new Date();
  const today = new Date();
  const daysDiff = Math.floor((today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
  const currentDay = Math.max(1, daysDiff + 1);

  // Convert waypoints
  const waypoints: JourneyWaypoint[] = (trip.waypoints || []).map((wp, index) => {
    const loc = wp.location;
    return {
      id: `wp-${wp.location_id}`,
      name: loc?.name || `Waypoint ${index + 1}`,
      coordinates: {
        lat: loc?.latitude || 0,
        lng: loc?.longitude || 0,
      },
      type: wp.departure_date ? 'visited' : 'mustSee',
      description: loc?.description || undefined,
      distance_from_start_km: loc?.distance_km || (index + 1) * 100,
      rating: loc?.rating || undefined,
      tags: loc?.tags?.slice(0, 3),
      visited_date: wp.departure_date || undefined,
    };
  });

  // Calculate total distance
  const totalDistanceKm = trip.max_distance_km ||
    (trip.end_latitude && trip.end_longitude && trip.start_latitude && trip.start_longitude
      ? calculateDistance(
          { latitude: trip.start_latitude, longitude: trip.start_longitude },
          { latitude: trip.end_latitude, longitude: trip.end_longitude }
        )
      : 1000);

  return {
    id: `trip-${trip.id}`,
    name: trip.name || 'My Journey',
    start: {
      id: 'start',
      name: trip.start_address || 'Starting Point',
      coordinates: {
        lat: trip.start_latitude,
        lng: trip.start_longitude,
      },
      type: 'start',
      distance_from_start_km: 0,
    },
    destination: {
      id: 'destination',
      name: trip.end_address || 'Destination',
      coordinates: {
        lat: trip.end_latitude || 0,
        lng: trip.end_longitude || 0,
      },
      type: 'destination',
      distance_from_start_km: totalDistanceKm,
    },
    waypoints,
    total_distance_km: totalDistanceKm,
    progress_km: Math.min(progressKm, totalDistanceKm),
    current_day: currentDay,
    started_date: trip.start_date || undefined,
  };
}

// Convert TripStats from API to JourneyStats for display
function tripStatsToJourneyStats(
  tripStats: TripStats,
  trip: Trip,
  journey: Journey
): JourneyStats {
  const placesVisited = journey.waypoints.filter(w => w.type === 'visited').length;
  const placesRemaining = journey.waypoints.filter(w => w.type === 'mustSee').length;

  return {
    days_traveled: journey.current_day,
    distance_covered_km: journey.progress_km,
    distance_remaining_km: Math.max(0, journey.total_distance_km - journey.progress_km),
    places_visited: placesVisited,
    places_remaining: placesRemaining,
    avg_km_per_day: journey.current_day > 0
      ? Math.round(journey.progress_km / journey.current_day)
      : 0,
  };
}

function toRad(deg: number): number {
  return deg * (Math.PI / 180);
}

function calculateDistance(from: Position, to: Position): number {
  const R = 6371;
  const dLat = toRad(to.latitude - from.latitude);
  const dLon = toRad(to.longitude - from.longitude);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(from.latitude)) *
      Math.cos(toRad(to.latitude)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

export function useJourneyState(tripId?: number) {
  const [state, setState] = useState<JourneyState>({
    journey: null,
    stats: null,
    currentPosition: null,
    isLoading: true,
    error: null,
    trips: [],
    activeTripId: tripId || null,
  });

  // Get current position
  useEffect(() => {
    async function fetchPosition() {
      try {
        const position = await getCurrentPosition();
        setState(prev => ({ ...prev, currentPosition: position }));
      } catch (error) {
        // No fallback - user must enable location or set it in profile
        console.warn('Location access denied');
      }
    }
    fetchPosition();
  }, []);

  // Fetch trips and active journey
  useEffect(() => {
    async function fetchJourney() {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      try {
        // Get all trips
        const trips = await getTrips();

        // Find active trip or use specified tripId
        let activeTrip: Trip | null = null;

        if (tripId) {
          activeTrip = await getTrip(tripId);
        } else {
          // Find the most recent active trip
          activeTrip = trips.find(t => t.status === 'active') || trips[0] || null;
        }

        if (!activeTrip) {
          // No active trip - show empty state
          setState(prev => ({
            ...prev,
            journey: null,
            stats: null,
            trips,
            isLoading: false,
            error: null,
          }));
          return;
        }

        // Get trip stats
        let tripStats: TripStats | null = null;
        try {
          tripStats = await getTripStats(activeTrip.id);
        } catch (e) {
          // Stats might not be available
          console.warn('Could not fetch trip stats:', e);
        }

        // Convert to journey format
        const journey = tripToJourney(activeTrip, state.currentPosition);
        const stats = tripStats
          ? tripStatsToJourneyStats(tripStats, activeTrip, journey)
          : {
              days_traveled: journey.current_day,
              distance_covered_km: journey.progress_km,
              distance_remaining_km: journey.total_distance_km - journey.progress_km,
              places_visited: journey.waypoints.filter(w => w.type === 'visited').length,
              places_remaining: journey.waypoints.filter(w => w.type === 'mustSee').length,
              avg_km_per_day: journey.current_day > 0
                ? Math.round(journey.progress_km / journey.current_day)
                : 0,
            };

        setState(prev => ({
          ...prev,
          journey,
          stats,
          trips,
          activeTripId: activeTrip!.id,
          isLoading: false,
          error: null,
        }));
      } catch (error) {
        console.error('Failed to fetch journey:', error);
        // Show error state
        setState(prev => ({
          ...prev,
          journey: null,
          stats: null,
          isLoading: false,
          error: 'Failed to load trips. Please try again.',
        }));
      }
    }

    fetchJourney();
  }, [tripId, state.currentPosition]);

  // Mark waypoint as visited
  const markVisited = useCallback((waypointId: string) => {
    setState(prev => {
      if (!prev.journey) return prev;

      const updatedWaypoints = prev.journey.waypoints.map(w =>
        w.id === waypointId
          ? { ...w, type: 'visited' as const, visited_date: new Date().toISOString().split('T')[0] }
          : w
      );

      const newJourney = { ...prev.journey, waypoints: updatedWaypoints };
      const placesVisited = updatedWaypoints.filter(w => w.type === 'visited').length;
      const placesRemaining = updatedWaypoints.filter(w => w.type === 'mustSee').length;

      return {
        ...prev,
        journey: newJourney,
        stats: prev.stats
          ? {
              ...prev.stats,
              places_visited: placesVisited,
              places_remaining: placesRemaining,
            }
          : null,
      };
    });

    // TODO: Call API to persist the change
  }, []);

  // Mark waypoint as skipped
  const markSkipped = useCallback((waypointId: string) => {
    setState(prev => {
      if (!prev.journey) return prev;

      const updatedWaypoints = prev.journey.waypoints.map(w =>
        w.id === waypointId ? { ...w, type: 'skipped' as const } : w
      );

      const newJourney = { ...prev.journey, waypoints: updatedWaypoints };
      const placesRemaining = updatedWaypoints.filter(w => w.type === 'mustSee').length;

      return {
        ...prev,
        journey: newJourney,
        stats: prev.stats
          ? {
              ...prev.stats,
              places_remaining: placesRemaining,
            }
          : null,
      };
    });

    // TODO: Call API to persist the change
  }, []);

  // Select a different trip
  const selectTrip = useCallback((newTripId: number) => {
    setState(prev => ({ ...prev, activeTripId: newTripId }));
  }, []);

  // Refetch trips from API
  const refetchTrips = useCallback(async () => {
    try {
      const trips = await getTrips();
      setState(prev => ({ ...prev, trips }));
      return trips;
    } catch (error) {
      console.error('Failed to refetch trips:', error);
      return state.trips;
    }
  }, [state.trips]);

  // Delete a trip
  const deleteTrip = useCallback(async (tripIdToDelete: number) => {
    try {
      await deleteTripApi(tripIdToDelete);

      // Refetch trips to update the list
      const updatedTrips = await getTrips();

      // If we deleted the active trip, clear the journey or select another
      if (state.activeTripId === tripIdToDelete) {
        const newActiveTrip = updatedTrips.find(t => t.status === 'active') || updatedTrips[0] || null;

        if (newActiveTrip) {
          const journey = tripToJourney(newActiveTrip, state.currentPosition);
          setState(prev => ({
            ...prev,
            trips: updatedTrips,
            activeTripId: newActiveTrip.id,
            journey,
          }));
        } else {
          setState(prev => ({
            ...prev,
            trips: updatedTrips,
            activeTripId: null,
            journey: null,
            stats: null,
          }));
        }
      } else {
        setState(prev => ({ ...prev, trips: updatedTrips }));
      }

      return true;
    } catch (error) {
      console.error('Failed to delete trip:', error);
      throw error;
    }
  }, [state.activeTripId, state.currentPosition]);

  return {
    ...state,
    markVisited,
    markSkipped,
    selectTrip,
    refetchTrips,
    deleteTrip,
  };
}
