'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Filter,
  MapPin,
  Calendar,
  Star,
  Clock,
  ChevronRight,
  Tent,
  Castle,
  Mountain,
  Music,
  X,
  Loader2,
  DollarSign,
  Wifi,
  Zap,
  Droplets,
  Car,
  Trash2,
  Sun,
  Sunset,
  Moon,
  Sunrise,
  RotateCcw,
} from 'lucide-react';
import { discover, type DiscoverEvent, type DiscoverLocation } from '@/services/discoverService';
import SafeHtml from '@/components/SafeHtml';
import { getCurrentPosition, type Position } from '@/services/locationService';

interface DisplayItem {
  id: string;
  name: string;
  type: 'event' | 'place' | 'camping';
  category: string;
  location: string;
  distance_km: number;
  date?: string;
  time?: string;
  rating?: number;
  price?: string;
  description?: string;
  latitude: number;
  longitude: number;
  score?: number;  // Quality/relevance score for events
}

const CATEGORIES = [
  { id: 'all', name: 'All', icon: Search },
  { id: 'events', name: 'Events', icon: Calendar },
  { id: 'places', name: 'Places', icon: Castle },
  { id: 'nature', name: 'Nature', icon: Mountain },
  { id: 'camping', name: 'Camping', icon: Tent },
  { id: 'music', name: 'Music', icon: Music },
];

// Filter options
const EVENT_CATEGORIES = [
  'FESTIVAL', 'CONCERT', 'SPORTS', 'MARKET', 'EXHIBITION',
  'THEATER', 'CULTURAL', 'FOOD', 'OUTDOOR', 'OTHER'
];

const LOCATION_TYPES = [
  { id: 'CAMPSITE', label: 'Campsite' },
  { id: 'PARKING', label: 'Parking' },
  { id: 'REST_AREA', label: 'Rest Area' },
  { id: 'SERVICE_AREA', label: 'Service Area' },
  { id: 'POI', label: 'Point of Interest' },
  { id: 'ATTRACTION', label: 'Attraction' },
  { id: 'RESTAURANT', label: 'Restaurant' },
  { id: 'HOTEL', label: 'Hotel' },
];

const PRICE_TYPES = [
  { id: 'free', label: 'Free' },
  { id: 'paid_low', label: '€ (Budget)' },
  { id: 'paid_medium', label: '€€ (Moderate)' },
  { id: 'paid_high', label: '€€€ (Premium)' },
];

const AMENITIES = [
  { id: 'wifi', label: 'WiFi', icon: Wifi },
  { id: 'electricity', label: 'Electricity', icon: Zap },
  { id: 'showers', label: 'Showers', icon: Droplets },
  { id: 'parking', label: 'Parking', icon: Car },
  { id: 'toilets', label: 'Toilets', icon: Droplets },
  { id: 'drinking_water', label: 'Drinking Water', icon: Droplets },
  { id: 'waste_disposal', label: 'Waste Disposal', icon: Trash2 },
];

const TIME_OF_DAY = [
  { id: 'morning', label: 'Morning', icon: Sunrise },
  { id: 'afternoon', label: 'Afternoon', icon: Sun },
  { id: 'evening', label: 'Evening', icon: Sunset },
  { id: 'night', label: 'Night', icon: Moon },
];

interface AdvancedFilters {
  // Event filters
  eventCategories: string[];
  eventFreeOnly: boolean;
  eventPriceMax: number | null;
  eventDateStart: string;
  eventDateEnd: string;
  eventTimeOfDay: string[];
  // Location filters
  locationTypes: string[];
  locationMinRating: number | null;
  locationPriceTypes: string[];
  locationAmenities: string[];
  locationIs24x7: boolean;
  locationNoBookingRequired: boolean;
  // General
  searchRadius: number;
}

const defaultFilters: AdvancedFilters = {
  eventCategories: [],
  eventFreeOnly: false,
  eventPriceMax: null,
  eventDateStart: '',
  eventDateEnd: '',
  eventTimeOfDay: [],
  locationTypes: [],
  locationMinRating: null,
  locationPriceTypes: [],
  locationAmenities: [],
  locationIs24x7: false,
  locationNoBookingRequired: false,
  searchRadius: 100,
};

