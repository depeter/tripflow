'use client';

import { useState } from 'react';
import { MapPin, Star, Check, X, ChevronRight, Sparkles } from 'lucide-react';
import type { JourneyWaypoint } from '@/types/journey';

interface WaypointListProps {
  waypoints: JourneyWaypoint[];
  currentDistanceKm: number;
  onWaypointSelect?: (waypoint: JourneyWaypoint) => void;
  onMarkVisited?: (waypoint: JourneyWaypoint) => void;
  onMarkSkipped?: (waypoint: JourneyWaypoint) => void;
}

function WaypointCard({
  waypoint,
  isUpcoming,
  isNext,
  onSelect,
  onMarkVisited,
  onMarkSkipped,
}: {
  waypoint: JourneyWaypoint;
  isUpcoming: boolean;
  isNext: boolean;
  onSelect?: () => void;
  onMarkVisited?: () => void;
  onMarkSkipped?: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  const getStatusStyles = () => {
    switch (waypoint.type) {
      case 'visited':
        return 'bg-emerald-500/10 border-emerald-500/30';
      case 'skipped':
        return 'bg-zinc-800/30 border-zinc-700 opacity-50';
      case 'mustSee':
        return isNext
          ? 'bg-blue-500/10 border-blue-500/30 ring-2 ring-blue-500/20'
          : 'bg-zinc-800/50 border-zinc-700';
      default:
        return 'bg-zinc-800/50 border-zinc-700';
    }
  };

  return (
    <div
      className={`rounded-xl border p-4 transition-all ${getStatusStyles()}`}
    >
      <div className="flex items-start gap-3">
        {/* Status indicator */}
        <div className="mt-1">
          {waypoint.type === 'visited' ? (
            <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center">
              <Check className="w-4 h-4 text-white" />
            </div>
          ) : waypoint.type === 'skipped' ? (
            <div className="w-6 h-6 rounded-full bg-zinc-600 flex items-center justify-center">
              <X className="w-4 h-4 text-zinc-400" />
            </div>
          ) : isNext ? (
            <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center animate-pulse">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
          ) : (
            <div className="w-6 h-6 rounded-full bg-zinc-700 flex items-center justify-center">
              <MapPin className="w-4 h-4 text-zinc-400" />
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-medium text-zinc-100">{waypoint.name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-zinc-500">
                  {waypoint.distance_from_start_km} km from start
                </span>
                {waypoint.rating && (
                  <span className="flex items-center gap-1 text-xs text-amber-400">
                    <Star className="w-3 h-3 fill-current" />
                    {waypoint.rating}
                  </span>
                )}
              </div>
            </div>

            {isNext && (
              <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 rounded-full">
                Next up
              </span>
            )}
          </div>

          {/* Tags */}
          {waypoint.tags && waypoint.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {waypoint.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-0.5 bg-zinc-700 text-zinc-400 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Description (expandable) */}
          {waypoint.description && (
            <div className="mt-2">
              <p className={`text-sm text-zinc-400 ${expanded ? '' : 'line-clamp-2'}`}>
                {waypoint.description}
              </p>
              {waypoint.description.length > 100 && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="text-xs text-zinc-500 hover:text-zinc-300 mt-1"
                >
                  {expanded ? 'Show less' : 'Show more'}
                </button>
              )}
            </div>
          )}

          {/* Actions for upcoming waypoints */}
          {isUpcoming && waypoint.type === 'mustSee' && (
            <div className="flex gap-2 mt-3">
              <button
                onClick={onMarkVisited}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 rounded-lg transition-colors"
              >
                <Check className="w-4 h-4" />
                Visited
              </button>
              <button
                onClick={onMarkSkipped}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm bg-zinc-700 text-zinc-400 hover:bg-zinc-600 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
                Skip
              </button>
              <button
                onClick={onSelect}
                className="px-3 py-2 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 rounded-lg transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Visited date */}
          {waypoint.visited_date && (
            <p className="text-xs text-emerald-500 mt-2">
              Visited on {new Date(waypoint.visited_date).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export function WaypointList({
  waypoints,
  currentDistanceKm,
  onWaypointSelect,
  onMarkVisited,
  onMarkSkipped,
}: WaypointListProps) {
  // Sort by distance and separate into upcoming and passed
  const sortedWaypoints = [...waypoints].sort(
    (a, b) => a.distance_from_start_km - b.distance_from_start_km
  );

  const upcomingWaypoints = sortedWaypoints.filter(
    (w) => w.distance_from_start_km > currentDistanceKm && w.type !== 'visited' && w.type !== 'skipped'
  );
  const passedWaypoints = sortedWaypoints.filter(
    (w) => w.distance_from_start_km <= currentDistanceKm || w.type === 'visited' || w.type === 'skipped'
  );

  const nextWaypoint = upcomingWaypoints[0];

  return (
    <div className="space-y-4">
      {/* Upcoming section */}
      {upcomingWaypoints.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-zinc-400 mb-3 uppercase tracking-wider">
            Coming Up ({upcomingWaypoints.length})
          </h3>
          <div className="space-y-3">
            {upcomingWaypoints.map((waypoint) => (
              <WaypointCard
                key={waypoint.id}
                waypoint={waypoint}
                isUpcoming={true}
                isNext={waypoint.id === nextWaypoint?.id}
                onSelect={() => onWaypointSelect?.(waypoint)}
                onMarkVisited={() => onMarkVisited?.(waypoint)}
                onMarkSkipped={() => onMarkSkipped?.(waypoint)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Passed section */}
      {passedWaypoints.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-zinc-400 mb-3 uppercase tracking-wider">
            Behind You ({passedWaypoints.length})
          </h3>
          <div className="space-y-3">
            {passedWaypoints.reverse().map((waypoint) => (
              <WaypointCard
                key={waypoint.id}
                waypoint={waypoint}
                isUpcoming={false}
                isNext={false}
                onSelect={() => onWaypointSelect?.(waypoint)}
              />
            ))}
          </div>
        </div>
      )}

      {waypoints.length === 0 && (
        <div className="text-center py-8">
          <MapPin className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
          <p className="text-zinc-500">No waypoints added yet</p>
          <p className="text-sm text-zinc-600 mt-1">
            We&apos;ll suggest must-see places along your route
          </p>
        </div>
      )}
    </div>
  );
}
