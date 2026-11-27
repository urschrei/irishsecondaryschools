import {
  LngLatBounds,
  Map as MapLibreMap,
  NavigationControl,
  Popup,
  ScaleControl,
  setWorkerUrl,
} from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import { circle } from './geo.js';

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

const SELECTION_SOURCE = 'selection';
const SELECTED_ICON = 'selected-school';

// A yellow diamond with a black edge, like the Irish school warning sign.
function diamond(size = 44, edge = 3) {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext('2d');
  const half = size / 2;
  const inset = edge + 1;
  context.beginPath();
  context.moveTo(half, inset);
  context.lineTo(size - inset, half);
  context.lineTo(half, size - inset);
  context.lineTo(inset, half);
  context.closePath();
  context.fillStyle = '#f2c200';
  context.fill();
  context.lineWidth = edge;
  context.strokeStyle = '#17212b';
  context.stroke();
  return context.getImageData(0, 0, size, size);
}

export function addSelection(map) {
  map.addImage(SELECTED_ICON, diamond(), { pixelRatio: 2 });
  map.addSource(SELECTION_SOURCE, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  map.addLayer(
    {
      id: 'selection-ring',
      type: 'line',
      source: SELECTION_SOURCE,
      filter: ['==', ['get', 'kind'], 'ring'],
      paint: { 'line-color': '#17212b', 'line-width': 1.5, 'line-dasharray': [3, 2] },
    },
    SCHOOLS_LAYER,
  );
  map.addLayer(
    {
      id: 'selection-nearest',
      type: 'line',
      source: SELECTION_SOURCE,
      filter: ['==', ['get', 'kind'], 'nearest'],
      paint: { 'line-color': '#17212b', 'line-width': 2 },
    },
    SCHOOLS_LAYER,
  );
  map.addLayer({
    id: 'selection-school',
    type: 'symbol',
    source: SELECTION_SOURCE,
    filter: ['==', ['get', 'kind'], 'school'],
    layout: {
      'icon-image': SELECTED_ICON,
      'icon-allow-overlap': true,
      'icon-ignore-placement': true,
    },
  });
}

// Show a school with a 5 km ring and a line to its nearest school.
export function setSelection(map, school, nearest, ringKm = 5) {
  const features = [];
  if (school?.coordinates) {
    features.push({ type: 'Feature', properties: { kind: 'ring' }, geometry: circle(school.coordinates, ringKm) });
    if (nearest?.coordinates) {
      features.push({
        type: 'Feature',
        properties: { kind: 'nearest' },
        geometry: { type: 'LineString', coordinates: [school.coordinates, nearest.coordinates] },
      });
    }
    features.push({ type: 'Feature', properties: { kind: 'school' }, geometry: { type: 'Point', coordinates: school.coordinates } });
  }
  map.getSource(SELECTION_SOURCE).setData({ type: 'FeatureCollection', features });
}

// Call onSelect with the roll number of a clicked school, and show the
// name of the school under the pointer.
export function onSchoolClick(map, onSelect, nameOf) {
  const popup = new Popup({ closeButton: false, closeOnClick: false, offset: 8, className: 'school-name' });
  map.on('click', SCHOOLS_LAYER, (event) => {
    const feature = event.features?.[0];
    if (feature) onSelect(feature.properties.roll_number);
  });
  map.on('mousemove', SCHOOLS_LAYER, (event) => {
    const feature = event.features?.[0];
    if (!feature) return;
    map.getCanvas().style.cursor = 'pointer';
    popup.setLngLat(feature.geometry.coordinates).setText(nameOf(feature.properties.roll_number)).addTo(map);
  });
  map.on('mouseleave', SCHOOLS_LAYER, () => {
    map.getCanvas().style.cursor = '';
    popup.remove();
  });
  map.on('movestart', () => popup.remove());
}
