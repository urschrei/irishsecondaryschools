import { Map as MapLibreMap, NavigationControl, ScaleControl, setWorkerUrl } from 'maplibre-gl';
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

export function addSchools(map, collection, colour) {
  map.addSource(SCHOOLS_SOURCE, {
    type: 'geojson',
    data: collection,
    promoteId: 'roll_number',
  });
  map.addLayer({
    id: SCHOOLS_LAYER,
    type: 'circle',
    source: SCHOOLS_SOURCE,
    paint: {
      'circle-color': colour,
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 2.5, 10, 5, 14, 8],
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 6, 0.5, 12, 1.25],
    },
  });
}
