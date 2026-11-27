import { geojsonToWkb, parquetWriteBuffer } from 'hyparquet-writer';
import { schoolsGeoJSON } from './export.js';

// Numeric fields that can have a fraction.
const DOUBLE_FIELDS = new Set(['change_5y_pct', 'hp_relative_index', 'nearest_school_km']);

function columnType(name, values) {
  if (DOUBLE_FIELDS.has(name)) return 'DOUBLE';
  const present = values.filter((value) => value !== null);
  if (present.length && present.every((value) => typeof value === 'boolean')) return 'BOOLEAN';
  if (present.length && present.every((value) => Number.isInteger(value))) return 'INT32';
  return 'STRING';
}

function bbox(features) {
  const points = features.filter((f) => f.geometry).map((f) => f.geometry.coordinates);
  if (!points.length) return undefined;
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}

// Return the schools as a GeoParquet 1.1 file: the published fields, and
// the locations as WKB points in longitude and latitude (OGC:CRS84).
export function schoolsGeoParquet(schools) {
  const features = schoolsGeoJSON(schools).features;
  const names = [...new Set(features.flatMap((feature) => Object.keys(feature.properties)))];
  const columnData = names.map((name) => {
    const data = features.map((feature) => feature.properties[name] ?? null);
    return { name, data, type: columnType(name, data) };
  });
  columnData.push({
    name: 'geometry',
    data: features.map((feature) => (feature.geometry ? geojsonToWkb(feature.geometry) : null)),
    type: 'BYTE_ARRAY',
  });
  const geo = {
    version: '1.1.0',
    primary_column: 'geometry',
    columns: { geometry: { encoding: 'WKB', geometry_types: ['Point'], bbox: bbox(features) } },
  };
  return parquetWriteBuffer({ columnData, kvMetadata: [{ key: 'geo', value: JSON.stringify(geo) }] });
}
