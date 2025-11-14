import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

// Fix for default marker icons in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom numbered marker icon
const createNumberedIcon = (number) => {
  return L.divIcon({
    className: 'numbered-marker',
    html: `<div class="marker-pin"><span>${number}</span></div>`,
    iconSize: [30, 42],
    iconAnchor: [15, 42],
    popupAnchor: [0, -42]
  });
};

// Component to update map view when bounds change
const MapUpdater = ({ center, zoom, bounds }) => {
  const map = useMap();

  useEffect(() => {
    if (bounds && bounds.length === 2) {
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (center) {
      map.setView(center, zoom || 10);
    }
  }, [center, zoom, bounds, map]);

  return null;
};

// Component to handle map clicks
const MapClickHandler = ({ onMapClick }) => {
  const map = useMap();

  useEffect(() => {
    if (!onMapClick) return;

    const handleClick = (e) => {
      const { lat, lng } = e.latlng;
      onMapClick({ lat, lng });
    };

    map.on('click', handleClick);

    return () => {
      map.off('click', handleClick);
    };
  }, [map, onMapClick]);

  return null;
};

const MapView = ({
  center = [51.505, -0.09],
  zoom = 13,
  markers = [],
  route = [],
  circle = null,
  onMarkerDrag = null,
  onMapClick = null,
  className = ''
}) => {
  const mapRef = useRef(null);

  // Calculate bounds if we have markers or route
  const calculateBounds = () => {
    const points = [];

    markers.forEach(marker => {
      if (marker.position) {
        points.push(marker.position);
      }
    });

    route.forEach(point => {
      if (Array.isArray(point) && point.length === 2) {
        points.push(point);
      }
    });

    if (circle && circle.center) {
      points.push(circle.center);
    }

    if (points.length > 1) {
      return L.latLngBounds(points);
    }

    return null;
  };

  const bounds = calculateBounds();

  return (
    <div className={`map-view-container ${className}`}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapUpdater center={center} zoom={zoom} bounds={bounds} />
        <MapClickHandler onMapClick={onMapClick} />

        {/* Markers */}
        {markers.map((marker, index) => {
          const markerProps = {
            position: marker.position,
            draggable: marker.draggable,
            eventHandlers: {
              dragend: (e) => {
                if (onMarkerDrag) {
                  const newPos = e.target.getLatLng();
                  onMarkerDrag(index, [newPos.lat, newPos.lng]);
                }
              }
            }
          };

          // Only add icon prop if we have a custom icon
          if (marker.numbered) {
            markerProps.icon = createNumberedIcon(marker.number || index + 1);
          }

          return (
            <Marker key={marker.id || index} {...markerProps}>
              {marker.popup && <Popup>{marker.popup}</Popup>}
            </Marker>
          );
        })}

        {/* Route polyline */}
        {route && route.length > 1 && (
          <Polyline
            positions={route}
            color="#3B82F6"
            weight={4}
            opacity={0.7}
          />
        )}

        {/* Circle (for radius visualization) */}
        {circle && circle.center && (
          <Circle
            center={circle.center}
            radius={circle.radius || 10000}
            pathOptions={{
              color: '#10B981',
              fillColor: '#10B981',
              fillOpacity: 0.1,
              weight: 2
            }}
          />
        )}
      </MapContainer>
    </div>
  );
};

export default MapView;