function CategoryIcon({ type }: { type: DisplayItem['type'] }) {
  switch (type) {
    case 'event':
      return <Calendar className="w-5 h-5 text-purple-400" />;
    case 'place':
      return <Castle className="w-5 h-5 text-amber-400" />;
    case 'camping':
      return <Tent className="w-5 h-5 text-emerald-400" />;
  }
}

// Filter Modal Component
function FilterModal({
  isOpen,
  onClose,
  filters,
  onFiltersChange,
  onApply,
  onReset,
  activeFilterCount,
  selectedCategory,
}: {
  isOpen: boolean;
  onClose: () => void;
  filters: AdvancedFilters;
  onFiltersChange: (filters: AdvancedFilters) => void;
  onApply: () => void;
  onReset: () => void;
  activeFilterCount: number;
  selectedCategory: string;
}) {
  if (!isOpen) return null;

  // Determine which filter sections to show based on selected category
  const showEventFilters = ['all', 'events', 'music'].includes(selectedCategory);
  const showLocationFilters = ['all', 'places', 'nature', 'camping'].includes(selectedCategory);

  const toggleArrayFilter = <K extends keyof AdvancedFilters>(
    key: K,
    value: string
  ) => {
    const current = filters[key] as string[];
    const updated = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    onFiltersChange({ ...filters, [key]: updated });
  };

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-end lg:items-center justify-center"
      onClick={onClose}
    >
      <div
        className="bg-zinc-900 rounded-t-2xl lg:rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col animate-slide-up lg:animate-none"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-semibold text-zinc-100">Filters</h2>
            {activeFilterCount > 0 && (
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">
                {activeFilterCount} active
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 text-zinc-400 hover:text-zinc-200 rounded-lg hover:bg-zinc-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="overflow-y-auto flex-1 p-4 space-y-6">
          {/* Search Radius */}
          <div>
            <label className="text-sm font-medium text-zinc-300 mb-2 block">
              Search Radius: {filters.searchRadius} km
            </label>
            <input
              type="range"
              min="10"
              max="500"
              step="10"
              value={filters.searchRadius}
              onChange={(e) =>
                onFiltersChange({
                  ...filters,
                  searchRadius: parseInt(e.target.value),
                })
              }
              className="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
            <div className="flex justify-between text-xs text-zinc-500 mt-1">
              <span>10 km</span>
              <span>500 km</span>
            </div>
          </div>

          {/* Location Filters Section */}
          {showLocationFilters && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-2">
              <MapPin className="w-4 h-4 text-emerald-400" />
              Location Filters
            </h3>

            {/* Location Types */}
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">
                Location Types
              </label>
              <div className="flex flex-wrap gap-2">
                {LOCATION_TYPES.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => toggleArrayFilter('locationTypes', type.id)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
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

            {/* Minimum Rating */}
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">
                Minimum Rating
              </label>
              <div className="flex gap-2">
                {[null, 3, 3.5, 4, 4.5].map((rating) => (
                  <button
                    key={rating ?? 'any'}
                    onClick={() =>
                      onFiltersChange({ ...filters, locationMinRating: rating })
                    }
                    className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg transition-colors ${
                      filters.locationMinRating === rating
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50'
                        : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                    }`}
                  >
                    {rating ? (
                      <>
                        <Star className="w-3 h-3 fill-current" />
                        {rating}+
                      </>
                    ) : (
                      'Any'
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Price Types */}
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">
                Price Range
              </label>
              <div className="flex flex-wrap gap-2">
                {PRICE_TYPES.map((price) => (
                  <button
                    key={price.id}
                    onClick={() =>
                      toggleArrayFilter('locationPriceTypes', price.id)
                    }
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                      filters.locationPriceTypes.includes(price.id)
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                        : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                    }`}
                  >
                    {price.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Amenities */}
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">
                Amenities
              </label>
              <div className="flex flex-wrap gap-2">
                {AMENITIES.map((amenity) => {
                  const Icon = amenity.icon;
                  return (
                    <button
                      key={amenity.id}
                      onClick={() =>
                        toggleArrayFilter('locationAmenities', amenity.id)
                      }
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors ${
                        filters.locationAmenities.includes(amenity.id)
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                          : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {amenity.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Location Toggles */}
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.locationIs24x7}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      locationIs24x7: e.target.checked,
                    })
                  }
                  className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-emerald-500 focus:ring-emerald-500/50"
                />
                <span className="text-sm text-zinc-300">24/7 Access Only</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.locationNoBookingRequired}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      locationNoBookingRequired: e.target.checked,
                    })
                  }
                  className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-emerald-500 focus:ring-emerald-500/50"
                />
                <span className="text-sm text-zinc-300">No Booking Required</span>
              </label>
            </div>
          </div>
          )}

          {/* Event Filters Section */}
          {showEventFilters && (
          <div className={`space-y-4 ${showLocationFilters ? 'pt-4 border-t border-zinc-800' : ''}`}>
            <h3 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-2">
              <Calendar className="w-4 h-4 text-purple-400" />
              Event Filters
            </h3>

            {/* Event Categories */}
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">
                Event Categories
              </label>
              <div className="flex flex-wrap gap-2">
                {EVENT_CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => toggleArrayFilter('eventCategories', cat)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors capitalize ${
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

            {/* Event Date Range */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-zinc-400 mb-2 block">
                  From Date
                </label>
                <input
                  type="date"
                  value={filters.eventDateStart}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      eventDateStart: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-emerald-500/50"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 mb-2 block">
                  To Date
                </label>
                <input
                  type="date"
                  value={filters.eventDateEnd}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      eventDateEnd: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-emerald-500/50"
                />
              </div>
            </div>

            {/* Time of Day */}
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">
                Time of Day
              </label>
              <div className="flex flex-wrap gap-2">
                {TIME_OF_DAY.map((time) => {
                  const Icon = time.icon;
                  return (
                    <button
                      key={time.id}
                      onClick={() =>
                        toggleArrayFilter('eventTimeOfDay', time.id)
                      }
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors ${
                        filters.eventTimeOfDay.includes(time.id)
                          ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
                          : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {time.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Event Price */}
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.eventFreeOnly}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      eventFreeOnly: e.target.checked,
                    })
                  }
                  className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-emerald-500 focus:ring-emerald-500/50"
                />
                <span className="text-sm text-zinc-300">Free Events Only</span>
              </label>
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-zinc-500" />
                <span className="text-sm text-zinc-400">Max Price:</span>
                <input
                  type="number"
                  min="0"
                  placeholder="Any"
                  value={filters.eventPriceMax ?? ''}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      eventPriceMax: e.target.value
                        ? parseInt(e.target.value)
                        : null,
                    })
                  }
                  className="w-20 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-sm text-zinc-100 focus:outline-none focus:border-emerald-500/50"
                />
                <span className="text-sm text-zinc-500">€</span>
              </div>
            </div>
          </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex gap-2 p-4 border-t border-zinc-800">
          <button
            onClick={onReset}
            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
          <button
            onClick={() => {
              onApply();
              onClose();
            }}
            className="flex-1 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-white font-medium rounded-lg transition-colors"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>
  );
}

function ResultCard({ item, onSelect }: { item: DisplayItem; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className="w-full text-left bg-zinc-900/50 hover:bg-zinc-800/50 border border-zinc-800 rounded-xl p-4 transition-colors"
    >
      <div className="flex gap-3">
        <div className="w-12 h-12 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
          <CategoryIcon type={item.type} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-medium text-zinc-100 truncate">{item.name}</h3>
            {item.rating && (
              <span className="flex items-center gap-1 text-sm text-amber-400 flex-shrink-0">
                <Star className="w-3 h-3 fill-current" />
                {item.rating.toFixed(1)}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 text-sm text-zinc-500 mt-1">
            <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs">
              {item.category}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {item.distance_km.toFixed(1)} km
            </span>
          </div>

          {item.date && (
            <div className="flex items-center gap-2 text-sm text-zinc-400 mt-2">
              <Calendar className="w-3 h-3" />
              <span>{item.date}</span>
              {item.time && (
                <>
                  <Clock className="w-3 h-3 ml-2" />
                  <span>{item.time}</span>
                </>
              )}
            </div>
          )}

          {item.price && (
            <p className="text-sm text-emerald-400 mt-1">{item.price}</p>
          )}
        </div>

        <ChevronRight className="w-5 h-5 text-zinc-600 flex-shrink-0 hidden sm:block" />
      </div>
    </button>
  );
}

// Convert API responses to display items
function eventToDisplayItem(event: DiscoverEvent, index: number): DisplayItem {
  return {
    id: `event-${event.id}`,
    name: event.name,
    type: 'event',
    category: event.category || 'Event',
    location: event.city ? `${event.city}, ${event.country}` : event.address || 'Unknown',
    distance_km: event.distance_km,
    date: event.start_datetime
      ? new Date(event.start_datetime).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        })
      : undefined,
    time: event.start_datetime && !event.all_day
      ? new Date(event.start_datetime).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
        })
      : undefined,
    price: event.free ? 'Free' : event.price ? `€${event.price}` : undefined,
    description: event.description || undefined,
    latitude: event.latitude,
    longitude: event.longitude,
    score: event.score ?? (1 - index * 0.01),  // Use backend score, or preserve order
  };
}

function locationToDisplayItem(location: DiscoverLocation): DisplayItem {
  const isCamping = ['CAMPSITE', 'PARKING', 'REST_AREA'].includes(location.location_type);
  return {
    id: `loc-${location.id}`,
    name: location.name,
    type: isCamping ? 'camping' : 'place',
    category: location.location_type?.replace('_', ' ') || 'Place',
    location: location.city ? `${location.city}, ${location.country}` : location.address || 'Unknown',
    distance_km: location.distance_km,
    rating: location.rating || undefined,
    price: location.price_type === 'free'
      ? 'Free'
      : location.price_min
      ? `€${location.price_min}${location.price_max ? `-${location.price_max}` : ''}/night`
      : undefined,
    description: location.description || undefined,
    latitude: location.latitude,
    longitude: location.longitude,
  };
}

// Helper to count active filters
function countActiveFilters(filters: AdvancedFilters): number {
  let count = 0;
  if (filters.searchRadius !== 100) count++;
  if (filters.eventCategories.length > 0) count++;
  if (filters.eventFreeOnly) count++;
  if (filters.eventPriceMax !== null) count++;
  if (filters.eventDateStart) count++;
  if (filters.eventDateEnd) count++;
  if (filters.eventTimeOfDay.length > 0) count++;
  if (filters.locationTypes.length > 0) count++;
  if (filters.locationMinRating !== null) count++;
  if (filters.locationPriceTypes.length > 0) count++;
  if (filters.locationAmenities.length > 0) count++;
  if (filters.locationIs24x7) count++;
  if (filters.locationNoBookingRequired) count++;
  return count;
}

export default function DiscoverPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedItem, setSelectedItem] = useState<DisplayItem | null>(null);

  const [position, setPosition] = useState<Position | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [results, setResults] = useState<DisplayItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);

  // Advanced filters state
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState<AdvancedFilters>(defaultFilters);
  const activeFilterCount = countActiveFilters(appliedFilters);

  // Get user position on mount
  useEffect(() => {
    async function getPosition() {
      try {
        const pos = await getCurrentPosition();
        setPosition(pos);
      } catch (error) {
        // No fallback - user must enable location services
        console.warn('Location access denied - discovery requires location');
      }
    }
    getPosition();
  }, []);

  // Fetch data when position, category, or filters change
  const fetchData = useCallback(async () => {
    if (!position) return;

    setIsLoading(true);
    try {
      // Determine what to fetch based on category
      const itemTypes: ('events' | 'locations')[] =
        selectedCategory === 'events' || selectedCategory === 'music'
          ? ['events']
          : selectedCategory === 'camping'
          ? ['locations']
          : selectedCategory === 'places' || selectedCategory === 'nature'
          ? ['locations']
          : ['events', 'locations'];

      // Build filters - start with category-based filters
      const eventFilters: Record<string, unknown> = {};
      const locationFilters: Record<string, unknown> = {};

      // Category-based filters
      if (selectedCategory === 'music') {
        eventFilters.categories = ['CONCERT', 'FESTIVAL'];
      }
      if (selectedCategory === 'camping') {
        locationFilters.location_types = ['CAMPSITE', 'PARKING', 'REST_AREA'];
      }
      if (selectedCategory === 'nature') {
        locationFilters.location_types = ['POI'];
        locationFilters.features = ['nature'];
      }
      if (selectedCategory === 'places') {
        locationFilters.location_types = ['POI', 'ATTRACTION'];
      }

      // Apply advanced event filters
      if (appliedFilters.eventCategories.length > 0) {
        eventFilters.categories = appliedFilters.eventCategories;
      }
      if (appliedFilters.eventFreeOnly) {
        eventFilters.free_only = true;
      }
      if (appliedFilters.eventPriceMax !== null) {
        eventFilters.price_max = appliedFilters.eventPriceMax;
      }
      if (appliedFilters.eventDateStart) {
        eventFilters.date_start = appliedFilters.eventDateStart;
      }
      if (appliedFilters.eventDateEnd) {
        eventFilters.date_end = appliedFilters.eventDateEnd;
      }
      if (appliedFilters.eventTimeOfDay.length > 0) {
        eventFilters.time_of_day = appliedFilters.eventTimeOfDay;
      }

      // Apply advanced location filters
      if (appliedFilters.locationTypes.length > 0) {
        locationFilters.location_types = appliedFilters.locationTypes;
      }
      if (appliedFilters.locationMinRating !== null) {
        locationFilters.min_rating = appliedFilters.locationMinRating;
      }
      if (appliedFilters.locationPriceTypes.length > 0) {
        locationFilters.price_types = appliedFilters.locationPriceTypes;
      }
      if (appliedFilters.locationAmenities.length > 0) {
        locationFilters.amenities = appliedFilters.locationAmenities;
      }
      if (appliedFilters.locationIs24x7) {
        locationFilters.is_24_7 = true;
      }
      if (appliedFilters.locationNoBookingRequired) {
        locationFilters.no_booking_required = true;
      }

      const response = await discover({
        latitude: position.latitude,
        longitude: position.longitude,
        radius_km: appliedFilters.searchRadius,
        item_types: itemTypes,
        search_text: searchQuery || undefined,
        limit: 50,
        event_filters: Object.keys(eventFilters).length > 0 ? eventFilters : undefined,
        location_filters: Object.keys(locationFilters).length > 0 ? locationFilters : undefined,
      });

      // Convert to display items (events already sorted by score from backend)
      const eventItems = response.events.map((event, index) => eventToDisplayItem(event, index));
      const locationItems = response.locations.map(locationToDisplayItem);

      // Combine items: events first (sorted by score), then locations (sorted by distance)
      // For 'all' category, interleave by score/distance; for specific categories, keep backend order
      let allItems: DisplayItem[];
      if (selectedCategory === 'all') {
        // Interleave events and locations, prioritizing by score for events
        allItems = [...eventItems, ...locationItems].sort((a, b) => {
          // Events with scores come first, sorted by score descending
          // Locations sorted by distance
          if (a.type === 'event' && b.type === 'event') {
            return (b.score ?? 0) - (a.score ?? 0);
          }
          if (a.type !== 'event' && b.type !== 'event') {
            return a.distance_km - b.distance_km;
          }
          // Events before locations when scores are high
          if (a.type === 'event') {
            return (a.score ?? 0) > 0.3 ? -1 : 1;
          }
          return (b.score ?? 0) > 0.3 ? 1 : -1;
        });
      } else {
        // For specific categories, just concatenate (backend already sorted appropriately)
        allItems = [...eventItems, ...locationItems];
      }

      setResults(allItems);
      setTotalCount(response.total_count);
    } catch (error) {
      console.error('Failed to fetch discover data:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, [position, selectedCategory, searchQuery, appliedFilters]);

  useEffect(() => {
    const debounce = setTimeout(fetchData, 300);
    return () => clearTimeout(debounce);
  }, [fetchData]);

  // Filter results client-side for search (API might not support full-text)
  const filteredResults = results.filter((item) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      item.name.toLowerCase().includes(query) ||
      item.location.toLowerCase().includes(query) ||
      item.category.toLowerCase().includes(query)
    );
  });

  return (
    <main className="min-h-screen bg-zinc-950">
      {/* Header with search */}
      <header className="sticky top-0 z-50 bg-zinc-950/90 backdrop-blur-sm border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-semibold text-zinc-100">Discover</h1>
            <button
              onClick={() => {
                setAdvancedFilters(appliedFilters);
                setShowFilterModal(true);
              }}
              className="flex items-center gap-1 text-sm text-zinc-400 hover:text-zinc-200 lg:hidden"
            >
              <Filter className="w-4 h-4" />
              Filters
              {activeFilterCount > 0 && (
                <span className="ml-1 px-1.5 py-0.5 bg-emerald-500 text-white text-xs rounded-full">
                  {activeFilterCount}
                </span>
              )}
            </button>
          </div>

          {/* Search bar */}
          <div className="relative max-w-2xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <input
              type="text"
              placeholder="Search places, events, camping..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-10 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500/50"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Category tabs */}
        <div className="max-w-7xl mx-auto px-4 lg:px-8 pb-3">
          <div className="flex gap-2 overflow-x-auto scrollbar-hide">
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap transition-colors ${
                    selectedCategory === cat.id
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm">{cat.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Results */}
      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-4">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-zinc-500">
            {isLoading ? 'Searching...' : `${filteredResults.length} results near you`}
          </p>
          <button
            onClick={() => {
              setAdvancedFilters(appliedFilters);
              setShowFilterModal(true);
            }}
            className="hidden lg:flex items-center gap-1 text-sm text-zinc-400 hover:text-zinc-200"
          >
            <Filter className="w-4 h-4" />
            More Filters
            {activeFilterCount > 0 && (
              <span className="ml-1 px-1.5 py-0.5 bg-emerald-500 text-white text-xs rounded-full">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 text-zinc-500 animate-spin" />
            <span className="ml-2 text-sm text-zinc-500">Finding places nearby...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredResults.map((item) => (
              <ResultCard
                key={item.id}
                item={item}
                onSelect={() => setSelectedItem(item)}
              />
            ))}
          </div>
        )}

        {!isLoading && filteredResults.length === 0 && (
          <div className="text-center py-12">
            <Search className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
            <p className="text-zinc-400">No results found</p>
            <p className="text-sm text-zinc-600 mt-1">
              Try adjusting your search or filters
            </p>
          </div>
        )}
      </div>

      {/* Detail modal */}
      {selectedItem && (
        <div
          className="fixed inset-0 bg-black/60 z-50 flex items-end lg:items-center justify-center"
          onClick={() => setSelectedItem(null)}
        >
          <div
            className="bg-zinc-900 rounded-t-2xl lg:rounded-2xl w-full max-w-lg p-6 animate-slide-up lg:animate-none"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-12 h-1 bg-zinc-700 rounded-full mx-auto mb-4 lg:hidden" />

            <div className="flex items-start gap-4 mb-4">
              <div className="w-14 h-14 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
                <CategoryIcon type={selectedItem.type} />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-zinc-100">
                  {selectedItem.name}
                </h2>
                <p className="text-sm text-zinc-500 mt-1">
                  {selectedItem.location}
                </p>
              </div>
            </div>

            {selectedItem.description && (
              <SafeHtml html={selectedItem.description} className="text-zinc-400 mb-4 [&_p]:mb-2 [&_a]:text-emerald-400 [&_a:hover]:text-emerald-300 [&_strong]:text-zinc-300 [&_ul]:list-disc [&_ul]:ml-4 [&_ol]:list-decimal [&_ol]:ml-4" />
            )}

            <div className="flex flex-wrap gap-3 text-sm mb-6">
              <span className="flex items-center gap-1 text-zinc-400">
                <MapPin className="w-4 h-4" />
                {selectedItem.distance_km.toFixed(1)} km away
              </span>
              {selectedItem.rating && (
                <span className="flex items-center gap-1 text-amber-400">
                  <Star className="w-4 h-4 fill-current" />
                  {selectedItem.rating.toFixed(1)}
                </span>
              )}
              {selectedItem.price && (
                <span className="text-emerald-400">{selectedItem.price}</span>
              )}
            </div>

            <div className="flex gap-2">
              <button className="flex-1 py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-medium rounded-lg transition-colors">
                Add to Trip
              </button>
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-3 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filter Modal */}
      <FilterModal
        isOpen={showFilterModal}
        onClose={() => setShowFilterModal(false)}
        filters={advancedFilters}
        onFiltersChange={setAdvancedFilters}
        onApply={() => setAppliedFilters(advancedFilters)}
        onReset={() => {
          setAdvancedFilters(defaultFilters);
          setAppliedFilters(defaultFilters);
        }}
        activeFilterCount={activeFilterCount}
        selectedCategory={selectedCategory}
      />
    </main>
  );
}
