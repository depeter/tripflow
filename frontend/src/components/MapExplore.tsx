'use client';

import { useEffect, useRef, useMemo, useState } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { MapItem } from '@/types/map';

// SVG icons for marker types (white, designed for dark backgrounds)
const MARKER_ICONS: Record<string, string> = {
  // Events
  event: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
  FESTIVAL: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>`,
  CONCERT: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>`,
  SPORTS: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10"/><path d="M12 2a15 15 0 0 0-4 10 15 15 0 0 0 4 10"/><path d="M2 12h20"/></svg>`,
  MARKET: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>`,
  EXHIBITION: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>`,
  THEATER: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="9" cy="9" r="1"/><circle cx="15" cy="9" r="1"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><circle cx="12" cy="12" r="10"/></svg>`,
  CULTURAL: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>`,
  FOOD: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M18 8h1a4 4 0 010 8h-1"/><path d="M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>`,
  OUTDOOR: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`,
  // Locations
  CAMPSITE: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L2 22h20L12 2z"/><path d="M12 22v-6"/><path d="M9 22l3-6 3 6"/></svg>`,
  PARKING: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 17V7h4a3 3 0 010 6H9"/></svg>`,
  REST_AREA: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M18 8h1a4 4 0 010 8h-1"/><path d="M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>`,
  SERVICE_AREA: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>`,
  POI: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>`,
  ATTRACTION: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
  RESTAURANT: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 002-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 00-5 5v6c0 1.1.9 2 2 2h3zm0 0v7"/></svg>`,
  HOTEL: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/><path d="M9 9h1"/><path d="M9 13h1"/><path d="M9 17h1"/></svg>`,
  ACTIVITY: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>`,
  // Default fallback
  default: `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>`,
};

// Marker colors by type
const MARKER_COLORS: Record<string, string> = {
  // Events
  event: '#a855f7', // purple
  FESTIVAL: '#ec4899', // pink
  CONCERT: '#f43f5e', // rose
  SPORTS: '#22c55e', // green
  MARKET: '#f59e0b', // amber
  EXHIBITION: '#06b6d4', // cyan
  THEATER: '#8b5cf6', // violet
  CULTURAL: '#6366f1', // indigo
  FOOD: '#ef4444', // red
  OUTDOOR: '#84cc16', // lime
  // Locations
  CAMPSITE: '#10b981', // emerald
  PARKING: '#64748b', // slate
  REST_AREA: '#0ea5e9', // sky
  SERVICE_AREA: '#3b82f6', // blue
  POI: '#f59e0b', // amber
  ATTRACTION: '#eab308', // yellow
  RESTAURANT: '#ef4444', // red
  HOTEL: '#a855f7', // purple
  ACTIVITY: '#22d3ee', // cyan
};

const getMarkerColor = (item: MapItem): string => {
  if (item.itemType === 'event') {
    return MARKER_COLORS[item.category || ''] || MARKER_COLORS.event;
  }
  return MARKER_COLORS[item.location_type || ''] || '#64748b';
};

const getMarkerIcon = (item: MapItem): string => {
  if (item.itemType === 'event') {
    return MARKER_ICONS[item.category || ''] || MARKER_ICONS.event;
  }
  return MARKER_ICONS[item.location_type || ''] || MARKER_ICONS.default;
};

// Create descriptive marker with icon and optional label
const createMarkerIcon = (item: MapItem, size: number = 36) => {
  const color = getMarkerColor(item);
  const icon = getMarkerIcon(item);
  const typeLabel = item.itemType === 'event'
    ? (item.category || 'Event')
    : (item.location_type || 'Place');

  // Create pin-shaped marker with icon
  return L.divIcon({
    className: 'custom-marker-descriptive',
    html: `
      <div style="
        position: relative;
        width: ${size}px;
        height: ${size + 12}px;
      ">
        <!-- Pin body -->
        <div style="
          width: ${size}px;
          height: ${size}px;
          background: ${color};
          border: 3px solid white;
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          box-shadow: 0 3px 10px rgba(0,0,0,0.4);
          position: absolute;
          top: 0;
          left: 0;
        ">
          <!-- Icon container (counter-rotate) -->
          <div style="
            width: 100%;
            height: 100%;
            transform: rotate(45deg);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 6px;
          ">
            ${icon}
          </div>
        </div>
        <!-- Pin point shadow -->
        <div style="
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 8px;
          height: 8px;
          background: rgba(0,0,0,0.2);
          border-radius: 50%;
          filter: blur(2px);
        "></div>
      </div>
    `,
    iconSize: [size, size + 12],
    iconAnchor: [size / 2, size + 10],
    popupAnchor: [0, -(size + 5)],
  });
};

