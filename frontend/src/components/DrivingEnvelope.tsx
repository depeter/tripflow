'use client';

import { useState, useCallback } from 'react';
import { Car } from 'lucide-react';

interface DrivingEnvelopeProps {
  value: number;
  max: number;
  onChange: (km: number) => void;
}

const MARKERS = [
  { label: 'Local only', km: 0, color: 'text-emerald-400' },
  { label: 'Light', km: 60, color: 'text-emerald-400' },
  { label: 'Normal', km: 300, color: 'text-yellow-400' },
  { label: 'Heavy', km: 600, color: 'text-orange-400' },
];

export function DrivingEnvelope({ value, max, onChange }: DrivingEnvelopeProps) {
  const [isDragging, setIsDragging] = useState(false);

  const getLabel = useCallback((km: number): string => {
    if (km <= 20) return 'Local Only';
    if (km <= 150) return 'Light Driving';
    if (km <= 400) return 'Normal Driving';
    return 'Heavy Transit';
  }, []);

  const getColor = useCallback((km: number): string => {
    if (km <= 20) return 'bg-emerald-500';
    if (km <= 150) return 'bg-emerald-400';
    if (km <= 400) return 'bg-yellow-400';
    return 'bg-orange-500';
  }, []);

  const percentage = (value / max) * 100;

  return (
    <div className="space-y-4">
      {/* Header with current value */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Car className="w-4 h-4 text-zinc-400" />
          <span className="text-sm text-zinc-400">How much driving today?</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-zinc-100">{value}</span>
          <span className="text-sm text-zinc-500">km</span>
        </div>
      </div>

      {/* Slider track */}
      <div className="relative pt-2 pb-6">
        <div className="relative h-2 bg-zinc-800 rounded-full">
          {/* Filled portion */}
          <div
            className={`absolute h-full rounded-full transition-all ${getColor(value)}`}
            style={{ width: `${percentage}%` }}
          />

          {/* Slider input */}
          <input
            type="range"
            min={0}
            max={max}
            step={10}
            value={value}
            onChange={(e) => onChange(parseInt(e.target.value))}
            onMouseDown={() => setIsDragging(true)}
            onMouseUp={() => setIsDragging(false)}
            onTouchStart={() => setIsDragging(true)}
            onTouchEnd={() => setIsDragging(false)}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />

          {/* Thumb indicator */}
          <div
            className={`absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-white shadow-lg border-2 transition-transform ${
              isDragging ? 'scale-125 border-blue-500' : 'border-zinc-300'
            }`}
            style={{ left: `calc(${percentage}% - 10px)` }}
          />
        </div>

        {/* Markers */}
        <div className="flex justify-between mt-3 px-1">
          {MARKERS.map((marker) => (
            <button
              key={marker.label}
              onClick={() => onChange(marker.km)}
              className={`text-xs ${
                Math.abs(value - marker.km) < 30
                  ? marker.color + ' font-medium'
                  : 'text-zinc-600'
              } hover:text-zinc-300 transition-colors`}
            >
              {marker.label}
            </button>
          ))}
        </div>
      </div>

      {/* Current mode label */}
      <div className="text-center">
        <span className={`text-sm font-medium ${getColor(value).replace('bg-', 'text-')}`}>
          {getLabel(value)}
        </span>
      </div>
    </div>
  );
}
