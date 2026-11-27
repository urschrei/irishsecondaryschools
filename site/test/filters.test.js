import { describe, expect, it } from 'vitest';
import { DEFAULT_FILTERS, activeFilterCount, filterOptions, matches } from '../src/filters.js';

const school = {
  category: 'post_primary',
  county: 'Cork',
  ethos: 'Catholic',
  patron: 'Cork ETB',
  school_type: 'Vocational',
  irish_classification: 'No subjects taught through Irish',
  gender: 'Mixed',
  total: 400,
  deis: true,
  gaeltacht: false,
  attendance_type: 'Mixed',
};

describe('filters', () => {
  it('match every school by default', () => {
    expect(matches(school, DEFAULT_FILTERS)).toBe(true);
    expect(activeFilterCount(DEFAULT_FILTERS)).toBe(0);
  });

  it('filter by level', () => {
    expect(matches(school, { ...DEFAULT_FILTERS, categories: ['primary'] })).toBe(false);
  });

  it('match part of a patron name without regard to case', () => {
    expect(matches(school, { ...DEFAULT_FILTERS, patron: 'etb' })).toBe(true);
    expect(matches(school, { ...DEFAULT_FILTERS, patron: 'Kerry' })).toBe(false);
  });

  it('filter by Irish-language group', () => {
    expect(matches(school, { ...DEFAULT_FILTERS, irish: 'none' })).toBe(true);
    expect(matches(school, { ...DEFAULT_FILTERS, irish: 'all' })).toBe(false);
  });

  it('filter by enrolment range', () => {
    expect(matches(school, { ...DEFAULT_FILTERS, min: 400, max: 400 })).toBe(true);
    expect(matches(school, { ...DEFAULT_FILTERS, min: 401 })).toBe(false);
  });

  it('apply flags only when they are on', () => {
    expect(matches(school, { ...DEFAULT_FILTERS, deis: true, boarding: true })).toBe(true);
    expect(matches(school, { ...DEFAULT_FILTERS, gaeltacht: true })).toBe(false);
  });

  it('count the active filters', () => {
    expect(activeFilterCount({ ...DEFAULT_FILTERS, county: 'Cork', categories: ['primary'] })).toBe(2);
  });

  it('list sorted distinct values', () => {
    const options = filterOptions([school, { ...school, county: 'Clare' }, { ...school }]);
    expect(options.county).toEqual(['Clare', 'Cork']);
  });
});
