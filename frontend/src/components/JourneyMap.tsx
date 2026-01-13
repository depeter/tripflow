'use client';

import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Journey, JourneyWaypoint } from '@/types/journey';

// Custom markers
const createIcon = (color: string, size: number = 12) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: ${size}px;
      height: ${size}px;
      background: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

const startIcon = createIcon('#10b981', 16); // emerald
const destIcon = createIcon('#f59e0b', 16); // amber
const mustSeeIcon = createIcon('#3b82f6', 12); // blue
const visitedIcon = createIcon('#22c55e', 10); // green
const currentIcon = L.divIcon({
  className: 'current-marker',
  html: `<div style="
    width: 20px;
    height: 20px;
    background: #ef4444;
    border: 3px solid white;
    border-radius: 50%;
    box-shadow: 0 0 0 4px rgba(239,68,68,0.3), 0 2px 4px rgba(0,0,0,0.3);
  "></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

function getIcon(type: JourneyWaypoint['type']) {
  switch (type) {
    case 'start':
      return startIcon;
    case 'destination':
      return destIcon;
    case 'visited':
      return visitedIcon;
    case 'mustSee':
      return mustSeeIcon;
    default:
      return mustSeeIcon;
  }
}

interface JourneyMapProps {
  journey: Journey;
  currentPosition?: { lat: number; lng: number };
  onWaypointClick?: (waypoint: JourneyWaypoint) => void;
  height?: string;
}

export default function JourneyMap({
  journey,
  currentPosition,
  onWaypointClick,
  height = '300px',
}: JourneyMapProps) {
  // Calculate bounds to fit all waypoints
  const allPoints = [
    journey.start,
    ...journey.waypoints,
    journey.destination,
  ];

  const bounds = L.latLngBounds(
    allPoints.map((p) => [p.coordinates.lat, p.coordinates.lng])
  );

  // Create corridor line
  const corridorPoints: [number, number][] = [
    [journey.start.coordinates.lat, journey.start.coordinates.lng],
    ...journey.waypoints
      .sort((a, b) => a.distance_from_start_km - b.distance_from_start_km)
      .map((w) => [w.coordinates.lat, w.coordinates.lng] as [number, number]),
    [journey.destination.coordinates.lat, journey.destination.coordinates.lng],
  ];

  // Progress line (visited portion)
  const progressPoints = corridorPoints.slice(
    0,
    Math.max(2, Math.floor((journey.progress_km / journey.total_distance_km) * corridorPoints.length))
  );

  return (
    <div style={{ height }} className="rounded-xl overflow-hidden">
      <MapContainer
        bounds={bounds}
        boundsOptions={{ padding: [30, 30] }}
        scrollWheelZoom={true}
        className="h-full w-full"
        style={{ background: '#18181b' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Full corridor (faded) */}
        <Polyline
          positions={corridorPoints}
          color="#3f3f46"
          weight={4}
          opacity={0.5}
          dashArray="10, 10"
        />

        {/* Progress line (solid) */}
        {progressPoints.length > 1 && (
          <Polyline
            positions={progressPoints}
            color="#10b981"
            weight={4}
            opacity={0.8}
          />
        )}

        {/* Start marker */}
        <Marker
          position={[journey.start.coordinates.lat, journey.start.coordinates.lng]}
          icon={startIcon}
        >
          <Popup>
            <div className="text-sm">
              <strong>Start:</strong> {journey.start.name}
            </div>
          </Popup>
        </Marker>

        {/* Destination marker */}
        <Marker
          position={[journey.destination.coordinates.lat, journey.destination.coordinates.lng]}
          icon={destIcon}
        >
          <Popup>
            <div className="text-sm">
              <strong>Destination:</strong> {journey.destination.name}
            </div>
          </Popup>
        </Marker>

        {/* Waypoint markers */}
        {journey.waypoints.map((waypoint) => (
          <Marker
            key={waypoint.id}
            position={[waypoint.coordinates.lat, waypoint.coordinates.lng]}
            icon={getIcon(waypoint.type)}
            eventHandlers={{
              click: () => onWaypointClick?.(waypoint),
            }}
          >
            <Popup>
              <div className="text-sm">
                <strong>{waypoint.name}</strong>
                {waypoint.description && (
                  <p className="text-zinc-600 mt-1">{waypoint.description}</p>
                )}
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Current position marker */}
        {currentPosition && (
          <Marker
            position={[currentPosition.lat, currentPosition.lng]}
            icon={currentIcon}
          >
            <Popup>
              <div className="text-sm">
                <strong>You are here</strong>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}
