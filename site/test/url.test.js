import { describe, expect, it } from 'vitest';
import { DEFAULT_STATE, decodeState, encodeState } from '../src/url.js';

describe('URL state', () => {
  it('leaves defaults out of the query string', () => {
    expect(encodeState(DEFAULT_STATE)).toBe('');
    expect(decodeState('')).toEqual(DEFAULT_STATE);
  });

  it('round-trips a state', () => {
    const state = {
      ...DEFAULT_STATE,
      q: 'scoil',
      categories: ['primary', 'post_primary'],
      county: 'Galway',
      deis: true,
      min: 100,
      colour: 'deprivation',
      sizeByEnrolment: true,
      school: '60010P',
      near: [-6.26031, 53.34981],
      radius: 10,
      compare: ['60010P', '19461J'],
      deprivationLayer: true,
    };
    expect(decodeState(encodeState(state))).toEqual(state);
  });

  it('replaces values that are not valid with defaults', () => {
    const state = decodeState('?school=bad&colour=nope&min=-3&level=x&radius=7&near=1,2&compare=bad,60010P');
    expect(state.school).toBeNull();
    expect(state.colour).toBe('level');
    expect(state.min).toBeNull();
    expect(state.categories).toEqual([]);
    expect(state.radius).toBe(5);
    expect(state.compare).toEqual(['60010P']);
  });
});
