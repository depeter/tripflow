'use client';

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import dynamic from 'next/dynamic';
import {
  Search,
  Filter,
  X,
  Loader2,
  Calendar,
  Tent,
  Castle,
  MapPin,
  Star,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Sun,
  Sunset,
  Moon,
  Sunrise,
  Wifi,
  Zap,
  Droplets,
  Car,
  Trash2,
  DollarSign,
  Layers,
  Navigation,
  Eye,
  EyeOff,
  List,
  PanelRightClose,
  PanelRightOpen,
} from 'lucide-react';
import {
  discover,
  type DiscoverEvent,
  type DiscoverLocation,
  type DiscoverFilters,
} from '@/services/discoverService';
import { getCurrentPosition, type Position } from '@/services/locationService';
import { type MapItem, eventsToMapItems, locationsToMapItems } from '@/types/map';
import type L from 'leaflet';

// Dynamically import the map component (no SSR for Leaflet)
const MapExplore = dynamic(() => import('@/components/MapExplore'), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full flex items-center justify-center bg-zinc-900">
      <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
    </div>
  ),
});

// Dynamically import the sidebar component
const MapSidebar = dynamic(() => import('@/components/MapSidebar'), {
  ssr: false,
});

// Filter constants
const ITEM_TYPES = [
  { id: 'all', label: 'All', icon: Layers },
  { id: 'events', label: 'Events', icon: Calendar },
  { id: 'locations', label: 'Places', icon: Castle },
];

const EVENT_CATEGORIES = [
  'FESTIVAL', 'CONCERT', 'SPORTS', 'MARKET', 'EXHIBITION',
  'THEATER', 'CULTURAL', 'FOOD', 'OUTDOOR'
];

const LOCATION_TYPES = [
  { id: 'CAMPSITE', label: 'Campsite', icon: Tent },
  { id: 'PARKING', label: 'Parking', icon: Car },
  { id: 'REST_AREA', label: 'Rest Area' },
  { id: 'SERVICE_AREA', label: 'Service Area' },
  { id: 'POI', label: 'Point of Interest', icon: MapPin },
  { id: 'ATTRACTION', label: 'Attraction', icon: Castle },
  { id: 'RESTAURANT', label: 'Restaurant' },
  { id: 'HOTEL', label: 'Hotel' },
];

const RATING_OPTIONS = [
  { value: null, label: 'Any' },
  { value: 3, label: '3+' },
  { value: 3.5, label: '3.5+' },
  { value: 4, label: '4+' },
  { value: 4.5, label: '4.5+' },
];

const AMENITIES = [
  { id: 'wifi', label: 'WiFi', icon: Wifi },
  { id: 'electricity', label: 'Electricity', icon: Zap },
  { id: 'showers', label: 'Showers', icon: Droplets },
  { id: 'parking', label: 'Parking', icon: Car },
  { id: 'toilets', label: 'Toilets', icon: Droplets },
  { id: 'drinking_water', label: 'Water', icon: Droplets },
  { id: 'waste_disposal', label: 'Waste', icon: Trash2 },
];

const TIME_OF_DAY = [
  { id: 'morning', label: 'Morning', icon: Sunrise },
  { id: 'afternoon', label: 'Afternoon', icon: Sun },
  { id: 'evening', label: 'Evening', icon: Sunset },
  { id: 'night', label: 'Night', icon: Moon },
];

interface MapFilters {
  itemType: 'all' | 'events' | 'locations';
  searchRadius: number;
  // Events
  eventCategories: string[];
  eventFreeOnly: boolean;
  eventDateStart: string;
  eventDateEnd: string;
  eventTimeOfDay: string[];
  // Locations
  locationTypes: string[];
  locationMinRating: number | null;
  locationAmenities: string[];
  locationIs24x7: boolean;
}

const defaultFilters: MapFilters = {
  itemType: 'all',
  searchRadius: 60, // 60km default view
  eventCategories: [],
  eventFreeOnly: false,
  eventDateStart: '',
  eventDateEnd: '',
  eventTimeOfDay: [],
  locationTypes: [],
  locationMinRating: null,
  locationAmenities: [],
  locationIs24x7: false,
};

// Default center: Belgium region
const DEFAULT_CENTER: [number, number] = [50.85, 4.35];
const DEFAULT_ZOOM = 9;

