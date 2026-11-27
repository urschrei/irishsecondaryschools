import {
  LngLatBounds,
  Map as MapLibreMap,
  NavigationControl,
  ScaleControl,
  setWorkerUrl,
} from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';

// Vite moves the bundled modules, so give MapLibre the worker location.
setWorkerUrl(workerUrl);

// OpenFreeMap needs no API key.
const BASEMAP = 'https://tiles.openfreemap.org/styles/positron';
const IRELAND = [
  [-10.7, 51.35],
  [-5.9, 55.45],
];

export const SCHOOLS_SOURCE = 'schools';
export const SCHOOLS_LAYER = 'schools';

export function createMap(container) {
  const map = new MapLibreMap({
    container,
    style: BASEMAP,
    bounds: IRELAND,
    fitBoundsOptions: { padding: 24 },
    attributionControl: { compact: true },
  });
  map.addControl(new NavigationControl({ showCompass: false }), 'top-right');
  map.addControl(new ScaleControl({ unit: 'metric' }), 'bottom-right');
  return map;
}

export function mapLoaded(map) {
  return map.loaded() ? Promise.resolve(map) : new Promise((done) => map.once('load', () => done(map)));
}

// Return a GeoJSON feature collection of the schools that have a location.
export function schoolCollection(schools, properties) {
  return {
    type: 'FeatureCollection',
    features: schools
      .filter((school) => school.coordinates)
      .map((school) => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: school.coordinates },
        properties: { roll_number: school.roll_number, ...properties(school) },
      })),
  };
}

export function addSchools(map, collection, colour, radius) {
  map.addSource(SCHOOLS_SOURCE, {
    type: 'geojson',
    data: collection,
    promoteId: 'roll_number',
  });
  map.addLayer({
    id: SCHOOLS_LAYER,
    type: 'circle',
    source: SCHOOLS_SOURCE,
    // Draw small schools above large ones.
    layout: { 'circle-sort-key': ['-', ['get', 'total']] },
    paint: {
      'circle-color': colour,
      'circle-radius': radius,
      // A dark outline keeps pale classes visible on the light basemap.
      'circle-stroke-color': 'rgba(23, 33, 43, 0.6)',
      'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 6, 0.4, 12, 1],
    },
  });
}

export function setSchoolStyle(map, colour, radius) {
  map.setPaintProperty(SCHOOLS_LAYER, 'circle-color', colour);
  map.setPaintProperty(SCHOOLS_LAYER, 'circle-radius', radius);
}

// Show only the given schools, or all schools if rolls is null.
export function showSchools(map, rolls) {
  map.setFilter(SCHOOLS_LAYER, rolls ? ['in', ['get', 'roll_number'], ['literal', rolls]] : null);
}

export function fitSchools(map, schools) {
  const located = schools.filter((school) => school.coordinates);
  if (!located.length) return;
  const bounds = new LngLatBounds(located[0].coordinates, located[0].coordinates);
  for (const school of located) bounds.extend(school.coordinates);
  map.fitBounds(bounds, { padding: 48, maxZoom: 14 });
}
