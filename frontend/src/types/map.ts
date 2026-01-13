import type { DiscoverEvent, DiscoverLocation } from '@/services/discoverService';

export interface MapItem {
  id: number;
  name: string;
  itemType: 'event' | 'location';
  latitude: number;
  longitude: number;
  // Event fields
  category?: string;
  start_datetime?: string;
  end_datetime?: string;
  venue_name?: string;
  // Location fields
  location_type?: string;
  rating?: number | null;
  rating_count?: number | null;
  price_type?: string | null;
  // Common
  description?: string | null;
  address?: string | null;
  city?: string | null;
  distance_km?: number;
  website?: string | null;
  main_image_url?: string | null;
  images?: string[];
  tags?: string[];
  source?: string;
}

// Convert API responses to MapItem
export function eventsToMapItems(events: DiscoverEvent[]): MapItem[] {
  return events.map(e => ({
    id: e.id,
    name: e.name,
    itemType: 'event' as const,
    latitude: e.latitude,
    longitude: e.longitude,
    category: e.category,
    start_datetime: e.start_datetime,
    end_datetime: e.end_datetime || undefined,
    venue_name: e.venue_name || undefined,
    description: e.description,
    address: e.address,
    city: e.city,
    distance_km: e.distance_km,
    website: e.website,
    images: e.images || [],
    tags: e.tags || [],
    source: e.source,
  }));
}

export function locationsToMapItems(locations: DiscoverLocation[]): MapItem[] {
  return locations.map(l => ({
    id: l.id,
    name: l.name,
    itemType: 'location' as const,
    latitude: l.latitude,
    longitude: l.longitude,
    location_type: l.location_type,
    rating: l.rating,
    rating_count: l.rating_count,
    price_type: l.price_type,
    description: l.description,
    address: l.address,
    city: l.city,
    distance_km: l.distance_km,
    website: l.website,
    main_image_url: l.main_image_url,
    images: l.images || [],
    tags: l.tags || [],
    source: l.source,
  }));
}
