export interface Coordinates {
  lat: number;
  lng: number;
}

export interface Location {
  id: string;
  name: string;
  coordinates: Coordinates;
  type: 'poi' | 'event' | 'overnight' | 'viewpoint';
  distance_km?: number;
  detour_km?: number;
  description?: string;
  time?: string;
  price?: string;
  amenities?: string[];
  rating?: number;
  // Additional details
  image?: string;
  city?: string;
  address?: string;
  website?: string;
  category?: string;
}

export interface DayPlanType {
  id: string;
  type: 'exploration' | 'transit' | 'zero';
  title: string;
  total_km: number;
  description: string;
  pois: Location[];
  events: Location[];
  overnight: Location[];
}

export interface Weather {
  temp_c: number;
  condition: string;
  icon: string;
}

export interface TripState {
  current_position: Coordinates | null;
  current_address: string;
  destination: {
    name: string;
    coordinates: Coordinates;
  } | null;
  driving_envelope_km: number;
  max_driving_km: number;
  selected_plan: DayPlanType | null;
  weather: Weather | null;
}
