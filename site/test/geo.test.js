import { describe, expect, it } from 'vitest';
import { circle, distanceKm } from '../src/geo.js';

const DUBLIN = [-6.2603, 53.3498];
const GALWAY = [-9.0568, 53.2707];

describe('geo', () => {
  it('measures the distance from Dublin to Galway', () => {
    expect(distanceKm(DUBLIN, GALWAY)).toBeCloseTo(186.4, 0);
    expect(distanceKm(DUBLIN, DUBLIN)).toBe(0);
  });

  it('makes a closed ring at the given radius', () => {
    const ring = circle(DUBLIN, 5, 36).coordinates[0];
    expect(ring).toHaveLength(37);
    expect(ring[0][0]).toBeCloseTo(ring.at(-1)[0], 10);
    for (const point of ring) expect(distanceKm(DUBLIN, point)).toBeCloseTo(5, 6);
  });
});
