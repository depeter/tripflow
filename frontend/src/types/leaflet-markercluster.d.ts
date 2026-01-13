import * as L from 'leaflet';

declare module 'leaflet' {
  interface MarkerClusterGroupOptions extends L.LayerOptions {
    chunkedLoading?: boolean;
    maxClusterRadius?: number | ((zoom: number) => number);
    spiderfyOnMaxZoom?: boolean;
    showCoverageOnHover?: boolean;
    zoomToBoundsOnClick?: boolean;
    singleMarkerMode?: boolean;
    disableClusteringAtZoom?: number;
    removeOutsideVisibleBounds?: boolean;
    animate?: boolean;
    animateAddingMarkers?: boolean;
    spiderfyDistanceMultiplier?: number;
    spiderLegPolylineOptions?: L.PolylineOptions;
    polygonOptions?: L.PolylineOptions;
    iconCreateFunction?: (cluster: MarkerCluster) => L.Icon | L.DivIcon;
  }

  interface MarkerCluster extends L.Marker {
    getChildCount(): number;
    getAllChildMarkers(): L.Marker[];
    spiderfy(): void;
    unspiderfy(): void;
  }

  interface MarkerClusterGroup extends L.FeatureGroup {
    addLayer(layer: L.Layer): this;
    removeLayer(layer: L.Layer): this;
    clearLayers(): this;
    hasLayer(layer: L.Layer): boolean;
    getLayers(): L.Layer[];
    getVisibleParent(marker: L.Marker): L.Marker | MarkerCluster;
    refreshClusters(layer?: L.Layer): this;
    zoomToShowLayer(layer: L.Layer, callback?: () => void): void;
  }

  function markerClusterGroup(options?: MarkerClusterGroupOptions): MarkerClusterGroup;
}

declare module 'leaflet.markercluster' {
  // This module augments the leaflet namespace
}