export default function MapPage() {
  // Map state
  const [center, setCenter] = useState<[number, number]>(DEFAULT_CENTER);
  const [zoom, setZoom] = useState(DEFAULT_ZOOM);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [searchCenter, setSearchCenter] = useState<{ lat: number; lng: number } | null>(null);

  // Debounce ref for map move handler
  const moveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Data state
  const [events, setEvents] = useState<DiscoverEvent[]>([]);
  const [locations, setLocations] = useState<DiscoverLocation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [filters, setFilters] = useState<MapFilters>(defaultFilters);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedItem, setSelectedItem] = useState<MapItem | null>(null);

  // Layer visibility
  const [showEvents, setShowEvents] = useState(true);
  const [showLocations, setShowLocations] = useState(true);

  // Results sidebar visibility (desktop: shown by default, mobile: hidden)
  const [showResultsSidebar, setShowResultsSidebar] = useState(true);

  // Mobile bottom sheet state
  const [mobileSheetExpanded, setMobileSheetExpanded] = useState(false);

  // Get user location on mount
  useEffect(() => {
    async function getUserLocation() {
      try {
        const pos = await getCurrentPosition();
        setUserLocation({ lat: pos.latitude, lng: pos.longitude });
        setSearchCenter({ lat: pos.latitude, lng: pos.longitude });
        setCenter([pos.latitude, pos.longitude]);
      } catch (err) {
        console.warn('Could not get user location, using default');
        // Set default search center if no user location
        setSearchCenter({ lat: DEFAULT_CENTER[0], lng: DEFAULT_CENTER[1] });
      }
    }
    getUserLocation();
  }, []);

  // Debounced handler for map move events
  const handleMoveEnd = useCallback((bounds: L.LatLngBounds, newCenter: L.LatLng, newZoom: number) => {
    // Clear any pending timeout
    if (moveTimeoutRef.current) {
      clearTimeout(moveTimeoutRef.current);
    }

    // Debounce the search center update by 500ms
    moveTimeoutRef.current = setTimeout(() => {
      setSearchCenter({ lat: newCenter.lat, lng: newCenter.lng });
    }, 500);
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (moveTimeoutRef.current) {
        clearTimeout(moveTimeoutRef.current);
      }
    };
  }, []);

  // Fetch data
  const fetchData = useCallback(async () => {
    // Use searchCenter (from map drag), fall back to userLocation, then default center
    const effectiveCenter = searchCenter || userLocation || { lat: center[0], lng: center[1] };

    setIsLoading(true);
    setError(null);

    try {
      const apiFilters: DiscoverFilters = {
        latitude: effectiveCenter.lat,
        longitude: effectiveCenter.lng,
        radius_km: filters.searchRadius,
        limit: 500, // More items for map view
      };

      // Set item types
      if (filters.itemType === 'events') {
        apiFilters.item_types = ['events'];
      } else if (filters.itemType === 'locations') {
        apiFilters.item_types = ['locations'];
      }

      // Event filters
      if (filters.eventCategories.length > 0) {
        apiFilters.event_filters = {
          ...apiFilters.event_filters,
          categories: filters.eventCategories,
        };
      }
      if (filters.eventFreeOnly) {
        apiFilters.event_filters = {
          ...apiFilters.event_filters,
          free_only: true,
        };
      }
      if (filters.eventDateStart) {
        apiFilters.event_filters = {
          ...apiFilters.event_filters,
          date_start: filters.eventDateStart,
        };
      }
      if (filters.eventDateEnd) {
        apiFilters.event_filters = {
          ...apiFilters.event_filters,
          date_end: filters.eventDateEnd,
        };
      }
      if (filters.eventTimeOfDay.length > 0) {
        apiFilters.event_filters = {
          ...apiFilters.event_filters,
          time_of_day: filters.eventTimeOfDay,
        };
      }

      // Location filters
      if (filters.locationTypes.length > 0) {
        apiFilters.location_filters = {
          ...apiFilters.location_filters,
          location_types: filters.locationTypes,
        };
      }
      if (filters.locationMinRating !== null) {
        apiFilters.location_filters = {
          ...apiFilters.location_filters,
          min_rating: filters.locationMinRating,
        };
      }
      if (filters.locationAmenities.length > 0) {
        apiFilters.location_filters = {
          ...apiFilters.location_filters,
          amenities: filters.locationAmenities,
        };
      }
      if (filters.locationIs24x7) {
        apiFilters.location_filters = {
          ...apiFilters.location_filters,
          is_24_7: true,
        };
      }

      const response = await discover(apiFilters);
      setEvents(response.events);
      setLocations(response.locations);
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('Failed to load map data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [searchCenter, userLocation, center, filters]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Convert to map items
  const mapItems = useMemo(() => {
    const items: MapItem[] = [];

    if (showEvents && (filters.itemType === 'all' || filters.itemType === 'events')) {
      items.push(...eventsToMapItems(events));
    }

    if (showLocations && (filters.itemType === 'all' || filters.itemType === 'locations')) {
      items.push(...locationsToMapItems(locations));
    }

    return items;
  }, [events, locations, showEvents, showLocations, filters.itemType]);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.searchRadius !== 60) count++;
    if (filters.eventCategories.length > 0) count++;
    if (filters.eventFreeOnly) count++;
    if (filters.eventDateStart) count++;
    if (filters.eventDateEnd) count++;
    if (filters.eventTimeOfDay.length > 0) count++;
    if (filters.locationTypes.length > 0) count++;
    if (filters.locationMinRating !== null) count++;
    if (filters.locationAmenities.length > 0) count++;
    if (filters.locationIs24x7) count++;
    return count;
  }, [filters]);

  // Toggle array filter
  const toggleArrayFilter = <K extends keyof MapFilters>(key: K, value: string) => {
    const current = filters[key] as string[];
    const updated = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value];
    setFilters({ ...filters, [key]: updated });
  };

  // Reset filters
  const resetFilters = () => {
    setFilters(defaultFilters);
  };

  // Center on user
  const centerOnUser = () => {
    if (userLocation) {
      setCenter([userLocation.lat, userLocation.lng]);
      setZoom(11);
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-zinc-900 border-b border-zinc-800 px-4 py-3 flex items-center gap-3 z-10">
        <div className="flex-1 flex items-center gap-3">
          <h1 className="text-lg font-semibold text-zinc-100">Explore Map</h1>
          <span className="text-sm text-zinc-500">
            {mapItems.length} items
          </span>
        </div>

        {/* Quick type toggle */}
        <div className="hidden sm:flex items-center gap-1 bg-zinc-800 rounded-lg p-1">
          {ITEM_TYPES.map(type => {
            const Icon = type.icon;
            return (
              <button
                key={type.id}
                onClick={() => setFilters({ ...filters, itemType: type.id as MapFilters['itemType'] })}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${
                  filters.itemType === type.id
                    ? 'bg-emerald-500 text-white'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <Icon className="w-4 h-4" />
                {type.label}
              </button>
            );
          })}
        </div>

        {/* Filter button */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            showFilters || activeFilterCount > 0
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
              : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Filter className="w-4 h-4" />
          <span className="hidden sm:inline">Filters</span>
          {activeFilterCount > 0 && (
            <span className="px-1.5 py-0.5 bg-emerald-500 text-white text-xs rounded-full">
              {activeFilterCount}
            </span>
          )}
        </button>

        {/* Center on user button */}
        {userLocation && (
          <button
            onClick={centerOnUser}
            className="p-2 bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded-lg transition-colors"
            title="Center on your location"
          >
            <Navigation className="w-4 h-4" />
          </button>
        )}

        {/* Toggle results sidebar button (desktop) */}
        <button
          onClick={() => setShowResultsSidebar(!showResultsSidebar)}
          className={`hidden lg:flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            showResultsSidebar
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
              : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
          }`}
          title={showResultsSidebar ? 'Hide results list' : 'Show results list'}
        >
          {showResultsSidebar ? (
            <PanelRightClose className="w-4 h-4" />
          ) : (
            <PanelRightOpen className="w-4 h-4" />
          )}
          <span className="hidden xl:inline">Results</span>
        </button>
      </header>

      <div className="flex-1 flex relative">
        {/* Filter sidebar */}
        {showFilters && (
          <aside className="w-80 bg-zinc-900 border-r border-zinc-800 overflow-y-auto">
            <div className="p-4">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-zinc-100">Filters</h2>
                <button
                  onClick={() => setShowFilters(false)}
                  className="p-1 text-zinc-500 hover:text-zinc-300"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Search Radius */}
              <div className="mb-6">
                <label className="text-sm text-zinc-400 mb-2 block">
                  Search Radius: {filters.searchRadius} km
                </label>
                <input
                  type="range"
                  min="10"
                  max="200"
                  step="10"
                  value={filters.searchRadius}
                  onChange={e => setFilters({ ...filters, searchRadius: parseInt(e.target.value) })}
                  className="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
                <div className="flex justify-between text-xs text-zinc-500 mt-1">
                  <span>10km</span>
                  <span>200km</span>
                </div>
              </div>

              {/* Layer visibility */}
              <div className="mb-6">
                <label className="text-sm text-zinc-400 mb-2 block">Show on map</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowEvents(!showEvents)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                      showEvents
                        ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
                        : 'bg-zinc-800 text-zinc-500 border border-zinc-700'
                    }`}
                  >
                    {showEvents ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    Events
                  </button>
                  <button
                    onClick={() => setShowLocations(!showLocations)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                      showLocations
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                        : 'bg-zinc-800 text-zinc-500 border border-zinc-700'
                    }`}
                  >
                    {showLocations ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    Places
                  </button>
                </div>
              </div>

              {/* Event Filters */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-purple-400" />
                  Event Filters
                </h3>

                {/* Categories */}
                <div className="mb-4">
                  <label className="text-xs text-zinc-500 mb-2 block">Categories</label>
                  <div className="flex flex-wrap gap-1.5">
                    {EVENT_CATEGORIES.map(cat => (
                      <button
                        key={cat}
                        onClick={() => toggleArrayFilter('eventCategories', cat)}
                        className={`px-2 py-1 text-xs rounded transition-colors capitalize ${
                          filters.eventCategories.includes(cat)
                            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
                            : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                        }`}
                      >
                        {cat.toLowerCase()}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Date range */}
                <div className="grid grid-cols-2 gap-2 mb-4">
                  <div>
                    <label className="text-xs text-zinc-500 mb-1 block">From</label>
                    <input
                      type="date"
                      value={filters.eventDateStart}
                      onChange={e => setFilters({ ...filters, eventDateStart: e.target.value })}
                      className="w-full px-2 py-1.5 bg-zinc-800 border border-zinc-700 rounded text-sm text-zinc-100 focus:outline-none focus:border-emerald-500/50"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-zinc-500 mb-1 block">To</label>
                    <input
                      type="date"
                      value={filters.eventDateEnd}
                      onChange={e => setFilters({ ...filters, eventDateEnd: e.target.value })}
                      className="w-full px-2 py-1.5 bg-zinc-800 border border-zinc-700 rounded text-sm text-zinc-100 focus:outline-none focus:border-emerald-500/50"
                    />
                  </div>
                </div>

                {/* Time of day */}
                <div className="mb-4">
                  <label className="text-xs text-zinc-500 mb-2 block">Time of Day</label>
                  <div className="flex flex-wrap gap-1.5">
                    {TIME_OF_DAY.map(time => {
                      const Icon = time.icon;
                      return (
                        <button
                          key={time.id}
                          onClick={() => toggleArrayFilter('eventTimeOfDay', time.id)}
                          className={`flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors ${
                            filters.eventTimeOfDay.includes(time.id)
                              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
                              : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                          }`}
                        >
                          <Icon className="w-3 h-3" />
                          {time.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Free only */}
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.eventFreeOnly}
                    onChange={e => setFilters({ ...filters, eventFreeOnly: e.target.checked })}
                    className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-emerald-500 focus:ring-emerald-500/50"
                  />
                  <span className="text-sm text-zinc-300">Free events only</span>
                </label>
              </div>

              {/* Location Filters */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-emerald-400" />
                  Location Filters
                </h3>

                {/* Location types */}
                <div className="mb-4">
                  <label className="text-xs text-zinc-500 mb-2 block">Types</label>
                  <div className="flex flex-wrap gap-1.5">
                    {LOCATION_TYPES.map(type => (
                      <button
                        key={type.id}
                        onClick={() => toggleArrayFilter('locationTypes', type.id)}
                        className={`px-2 py-1 text-xs rounded transition-colors ${
                          filters.locationTypes.includes(type.id)
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                            : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                        }`}
                      >
                        {type.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Rating */}
                <div className="mb-4">
                  <label className="text-xs text-zinc-500 mb-2 block">Minimum Rating</label>
                  <div className="flex gap-1.5">
                    {RATING_OPTIONS.map(opt => (
                      <button
                        key={opt.label}
                        onClick={() => setFilters({ ...filters, locationMinRating: opt.value })}
                        className={`flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors ${
                          filters.locationMinRating === opt.value
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50'
                            : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                        }`}
                      >
                        {opt.value && <Star className="w-3 h-3 fill-current" />}
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Amenities */}
                <div className="mb-4">
                  <label className="text-xs text-zinc-500 mb-2 block">Amenities</label>
                  <div className="flex flex-wrap gap-1.5">
                    {AMENITIES.map(amenity => {
                      const Icon = amenity.icon;
                      return (
                        <button
                          key={amenity.id}
                          onClick={() => toggleArrayFilter('locationAmenities', amenity.id)}
                          className={`flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors ${
                            filters.locationAmenities.includes(amenity.id)
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                              : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                          }`}
                        >
                          <Icon className="w-3 h-3" />
                          {amenity.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* 24/7 */}
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.locationIs24x7}
                    onChange={e => setFilters({ ...filters, locationIs24x7: e.target.checked })}
                    className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-emerald-500 focus:ring-emerald-500/50"
                  />
                  <span className="text-sm text-zinc-300">24/7 access only</span>
                </label>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t border-zinc-800">
                <button
                  onClick={resetFilters}
                  className="flex items-center justify-center gap-2 px-3 py-2 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors text-sm"
                >
                  <RotateCcw className="w-4 h-4" />
                  Reset
                </button>
                <button
                  onClick={() => {
                    fetchData();
                    setShowFilters(false);
                  }}
                  className="flex-1 py-2 bg-emerald-500 hover:bg-emerald-400 text-white font-medium rounded-lg transition-colors text-sm"
                >
                  Apply Filters
                </button>
              </div>
            </div>
          </aside>
        )}

        {/* Map */}
        <div className="flex-1 relative">
          {isLoading && (
            <div className="absolute inset-0 bg-zinc-900/80 flex items-center justify-center z-10">
              <div className="flex items-center gap-3 text-zinc-300">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
                <span>Loading map data...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 px-4 py-2 bg-red-500/20 border border-red-500/50 text-red-400 rounded-lg text-sm">
              {error}
            </div>
          )}

          <MapExplore
            items={mapItems}
            center={center}
            zoom={zoom}
            userLocation={userLocation || undefined}
            onItemClick={setSelectedItem}
            onMoveEnd={handleMoveEnd}
            height="100%"
          />

          {/* Item count badge */}
          <div className="absolute bottom-4 left-4 z-10 flex items-center gap-2">
            <div className="px-3 py-1.5 bg-zinc-900/90 backdrop-blur-sm rounded-lg border border-zinc-700 text-sm">
              <span className="text-zinc-400">Showing </span>
              <span className="text-emerald-400 font-medium">{mapItems.length}</span>
              <span className="text-zinc-400"> items</span>
            </div>
            {!showLocations && (
              <div className="px-2 py-1 bg-zinc-900/90 backdrop-blur-sm rounded border border-zinc-700 text-xs text-zinc-500">
                Places hidden
              </div>
            )}
            {!showEvents && (
              <div className="px-2 py-1 bg-zinc-900/90 backdrop-blur-sm rounded border border-zinc-700 text-xs text-zinc-500">
                Events hidden
              </div>
            )}
          </div>

          {/* Legend - hidden when sidebar is open on desktop */}
          <div className={`absolute bottom-4 z-10 bg-zinc-900/90 backdrop-blur-sm rounded-lg border border-zinc-700 p-3 transition-all ${
            showResultsSidebar ? 'right-4 lg:right-[340px]' : 'right-4'
          }`}>
            <p className="text-xs text-zinc-400 mb-2">Legend</p>
            <div className="flex flex-col gap-1.5 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500 border-2 border-white shadow-sm" />
                <span className="text-zinc-300">Events</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-emerald-500 border-2 border-white shadow-sm" />
                <span className="text-zinc-300">Camping/Parking</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-amber-500 border-2 border-white shadow-sm" />
                <span className="text-zinc-300">Attractions</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500 border-2 border-white shadow-sm" />
                <span className="text-zinc-300">Your location</span>
              </div>
            </div>
          </div>

          {/* Mobile: Show results button */}
          <button
            onClick={() => setMobileSheetExpanded(true)}
            className="lg:hidden absolute bottom-4 right-4 z-10 flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-full shadow-lg hover:bg-emerald-400 transition-colors"
          >
            <List className="w-4 h-4" />
            <span className="font-medium">{mapItems.length} Results</span>
          </button>
        </div>

        {/* Results sidebar - Desktop */}
        {showResultsSidebar && (
          <MapSidebar
            items={mapItems}
            selectedItem={selectedItem}
            onItemSelect={setSelectedItem}
            onClose={() => setShowResultsSidebar(false)}
            className="hidden lg:flex w-80 xl:w-96"
          />
        )}
      </div>

      {/* Mobile bottom sheet for results */}
      {mobileSheetExpanded && (
        <div className="lg:hidden fixed inset-0 z-30">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileSheetExpanded(false)}
          />
          {/* Sheet */}
          <div className="absolute bottom-0 left-0 right-0 max-h-[80vh] bg-zinc-900 rounded-t-2xl shadow-xl flex flex-col">
            {/* Handle */}
            <div className="flex justify-center py-2">
              <div className="w-12 h-1 bg-zinc-700 rounded-full" />
            </div>
            {/* Content */}
            <MapSidebar
              items={mapItems}
              selectedItem={selectedItem}
              onItemSelect={(item) => {
                setSelectedItem(item);
                setMobileSheetExpanded(false);
              }}
              onClose={() => setMobileSheetExpanded(false)}
              className="flex-1 overflow-hidden border-t-0 border-l-0 border-r-0"
            />
          </div>
        </div>
      )}

      {/* Selected item panel (mobile) - only show when bottom sheet is closed */}
      {selectedItem && !mobileSheetExpanded && (
        <div className="lg:hidden fixed bottom-20 left-4 right-4 z-20 bg-zinc-900 rounded-xl border border-zinc-700 shadow-xl overflow-hidden">
          <button
            onClick={() => setSelectedItem(null)}
            className="absolute top-2 right-2 z-10 p-1 bg-zinc-800/80 rounded-full text-zinc-400 hover:text-zinc-200"
          >
            <X className="w-4 h-4" />
          </button>

          {/* Image header */}
          {(selectedItem.main_image_url || (selectedItem.images && selectedItem.images.length > 0)) && (
            <div className="h-24 w-full">
              <img
                src={selectedItem.main_image_url || selectedItem.images?.[0]}
                alt={selectedItem.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).parentElement!.style.display = 'none';
                }}
              />
            </div>
          )}

          <div className="p-4">
            <div className="flex items-start gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                selectedItem.itemType === 'event' ? 'bg-purple-500/20' : 'bg-emerald-500/20'
              }`}>
                {selectedItem.itemType === 'event' ? (
                  <Calendar className="w-5 h-5 text-purple-400" />
                ) : (
                  <MapPin className="w-5 h-5 text-emerald-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-zinc-100 truncate">{selectedItem.name}</h3>
                <p className="text-sm text-zinc-400">
                  {selectedItem.city || selectedItem.address || 'Unknown location'}
                </p>
                {selectedItem.rating && (
                  <div className="flex items-center gap-1 mt-1">
                    <Star className="w-3 h-3 text-amber-400 fill-current" />
                    <span className="text-sm text-amber-400">{selectedItem.rating.toFixed(1)}</span>
                  </div>
                )}
              </div>
            </div>
            {selectedItem.website && (
              <a
                href={selectedItem.website}
                target="_blank"
                rel="noopener noreferrer"
                className="block mt-3 py-2 text-center bg-emerald-500/20 text-emerald-400 rounded-lg text-sm hover:bg-emerald-500/30 transition-colors"
              >
                Visit website
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
