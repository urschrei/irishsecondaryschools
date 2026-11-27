import { describe, expect, it } from 'vitest';
import { schoolsGeoJSON } from '../src/export.js';

describe('schoolsGeoJSON', () => {
  it('writes the published fields and the location', () => {
    const collection = schoolsGeoJSON([
      { roll_number: '60010P', name: 'A', category: 'post_primary', coordinates: [-6.1, 53.6] },
      { roll_number: '20595W', name: 'B', category: 'special', coordinates: null },
    ]);
    expect(collection.features[0]).toEqual({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [-6.1, 53.6] },
      properties: { roll_number: '60010P', name: 'A' },
    });
    expect(collection.features[1].geometry).toBeNull();
  });
});

import { parquetMetadata, parquetReadObjects } from 'hyparquet';
import { schoolsGeoParquet } from '../src/parquet.js';

describe('schoolsGeoParquet', () => {
  it('writes the fields, WKB points and GeoParquet metadata', async () => {
    const buffer = schoolsGeoParquet([
      { roll_number: '60010P', total: 1220, deis: false, change_5y_pct: -5, phone_display: 'x', coordinates: [-6.1, 53.6] },
      { roll_number: '20595W', total: 30, deis: true, change_5y_pct: 2.5, coordinates: null },
    ]);
    const metadata = parquetMetadata(buffer);
    const geo = JSON.parse(metadata.key_value_metadata.find((kv) => kv.key === 'geo').value);
    expect(geo.primary_column).toBe('geometry');
    expect(geo.columns.geometry.bbox).toEqual([-6.1, 53.6, -6.1, 53.6]);
    const rows = await parquetReadObjects({ file: buffer });
    expect(rows[0]).toMatchObject({ roll_number: '60010P', total: 1220, deis: false, change_5y_pct: -5 });
    expect(rows[0]).not.toHaveProperty('phone_display');
    expect(rows[1].geometry).toBeNull();
  });
});