// Format date for display
function formatEventDate(datetime: string): string {
  const date = new Date(datetime);
  return date.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Get the best image for an item
function getItemImage(item: MapItem): string | null {
  if (item.main_image_url) return item.main_image_url;
  if (item.images && item.images.length > 0) return item.images[0];
  return null;
}

// Create popup content
function createPopupContent(item: MapItem): string {
  const isEvent = item.itemType === 'event';
  const typeLabel = isEvent ? item.category : item.location_type;
  const typeColor = getMarkerColor(item);
  const imageUrl = getItemImage(item);

  let content = `
    <div style="min-width: 220px; max-width: 300px;">
  `;

  // Image header
  if (imageUrl) {
    content += `
      <div style="margin: -10px -10px 10px -10px; height: 120px; overflow: hidden; border-radius: 8px 8px 0 0;">
        <img
          src="${imageUrl}"
          alt="${item.name}"
          style="width: 100%; height: 100%; object-fit: cover;"
          onerror="this.style.display='none'; this.parentElement.style.display='none';"
        />
      </div>
    `;
  }

  content += `
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <span style="
          display: inline-block;
          padding: 2px 8px;
          background: ${typeColor}22;
          color: ${typeColor};
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
        ">${typeLabel || (isEvent ? 'Event' : 'Location')}</span>
        ${item.distance_km !== undefined ? `
          <span style="font-size: 11px; color: #a1a1aa;">${item.distance_km.toFixed(1)} km</span>
        ` : ''}
      </div>
      <h3 style="margin: 0 0 8px 0; font-size: 15px; font-weight: 600; color: #fafafa; line-height: 1.3;">
        ${item.name}
      </h3>
  `;

  if (isEvent && item.start_datetime) {
    content += `
      <p style="margin: 0 0 6px 0; font-size: 12px; color: #a855f7;">
        ${formatEventDate(item.start_datetime)}
      </p>
    `;
  }

  if (item.venue_name || item.city) {
    content += `
      <p style="margin: 0 0 6px 0; font-size: 12px; color: #a1a1aa;">
        ${item.venue_name || item.city}${item.city && item.venue_name ? `, ${item.city}` : ''}
      </p>
    `;
  }

  if (!isEvent && item.rating !== null && item.rating !== undefined) {
    content += `
      <p style="margin: 0 0 6px 0; font-size: 12px; color: #fbbf24;">
        ${'★'.repeat(Math.round(item.rating))}${'☆'.repeat(5 - Math.round(item.rating))}
        <span style="color: #71717a; margin-left: 4px;">${item.rating.toFixed(1)}</span>
        ${item.rating_count ? `<span style="color: #71717a;"> (${item.rating_count})</span>` : ''}
      </p>
    `;
  }

  if (item.price_type) {
    const priceLabels: Record<string, string> = {
      free: 'Free',
      paid: 'Paid',
      donation: 'Donation',
    };
    content += `
      <p style="margin: 0 0 6px 0; font-size: 12px; color: #10b981;">
        ${priceLabels[item.price_type] || item.price_type}
      </p>
    `;
  }

  if (item.website) {
    content += `
      <a href="${item.website}" target="_blank" rel="noopener noreferrer"
         style="display: inline-block; margin-top: 8px; font-size: 12px; color: #3b82f6; text-decoration: none;">
        Visit website →
      </a>
    `;
  }

  content += '</div>';
  return content;
}

// Component to handle marker clusters
interface MarkerClusterLayerProps {
  items: MapItem[];
  onItemClick?: (item: MapItem) => void;
}

function MarkerClusterLayer({ items, onItemClick }: MarkerClusterLayerProps) {
  const map = useMap();
  const clusterGroupRef = useRef<L.MarkerClusterGroup | null>(null);
  const [isReady, setIsReady] = useState(false);

  // Dynamically import markercluster JS (CSS is in globals.css)
  useEffect(() => {
    const loadMarkerCluster = async () => {
      // @ts-ignore - dynamic import of leaflet plugin
      await import('leaflet.markercluster');
      setIsReady(true);
    };
    loadMarkerCluster();
  }, []);

  useEffect(() => {
    if (!isReady) return;

    // Create cluster group with custom options
    // Lower maxClusterRadius = markers must be closer to cluster (more individual markers visible)
    // Lower disableClusteringAtZoom = clustering stops earlier when zooming in
    const clusterGroup = L.markerClusterGroup({
      chunkedLoading: true,
      maxClusterRadius: 35,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      disableClusteringAtZoom: 13,
      iconCreateFunction: (cluster) => {
        const count = cluster.getChildCount();
        const childMarkers = cluster.getAllChildMarkers();

        // Count events vs locations in cluster
        let eventCount = 0;
        let locationCount = 0;
        childMarkers.forEach((m: any) => {
          // Try to identify the type from the marker's icon class
          const iconHtml = m.options?.icon?.options?.html || '';
          if (iconHtml.includes('#a855f7') || iconHtml.includes('#ec4899') ||
              iconHtml.includes('#f43f5e') || iconHtml.includes('#8b5cf6') ||
              iconHtml.includes('#6366f1')) {
            eventCount++;
          } else {
            locationCount++;
          }
        });

        // Determine size based on count
        let sizeClass = 44;
        let fontSize = '13px';
        if (count >= 100) {
          sizeClass = 56;
          fontSize = '15px';
        } else if (count >= 10) {
          sizeClass = 50;
          fontSize = '14px';
        }

        // Determine gradient based on contents
        let gradient = 'linear-gradient(135deg, #10b981 0%, #059669 100%)'; // Green (locations)
        if (eventCount > locationCount) {
          gradient = 'linear-gradient(135deg, #a855f7 0%, #7c3aed 100%)'; // Purple (events)
        } else if (eventCount > 0 && locationCount > 0) {
          gradient = 'linear-gradient(135deg, #a855f7 0%, #10b981 100%)'; // Mixed
        }

        return L.divIcon({
          html: `
            <div style="
              width: ${sizeClass}px;
              height: ${sizeClass}px;
              background: ${gradient};
              border: 3px solid white;
              border-radius: 50%;
              box-shadow: 0 4px 14px rgba(0,0,0,0.35);
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              color: white;
              font-weight: 700;
              font-size: ${fontSize};
              line-height: 1;
            ">
              <span>${count}</span>
              <span style="font-size: 8px; font-weight: 500; opacity: 0.9; margin-top: 1px;">
                ${eventCount > 0 && locationCount > 0 ? 'mixed' : eventCount > 0 ? 'events' : 'places'}
              </span>
            </div>
          `,
          className: `marker-cluster marker-cluster-${count >= 100 ? 'large' : count >= 10 ? 'medium' : 'small'}`,
          iconSize: L.point(sizeClass, sizeClass),
        });
      },
    });

    // Add markers to cluster group
    items.forEach((item) => {
      const marker = L.marker([item.latitude, item.longitude], {
        icon: createMarkerIcon(item),
      });

      marker.bindPopup(createPopupContent(item), {
        maxWidth: 300,
        className: 'custom-popup',
      });

      if (onItemClick) {
        marker.on('click', () => onItemClick(item));
      }

      clusterGroup.addLayer(marker);
    });

    map.addLayer(clusterGroup);
    clusterGroupRef.current = clusterGroup;

    return () => {
      map.removeLayer(clusterGroup);
    };
  }, [map, items, onItemClick, isReady]);

  return null;
}

// Component to handle map view changes
interface MapControllerProps {
  center: [number, number];
  zoom: number;
  onMoveEnd?: (bounds: L.LatLngBounds, center: L.LatLng, zoom: number) => void;
}

function MapController({ center, zoom, onMoveEnd }: MapControllerProps) {
  const map = useMap();

  useEffect(() => {
    map.setView(center, zoom);
  }, [map, center, zoom]);

  useEffect(() => {
    if (onMoveEnd) {
      const handler = () => {
        onMoveEnd(map.getBounds(), map.getCenter(), map.getZoom());
      };
      map.on('moveend', handler);
      return () => {
        map.off('moveend', handler);
      };
    }
  }, [map, onMoveEnd]);

  return null;
}

// User location marker
interface UserLocationProps {
  position: { lat: number; lng: number };
}

function UserLocationMarker({ position }: UserLocationProps) {
  const map = useMap();

  useEffect(() => {
    const marker = L.marker([position.lat, position.lng], {
      icon: L.divIcon({
        className: 'user-location-marker',
        html: `<div style="
          width: 24px;
          height: 24px;
          background: #3b82f6;
          border: 4px solid white;
          border-radius: 50%;
          box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.2), 0 2px 8px rgba(0,0,0,0.3);
        "></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      }),
      zIndexOffset: 1000,
    });

    marker.bindPopup('<strong>Your location</strong>', { className: 'custom-popup' });
    marker.addTo(map);

    return () => {
      marker.remove();
    };
  }, [map, position]);

  return null;
}

export interface MapExploreProps {
  items: MapItem[];
  center?: [number, number];
  zoom?: number;
  userLocation?: { lat: number; lng: number };
  onItemClick?: (item: MapItem) => void;
  onMoveEnd?: (bounds: L.LatLngBounds, center: L.LatLng, zoom: number) => void;
  height?: string;
}

export default function MapExplore({
  items,
  center = [50.85, 4.35], // Default: Brussels, Belgium
  zoom = 9, // ~60km view
  userLocation,
  onItemClick,
  onMoveEnd,
  height = '100%',
}: MapExploreProps) {
  // Memoize items to prevent unnecessary re-renders
  const memoizedItems = useMemo(() => items, [items]);

  return (
    <div style={{ height, width: '100%' }} className="rounded-xl overflow-hidden">
      <style jsx global>{`
        .custom-popup .leaflet-popup-content-wrapper {
          background: #18181b;
          color: #fafafa;
          border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }
        .custom-popup .leaflet-popup-tip {
          background: #18181b;
        }
        .custom-popup .leaflet-popup-close-button {
          color: #a1a1aa;
        }
        .custom-popup .leaflet-popup-close-button:hover {
          color: #fafafa;
        }
        .leaflet-container {
          background: #09090b;
        }
      `}</style>
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        className="h-full w-full"
        style={{ background: '#09090b' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapController center={center} zoom={zoom} onMoveEnd={onMoveEnd} />
        <MarkerClusterLayer items={memoizedItems} onItemClick={onItemClick} />
        {userLocation && <UserLocationMarker position={userLocation} />}
      </MapContainer>
    </div>
  );
}
