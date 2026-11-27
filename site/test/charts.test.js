import { describe, expect, it } from 'vitest';
import { niceCeiling } from '../src/charts.js';

describe('niceCeiling', () => {
  it('rounds up to a half step of the leading digit', () => {
    expect(niceCeiling(1220)).toBe(1500);
    expect(niceCeiling(87)).toBe(90);
    expect(niceCeiling(100)).toBe(100);
    expect(niceCeiling(0)).toBe(10);
  });
});

import { titleCase } from '../src/detail.js';

describe('titleCase', () => {
  it('capitalises each word of an ED name', () => {
    expect(titleCase('BALLINTEMPLE (CORK)')).toBe('Ballintemple (Cork)');
    expect(titleCase("ST. KEVIN'S")).toBe("St. Kevin's");
    expect(titleCase('DÚN LAOGHAIRE-GLENAGEARY')).toBe('Dún Laoghaire-Glenageary');
  });
});
