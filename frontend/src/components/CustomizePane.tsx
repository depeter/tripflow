'use client';

import { useState } from 'react';
import { Calendar, MapPin, Moon, RefreshCw, Plus, Check, X, Clock, DollarSign, Zap } from 'lucide-react';
import type { DayPlanType, Location } from '@/types/trip';

interface CustomizePaneProps {
  plan: DayPlanType;
  alternativeEvents?: Location[];
  alternativeStops?: Location[];
  alternativeOvernights?: Location[];
  onUpdatePlan: (updatedPlan: DayPlanType) => void;
}

interface LocationRowProps {
  location: Location;
  icon: typeof MapPin;
  isSelected?: boolean;
  onReplace?: () => void;
  onSelect?: () => void;
  showActions?: boolean;
}

function LocationRow({
  location,
  icon: Icon,
  isSelected,
  onReplace,
  onSelect,
  showActions = true,
}: LocationRowProps) {
  return (
    <div
      className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
        isSelected
          ? 'bg-emerald-500/10 border border-emerald-500/30'
          : 'bg-zinc-800/50 hover:bg-zinc-800'
      }`}
    >
      {/* Selection indicator for overnight options */}
      {onSelect && (
        <button
          onClick={onSelect}
          className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
            isSelected
              ? 'border-emerald-500 bg-emerald-500'
              : 'border-zinc-600 hover:border-zinc-400'
          }`}
        >
          {isSelected && <Check className="w-3 h-3 text-white" />}
        </button>
      )}

      {/* Icon */}
      <Icon className="w-4 h-4 text-zinc-500 flex-shrink-0" />

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-zinc-200 truncate">{location.name}</p>
        <div className="flex items-center gap-3 text-xs text-zinc-500">
          {location.distance_km !== undefined && (
            <span>{location.distance_km} km</span>
          )}
          {location.detour_km !== undefined && (
            <span className="text-orange-400">+{location.detour_km} km detour</span>
          )}
          {location.time && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {location.time}
            </span>
          )}
          {location.price && (
            <span className="flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              {location.price}
            </span>
          )}
        </div>
        {location.amenities && location.amenities.length > 0 && (
          <div className="flex gap-1 mt-1">
            {location.amenities.slice(0, 3).map((amenity) => (
              <span
                key={amenity}
                className="text-xs px-2 py-0.5 bg-zinc-700 rounded text-zinc-400"
              >
                {amenity}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Replace action */}
      {showActions && onReplace && (
        <button
          onClick={onReplace}
          className="px-2 py-1 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 rounded transition-colors flex items-center gap-1"
        >
          <RefreshCw className="w-3 h-3" />
          Replace
        </button>
      )}
    </div>
  );
}

function SectionHeader({
  icon: Icon,
  title,
  onAdd,
}: {
  icon: typeof Calendar;
  title: string;
  onAdd?: () => void;
}) {
  return (
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-zinc-400" />
        <h4 className="text-sm font-medium text-zinc-300">{title}</h4>
      </div>
      {onAdd && (
        <button
          onClick={onAdd}
          className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <Plus className="w-3 h-3" />
          Add
        </button>
      )}
    </div>
  );
}

export function CustomizePane({
  plan,
  alternativeEvents = [],
  alternativeStops = [],
  alternativeOvernights = [],
  onUpdatePlan,
}: CustomizePaneProps) {
  const [selectedOvernightId, setSelectedOvernightId] = useState<string>(
    plan.overnight[0]?.id || ''
  );
  const [showAlternativeEvents, setShowAlternativeEvents] = useState(false);
  const [showAlternativeStops, setShowAlternativeStops] = useState(false);

  const handleSelectOvernight = (id: string) => {
    setSelectedOvernightId(id);
    const selectedOvernight = [...plan.overnight, ...alternativeOvernights].find(
      (o) => o.id === id
    );
    if (selectedOvernight) {
      onUpdatePlan({
        ...plan,
        overnight: [selectedOvernight],
      });
    }
  };

  const handleReplaceEvent = (index: number, newEvent: Location) => {
    const newEvents = [...plan.events];
    newEvents[index] = newEvent;
    onUpdatePlan({ ...plan, events: newEvents });
    setShowAlternativeEvents(false);
  };

  const handleReplaceStop = (index: number, newStop: Location) => {
    const newPois = [...plan.pois];
    newPois[index] = newStop;
    onUpdatePlan({ ...plan, pois: newPois });
    setShowAlternativeStops(false);
  };

  return (
    <div className="space-y-6 bg-zinc-900/50 rounded-xl p-4">
      {/* Plan header */}
      <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
        <h3 className="font-semibold text-zinc-100">{plan.title}</h3>
        <span className="text-sm text-zinc-400">{plan.total_km} km total</span>
      </div>

      {/* Events section */}
      <div>
        <SectionHeader
          icon={Calendar}
          title="Events Today Near You"
          onAdd={() => setShowAlternativeEvents(!showAlternativeEvents)}
        />
        <div className="space-y-2">
          {plan.events.length > 0 ? (
            plan.events.map((event, idx) => (
              <LocationRow
                key={event.id}
                location={event}
                icon={Calendar}
                onReplace={() => setShowAlternativeEvents(true)}
              />
            ))
          ) : (
            <p className="text-sm text-zinc-500 italic">No events today</p>
          )}
        </div>

        {/* Alternative events */}
        {showAlternativeEvents && alternativeEvents.length > 0 && (
          <div className="mt-2 p-3 bg-zinc-800/50 rounded-lg border border-zinc-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-zinc-400">Alternative events</span>
              <button
                onClick={() => setShowAlternativeEvents(false)}
                className="text-zinc-500 hover:text-zinc-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2">
              {alternativeEvents.map((event) => (
                <button
                  key={event.id}
                  onClick={() => handleReplaceEvent(0, event)}
                  className="w-full text-left"
                >
                  <LocationRow
                    location={event}
                    icon={Calendar}
                    showActions={false}
                  />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Stops section */}
      <div>
        <SectionHeader
          icon={MapPin}
          title="Stops Along Your Route"
          onAdd={() => setShowAlternativeStops(!showAlternativeStops)}
        />
        <div className="space-y-2">
          {plan.pois.length > 0 ? (
            plan.pois.map((poi, idx) => (
              <LocationRow
                key={poi.id}
                location={poi}
                icon={MapPin}
                onReplace={() => setShowAlternativeStops(true)}
              />
            ))
          ) : (
            <p className="text-sm text-zinc-500 italic">Direct route, no stops</p>
          )}
        </div>

        {/* Alternative stops */}
        {showAlternativeStops && alternativeStops.length > 0 && (
          <div className="mt-2 p-3 bg-zinc-800/50 rounded-lg border border-zinc-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-zinc-400">Alternative stops</span>
              <button
                onClick={() => setShowAlternativeStops(false)}
                className="text-zinc-500 hover:text-zinc-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2">
              {alternativeStops.map((stop) => (
                <button
                  key={stop.id}
                  onClick={() => handleReplaceStop(0, stop)}
                  className="w-full text-left"
                >
                  <LocationRow
                    location={stop}
                    icon={MapPin}
                    showActions={false}
                  />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Overnight section */}
      <div>
        <SectionHeader icon={Moon} title="Overnight Options" />
        <div className="space-y-2">
          {[...plan.overnight, ...alternativeOvernights].map((overnight) => (
            <LocationRow
              key={overnight.id}
              location={overnight}
              icon={Moon}
              isSelected={overnight.id === selectedOvernightId}
              onSelect={() => handleSelectOvernight(overnight.id)}
              showActions={false}
            />
          ))}
        </div>
      </div>

      {/* Confirm button */}
      <button className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2">
        <Check className="w-4 h-4" />
        Confirm Today&apos;s Plan
      </button>
    </div>
  );
}
