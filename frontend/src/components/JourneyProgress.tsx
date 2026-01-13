'use client';

import { MapPin, Flag, Calendar, TrendingUp } from 'lucide-react';
import type { Journey, JourneyStats } from '@/types/journey';

interface JourneyProgressProps {
  journey: Journey;
  stats: JourneyStats;
}

export function JourneyProgress({ journey, stats }: JourneyProgressProps) {
  const progressPercent = (journey.progress_km / journey.total_distance_km) * 100;

  return (
    <div className="space-y-4">
      {/* Journey header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100">{journey.name}</h2>
          <p className="text-sm text-zinc-500">Day {journey.current_day}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-zinc-100">
            {Math.round(progressPercent)}%
          </p>
          <p className="text-xs text-zinc-500">complete</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="relative">
        <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Start and end labels */}
        <div className="flex justify-between mt-2">
          <div className="flex items-center gap-1 text-xs text-zinc-400">
            <MapPin className="w-3 h-3 text-emerald-500" />
            <span className="truncate max-w-[100px]">{journey.start.name}</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-zinc-400">
            <span className="truncate max-w-[100px]">{journey.destination.name}</span>
            <Flag className="w-3 h-3 text-amber-500" />
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-zinc-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-emerald-500" />
            <span className="text-xs text-zinc-500">Distance</span>
          </div>
          <p className="text-lg font-semibold text-zinc-100">
            {stats.distance_covered_km.toLocaleString()} km
          </p>
          <p className="text-xs text-zinc-500">
            {stats.distance_remaining_km.toLocaleString()} km remaining
          </p>
        </div>

        <div className="bg-zinc-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Calendar className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-zinc-500">Days</span>
          </div>
          <p className="text-lg font-semibold text-zinc-100">
            {stats.days_traveled}
          </p>
          <p className="text-xs text-zinc-500">
            ~{stats.avg_km_per_day} km/day avg
          </p>
        </div>

        <div className="bg-zinc-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <MapPin className="w-4 h-4 text-purple-500" />
            <span className="text-xs text-zinc-500">Places Visited</span>
          </div>
          <p className="text-lg font-semibold text-zinc-100">
            {stats.places_visited}
          </p>
          <p className="text-xs text-zinc-500">
            {stats.places_remaining} must-sees left
          </p>
        </div>

        <div className="bg-zinc-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Flag className="w-4 h-4 text-amber-500" />
            <span className="text-xs text-zinc-500">ETA</span>
          </div>
          <p className="text-lg font-semibold text-zinc-100">
            ~{Math.ceil(stats.distance_remaining_km / stats.avg_km_per_day)} days
          </p>
          <p className="text-xs text-zinc-500">at current pace</p>
        </div>
      </div>
    </div>
  );
}
