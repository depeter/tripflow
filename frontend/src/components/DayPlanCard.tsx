'use client';

import { useState } from 'react';
import { Compass, Route, Coffee, MapPin, Calendar, Moon, X, Star, ExternalLink, Navigation, ChevronDown, ChevronRight } from 'lucide-react';
import type { DayPlanType, Location } from '@/types/trip';
import { recordRemoval } from '@/services/preferencesService';

interface DayPlanCardProps {
  plan: DayPlanType;
  isSelected: boolean;
  onSelect: () => void;
  onViewDetails: () => void;
  onRemoveItem?: (itemType: 'event' | 'location', itemId: string) => void;
}

// Detail popup component
function LocationDetailPopup({ location, onClose }: { location: Location; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-zinc-900 border border-zinc-700 rounded-xl max-w-md w-full max-h-[80vh] overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Image */}
        {location.image ? (
          <div className="relative h-48 bg-zinc-800">
            <img
              src={location.image}
              alt={location.name}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
            <button
              onClick={onClose}
              className="absolute top-3 right-3 p-2 bg-black/50 hover:bg-black/70 rounded-full transition-colors"
            >
              <X className="w-4 h-4 text-white" />
            </button>
          </div>
        ) : (
          <div className="relative h-32 bg-gradient-to-br from-zinc-800 to-zinc-900 flex items-center justify-center">
            <MapPin className="w-12 h-12 text-zinc-600" />
            <button
              onClick={onClose}
              className="absolute top-3 right-3 p-2 bg-black/50 hover:bg-black/70 rounded-full transition-colors"
            >
              <X className="w-4 h-4 text-white" />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="p-4 space-y-3">
          {/* Title and category */}
          <div>
            <h3 className="text-lg font-semibold text-zinc-100">{location.name}</h3>
            {location.category && (
              <span className="text-xs text-zinc-500 uppercase tracking-wide">{location.category}</span>
            )}
          </div>

          {/* Location info */}
          {(location.city || location.address) && (
            <div className="flex items-start gap-2 text-sm text-zinc-400">
              <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <div>
                {location.address && <p>{location.address}</p>}
                {location.city && <p>{location.city}</p>}
              </div>
            </div>
          )}

          {/* Distance */}
          {location.distance_km !== undefined && (
            <div className="flex items-center gap-2 text-sm">
              <Navigation className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400 font-medium">{location.distance_km.toFixed(1)} km</span>
              <span className="text-zinc-500">from your location</span>
            </div>
          )}

          {/* Rating */}
          {location.rating && (
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
              <span className="text-sm text-zinc-300">{location.rating.toFixed(1)}</span>
            </div>
          )}

          {/* Time and price */}
          <div className="flex items-center gap-4 text-sm">
            {location.time && (
              <div className="flex items-center gap-1 text-zinc-400">
                <Calendar className="w-4 h-4" />
                <span>{location.time}</span>
              </div>
            )}
            {location.price && (
              <span className={`font-medium ${location.price === 'Free' ? 'text-emerald-400' : 'text-zinc-300'}`}>
                {location.price}
              </span>
            )}
          </div>

          {/* Description */}
          {location.description && (
            <p className="text-sm text-zinc-400 line-clamp-4">{location.description}</p>
          )}

          {/* Amenities */}
          {location.amenities && location.amenities.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {location.amenities.map((amenity, i) => (
                <span key={i} className="px-2 py-0.5 text-xs bg-zinc-800 text-zinc-400 rounded">
                  {amenity}
                </span>
              ))}
            </div>
          )}

          {/* Website link */}
          {location.website && (
            <a
              href={location.website}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              <span>View website</span>
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function PlanIcon({ type }: { type: DayPlanType['type'] }) {
  switch (type) {
    case 'exploration':
      return <Compass className="w-5 h-5 text-emerald-400" />;
    case 'transit':
      return <Route className="w-5 h-5 text-orange-400" />;
    case 'zero':
      return <Coffee className="w-5 h-5 text-blue-400" />;
  }
}

function getPlanStyle(type: DayPlanType['type']) {
  switch (type) {
    case 'exploration':
      return {
        border: 'border-emerald-500/30',
        bg: 'bg-emerald-500/5',
        accent: 'text-emerald-400',
      };
    case 'transit':
      return {
        border: 'border-orange-500/30',
        bg: 'bg-orange-500/5',
        accent: 'text-orange-400',
      };
    case 'zero':
      return {
        border: 'border-blue-500/30',
        bg: 'bg-blue-500/5',
        accent: 'text-blue-400',
      };
  }
}

function LocationPreview({ locations, icon: Icon, label, onRemove, onItemClick }: {
  locations: Location[];
  icon: typeof MapPin;
  label: string;
  onRemove?: (location: Location) => void;
  onItemClick?: (location: Location) => void;
}) {
  if (locations.length === 0) return null;

  return (
    <div className="space-y-1">
      {locations.map((loc) => (
        <div
          key={loc.id}
          className={`flex items-start gap-2 group ${onItemClick ? 'cursor-pointer hover:bg-zinc-800/50 -mx-2 px-2 py-1 rounded-lg transition-colors' : ''}`}
          onClick={(e) => {
            if (onItemClick) {
              e.stopPropagation();
              onItemClick(loc);
            }
          }}
        >
          <Icon className="w-4 h-4 text-zinc-500 mt-0.5 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-sm text-zinc-300 truncate">{loc.name}</p>
            <div className="flex items-center gap-1 text-xs text-zinc-500">
              {loc.city && <span>{loc.city}</span>}
              {loc.city && loc.distance_km !== undefined && <span>-</span>}
              {loc.distance_km !== undefined && (
                <span className="text-emerald-400">{loc.distance_km.toFixed(0)} km</span>
              )}
              {loc.time && (
                <>
                  <span className="mx-1">·</span>
                  <span>{loc.time}</span>
                </>
              )}
            </div>
          </div>
          {onRemove && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove(loc);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all"
              title="Remove from plan"
            >
              <X className="w-3 h-3 text-red-400" />
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

export function DayPlanCard({
  plan,
  isSelected,
  onSelect,
  onViewDetails,
  onRemoveItem,
}: DayPlanCardProps) {
  const style = getPlanStyle(plan.type);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleRemove = (itemType: 'event' | 'location', location: Location) => {
    // Extract numeric ID from the location id (e.g., 'event-123' -> 123)
    const numericId = parseInt(location.id.replace(/^(event-|loc-|overnight-)/, ''), 10);

    // Record the removal in the backend
    if (!isNaN(numericId)) {
      recordRemoval(itemType, numericId, location.name, {
        planId: plan.id,
        planType: plan.type,
      });
    }

    // Notify parent to update the plan
    if (onRemoveItem) {
      onRemoveItem(itemType, location.id);
    }
  };

  // Count total items in the plan
  const totalItems = plan.pois.length + plan.events.length + plan.overnight.length;

  return (
    <div
      className={`rounded-xl border-2 transition-all ${
        isSelected
          ? `${style.border} ${style.bg} ring-2 ring-offset-2 ring-offset-zinc-950 ring-${plan.type === 'exploration' ? 'emerald' : plan.type === 'transit' ? 'orange' : 'blue'}-500/50`
          : 'border-zinc-800 bg-zinc-900/50 hover:border-zinc-700'
      }`}
    >
      {/* Collapsible Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 pb-3 text-left"
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <PlanIcon type={plan.type} />
            <h3 className="font-semibold text-zinc-100">{plan.title}</h3>
          </div>
          <div className="flex items-center gap-3">
            <div className={`text-sm font-medium ${style.accent}`}>
              {plan.total_km} km
            </div>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-zinc-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-zinc-500" />
            )}
          </div>
        </div>
        <p className="text-sm text-zinc-400">{plan.description}</p>
        {/* Collapsed summary */}
        {!isExpanded && totalItems > 0 && (
          <div className="mt-2 flex items-center gap-3 text-xs text-zinc-500">
            {plan.events.length > 0 && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {plan.events.length} event{plan.events.length !== 1 ? 's' : ''}
              </span>
            )}
            {plan.pois.length > 0 && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {plan.pois.length} stop{plan.pois.length !== 1 ? 's' : ''}
              </span>
            )}
            {plan.overnight.length > 0 && (
              <span className="flex items-center gap-1">
                <Moon className="w-3 h-3" />
                {plan.overnight.length} overnight
              </span>
            )}
          </div>
        )}
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <>
          {/* Quick preview of locations */}
          <div className="px-4 pb-3 space-y-2">
            <LocationPreview
              locations={plan.events}
              icon={Calendar}
              label="Event"
              onRemove={onRemoveItem ? (loc) => handleRemove('event', loc) : undefined}
              onItemClick={(loc) => setSelectedLocation(loc)}
            />
            <LocationPreview
              locations={plan.pois}
              icon={MapPin}
              label="Visit"
              onRemove={onRemoveItem ? (loc) => handleRemove('location', loc) : undefined}
              onItemClick={(loc) => setSelectedLocation(loc)}
            />
            <LocationPreview
              locations={plan.overnight}
              icon={Moon}
              label="Overnight"
              onRemove={onRemoveItem ? (loc) => handleRemove('location', loc) : undefined}
              onItemClick={(loc) => setSelectedLocation(loc)}
            />
          </div>

          {/* Actions - only View details button */}
          <div className="px-4 pb-4">
            <button
              onClick={onViewDetails}
              className="w-full px-3 py-2 text-sm text-zinc-300 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
            >
              View details
            </button>
          </div>
        </>
      )}

      {/* Detail popup */}
      {selectedLocation && (
        <LocationDetailPopup
          location={selectedLocation}
          onClose={() => setSelectedLocation(null)}
        />
      )}
    </div>
  );
}
