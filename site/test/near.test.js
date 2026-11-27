import { describe, expect, it } from 'vitest';
import { schoolsNear } from '../src/near.js';

const schools = [
  { roll_number: 'A', coordinates: [-6.2603, 53.3698] },
  { roll_number: 'B', coordinates: [-6.2603, 53.3518] },
  { roll_number: 'C', coordinates: [-9.0568, 53.2707] },
  { roll_number: 'D', coordinates: null },
];

describe('schoolsNear', () => {
  it('returns the schools within the radius, nearest first', () => {
    const { near, distances } = schoolsNear(schools, [-6.2603, 53.3498], 5);
    expect(near.map((s) => s.roll_number)).toEqual(['B', 'A']);
    expect(distances.get('A')).toBeCloseTo(2.22, 2);
    expect(distances.has('D')).toBe(false);
  });
});
