export interface Interest {
  id: string;
  name: string;
  icon: string;
  selected: boolean;
}

export interface TravelStyle {
  pace: 'slow' | 'moderate' | 'fast';
  environment: ('nature' | 'cities' | 'villages' | 'coast')[];
  budget: 'budget' | 'mid-range' | 'comfort';
  accommodation: ('camping' | 'wild' | 'stellplatz' | 'hotel')[];
}

export interface VehicleInfo {
  type: 'campervan' | 'motorhome' | 'caravan' | 'car-tent';
  length_m?: number;
  height_m?: number;
  weight_kg?: number;
}

export interface UserProfile {
  name: string;
  avatar?: string;
  language?: string;  // Language code from available languages API
  interests: Interest[];
  travelStyle: TravelStyle;
  vehicle: VehicleInfo;
  homeBase?: {
    name: string;
    coordinates: { lat: number; lng: number };
  };
}
