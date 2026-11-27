import { describe, expect, it } from 'vitest';
import { MAX_COMPARE, toggleCompare } from '../src/compare.js';

describe('toggleCompare', () => {
  it('adds and removes a school', () => {
    expect(toggleCompare([], 'A')).toEqual(['A']);
    expect(toggleCompare(['A', 'B'], 'A')).toEqual(['B']);
  });

  it('does not add more than the maximum', () => {
    const full = ['A', 'B', 'C', 'D'];
    expect(full).toHaveLength(MAX_COMPARE);
    expect(toggleCompare(full, 'E')).toBe(full);
  });
});
