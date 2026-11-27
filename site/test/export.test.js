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
