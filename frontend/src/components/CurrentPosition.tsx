'use client';

import { MapPin, Navigation, Cloud, Sun, CloudRain } from 'lucide-react';
import dynamic from 'next/dynamic';
import type { Coordinates, Weather } from '@/types/trip';

// Dynamic import for Leaflet (no SSR)
const MiniMap = dynamic(() => import('./MiniMap'), {
  ssr: false,
  loading: () => <div className="h-32 bg-zinc-800 rounded-lg animate-pulse" />
});

interface CurrentPositionProps {
  coordinates: Coordinates | null;
  address: string;
  destination: { name: string; coordinates: Coordinates } | null;
  weather: Weather | null;
}

function WeatherIcon({ condition }: { condition: string }) {
  const lower = condition.toLowerCase();
  if (lower.includes('rain') || lower.includes('drizzle')) {
    return <CloudRain className="w-6 h-6 text-blue-400" />;
  }
  if (lower.includes('cloud') || lower.includes('overcast')) {
    return <Cloud className="w-6 h-6 text-zinc-400" />;
  }
  return <Sun className="w-6 h-6 text-yellow-400" />;
}

function calculateDistance(from: Coordinates, to: Coordinates): number {
  const R = 6371; // Earth's radius in km
  const dLat = (to.lat - from.lat) * Math.PI / 180;
  const dLon = (to.lng - from.lng) * Math.PI / 180;
  const a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(from.lat * Math.PI / 180) * Math.cos(to.lat * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return Math.round(R * c);
}

export function CurrentPosition({
  coordinates,
  address,
  destination,
  weather
}: CurrentPositionProps) {
  const distanceToDestination = coordinates && destination
    ? calculateDistance(coordinates, destination.coordinates)
    : null;

  return (
    <div className="space-y-3">
      {/* Map snippet */}
      <div className="h-32 rounded-lg overflow-hidden">
        {coordinates ? (
          <MiniMap center={coordinates} />
        ) : (
          <div className="h-full bg-zinc-800 flex items-center justify-center">
            <span className="text-zinc-500 text-sm">Locating...</span>
          </div>
        )}
      </div>

      {/* Info tiles */}
      <div className="grid grid-cols-3 gap-2">
        {/* Location */}
        <div className="bg-zinc-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <MapPin className="w-4 h-4 text-emerald-500" />
            <span className="text-xs text-zinc-500">Location</span>
          </div>
          <p className="text-sm text-zinc-200 truncate" title={address}>
            {address || 'Unknown'}
          </p>
        </div>

        {/* Weather */}
        <div className="bg-zinc-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            {weather ? (
              <WeatherIcon condition={weather.condition} />
            ) : (
              <Cloud className="w-4 h-4 text-zinc-500" />
            )}
            <span className="text-xs text-zinc-500">Weather</span>
          </div>
          {weather ? (
            <p className="text-sm text-zinc-200">
              {weather.temp_c}°C
            </p>
          ) : (
            <p className="text-sm text-zinc-400">--</p>
          )}
        </div>

        {/* Distance to destination */}
        <div className="bg-zinc-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Navigation className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-zinc-500">To dest.</span>
          </div>
          {distanceToDestination !== null ? (
            <p className="text-sm text-zinc-200">
              {distanceToDestination.toLocaleString()} km
            </p>
          ) : (
            <p className="text-sm text-zinc-400">--</p>
          )}
        </div>
      </div>

      {/* Destination name */}
      {destination && (
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <span>→</span>
          <span>{destination.name}</span>
        </div>
      )}
    </div>
  );
}
