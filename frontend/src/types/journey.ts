import type { Coordinates, Location } from './trip';

export interface JourneyWaypoint {
  id: string;
  name: string;
  coordinates: Coordinates;
  type: 'start' | 'destination' | 'mustSee' | 'visited' | 'skipped';
  description?: string;
  distance_from_start_km: number;
  estimated_day?: number;
  rating?: number;
  tags?: string[];
  visited_date?: string;
}

export interface Journey {
  id: string;
  name: string;
  start: JourneyWaypoint;
  destination: JourneyWaypoint;
  waypoints: JourneyWaypoint[];
  total_distance_km: number;
  progress_km: number;
  current_day: number;
  started_date?: string;
}

export interface JourneyStats {
  days_traveled: number;
  distance_covered_km: number;
  distance_remaining_km: number;
  places_visited: number;
  places_remaining: number;
  avg_km_per_day: number;
}
