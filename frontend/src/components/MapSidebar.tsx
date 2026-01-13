'use client';

import { useState, useMemo } from 'react';
import {
  X,
  Calendar,
  MapPin,
  Star,
  Clock,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Image as ImageIcon,
  SortAsc,
  Filter,
} from 'lucide-react';
import type { MapItem } from '@/types/map';

// Get the best image for an item
function getItemImage(item: MapItem): string | null {
  // Try main_image_url first (for locations)
  if (item.main_image_url) return item.main_image_url;
  // Then try first image from images array
  if (item.images && item.images.length > 0) return item.images[0];
  return null;
}

// Format date for display
function formatEventDate(datetime: string): string {
  const date = new Date(datetime);
  return date.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}

function formatEventTime(datetime: string): string {
  const date = new Date(datetime);
  return date.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Marker colors (same as MapExplore)
const MARKER_COLORS: Record<string, string> = {
  event: '#a855f7',
  FESTIVAL: '#ec4899',
  CONCERT: '#f43f5e',
  SPORTS: '#22c55e',
  MARKET: '#f59e0b',
  EXHIBITION: '#06b6d4',
  THEATER: '#8b5cf6',
  CULTURAL: '#6366f1',
  FOOD: '#ef4444',
  OUTDOOR: '#84cc16',
  CAMPSITE: '#10b981',
  PARKING: '#64748b',
  REST_AREA: '#0ea5e9',
  SERVICE_AREA: '#3b82f6',
  POI: '#f59e0b',
  ATTRACTION: '#eab308',
  RESTAURANT: '#ef4444',
  HOTEL: '#a855f7',
  ACTIVITY: '#22d3ee',
};

const getMarkerColor = (item: MapItem): string => {
  if (item.itemType === 'event') {
    return MARKER_COLORS[item.category || ''] || MARKER_COLORS.event;
  }
  return MARKER_COLORS[item.location_type || ''] || '#64748b';
};

type SortOption = 'distance' | 'rating' | 'name' | 'date';

interface MapSidebarProps {
  items: MapItem[];
  selectedItem: MapItem | null;
  onItemSelect: (item: MapItem) => void;
  onClose?: () => void;
  isOpen?: boolean;
  className?: string;
}

export default function MapSidebar({
  items,
  selectedItem,
  onItemSelect,
  onClose,
  isOpen = true,
  className = '',
}: MapSidebarProps) {
  const [sortBy, setSortBy] = useState<SortOption>('distance');
  const [filterType, setFilterType] = useState<'all' | 'event' | 'location'>('all');
  const [expandedItem, setExpandedItem] = useState<number | null>(null);

  // Filter and sort items
  const processedItems = useMemo(() => {
    let filtered = items;

    // Filter by type
    if (filterType !== 'all') {
      filtered = items.filter(item => item.itemType === filterType);
    }

    // Sort
    return [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'distance':
          return (a.distance_km ?? Infinity) - (b.distance_km ?? Infinity);
        case 'rating':
          return (b.rating ?? 0) - (a.rating ?? 0);
        case 'name':
          return a.name.localeCompare(b.name);
        case 'date':
          if (a.start_datetime && b.start_datetime) {
            return new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime();
          }
          return a.start_datetime ? -1 : 1;
        default:
          return 0;
      }
    });
  }, [items, sortBy, filterType]);

  // Count by type
  const eventCount = useMemo(() => items.filter(i => i.itemType === 'event').length, [items]);
  const locationCount = useMemo(() => items.filter(i => i.itemType === 'location').length, [items]);

  if (!isOpen) return null;

  return (
    <aside className={`bg-zinc-900 border-l border-zinc-800 flex flex-col ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-zinc-800">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-zinc-100">
            Results
            <span className="ml-2 text-sm text-zinc-500 font-normal">
              {processedItems.length} items
            </span>
          </h2>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 text-zinc-500 hover:text-zinc-300 lg:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Type filter */}
        <div className="flex gap-1 mb-3">
          <button
            onClick={() => setFilterType('all')}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              filterType === 'all'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
            }`}
          >
            All ({items.length})
          </button>
          <button
            onClick={() => setFilterType('event')}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              filterType === 'event'
                ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
                : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
            }`}
          >
            Events ({eventCount})
          </button>
          <button
            onClick={() => setFilterType('location')}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              filterType === 'location'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-zinc-600'
            }`}
          >
            Places ({locationCount})
          </button>
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <SortAsc className="w-4 h-4 text-zinc-500" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="flex-1 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-sm text-zinc-300 focus:outline-none focus:border-emerald-500/50"
          >
            <option value="distance">Nearest first</option>
            <option value="rating">Highest rated</option>
            <option value="name">Name A-Z</option>
            <option value="date">Upcoming events</option>
          </select>
        </div>
      </div>

      {/* Items list */}
      <div className="flex-1 overflow-y-auto">
        {processedItems.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            <ImageIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No items to display</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {processedItems.map((item) => {
              const imageUrl = getItemImage(item);
              const isSelected = selectedItem?.id === item.id && selectedItem?.itemType === item.itemType;
              const isExpanded = expandedItem === item.id;
              const color = getMarkerColor(item);
              const typeLabel = item.itemType === 'event' ? item.category : item.location_type;

              return (
                <div
                  key={`${item.itemType}-${item.id}`}
                  className={`transition-colors ${
                    isSelected ? 'bg-zinc-800/50' : 'hover:bg-zinc-800/30'
                  }`}
                >
                  {/* Main card */}
                  <button
                    onClick={() => {
                      onItemSelect(item);
                      setExpandedItem(isExpanded ? null : item.id);
                    }}
                    className="w-full p-3 text-left"
                  >
                    <div className="flex gap-3">
                      {/* Image */}
                      <div className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden bg-zinc-800">
                        {imageUrl ? (
                          <img
                            src={imageUrl}
                            alt={item.name}
                            className="w-full h-full object-cover"
                            loading="lazy"
                            onError={(e) => {
                              // Hide broken images
                              (e.target as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        ) : (
                          <div
                            className="w-full h-full flex items-center justify-center"
                            style={{ backgroundColor: `${color}22` }}
                          >
                            {item.itemType === 'event' ? (
                              <Calendar className="w-8 h-8" style={{ color }} />
                            ) : (
                              <MapPin className="w-8 h-8" style={{ color }} />
                            )}
                          </div>
                        )}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        {/* Type badge and distance */}
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className="px-1.5 py-0.5 text-[10px] font-semibold rounded uppercase"
                            style={{
                              backgroundColor: `${color}22`,
                              color: color,
                            }}
                          >
                            {typeLabel || (item.itemType === 'event' ? 'Event' : 'Place')}
                          </span>
                          {item.distance_km !== undefined && (
                            <span className="text-[10px] text-zinc-500">
                              {item.distance_km.toFixed(1)} km
                            </span>
                          )}
                        </div>

                        {/* Name */}
                        <h3 className="font-medium text-zinc-100 text-sm leading-tight truncate">
                          {item.name}
                        </h3>

                        {/* Event date/time */}
                        {item.itemType === 'event' && item.start_datetime && (
                          <p className="text-xs text-purple-400 mt-0.5 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatEventDate(item.start_datetime)} {formatEventTime(item.start_datetime)}
                          </p>
                        )}

                        {/* Location/venue */}
                        <p className="text-xs text-zinc-500 mt-0.5 truncate">
                          {item.venue_name || item.city || item.address || 'Unknown location'}
                        </p>

                        {/* Rating (locations only) */}
                        {item.itemType === 'location' && item.rating !== null && item.rating !== undefined && (
                          <div className="flex items-center gap-1 mt-1">
                            <Star className="w-3 h-3 text-amber-400 fill-current" />
                            <span className="text-xs text-amber-400">{item.rating.toFixed(1)}</span>
                            {item.rating_count && (
                              <span className="text-xs text-zinc-500">({item.rating_count})</span>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Expand indicator */}
                      <div className="flex-shrink-0 self-center">
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-zinc-500" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-zinc-500" />
                        )}
                      </div>
                    </div>
                  </button>

                  {/* Expanded content */}
                  {isExpanded && (
                    <div className="px-3 pb-3 pt-0 space-y-3">
                      {/* More images */}
                      {item.images && item.images.length > 1 && (
                        <div className="flex gap-2 overflow-x-auto pb-2">
                          {item.images.slice(0, 5).map((img, idx) => (
                            <img
                              key={idx}
                              src={img}
                              alt={`${item.name} ${idx + 1}`}
                              className="w-16 h-16 rounded object-cover flex-shrink-0"
                              loading="lazy"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none';
                              }}
                            />
                          ))}
                        </div>
                      )}

                      {/* Description */}
                      {item.description && (
                        <p className="text-xs text-zinc-400 line-clamp-3">
                          {item.description}
                        </p>
                      )}

                      {/* Tags */}
                      {item.tags && item.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {item.tags.slice(0, 5).map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 text-[10px] rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Price */}
                      {item.price_type && (
                        <p className="text-xs text-emerald-400">
                          {item.price_type === 'free' ? 'Free' : item.price_type === 'paid' ? 'Paid' : item.price_type}
                        </p>
                      )}

                      {/* Website link */}
                      {item.website && (
                        <a
                          href={item.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="w-3 h-3" />
                          Visit website
                        </a>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
}
