import { describe, expect, it } from 'vitest';
import { createSearch, foldTerm } from '../src/search.js';

const schools = [
  { roll_number: '60010P', name: 'Loreto Secondary School', address_1: 'Brick Lane', address_2: 'Balbriggan', eircode: 'K32R248' },
  { roll_number: '19461J', name: 'Gaelscoil Ó Doghair', address_1: 'Ballina', eircode: 'F26X1A2' },
  { roll_number: '20001A', name: 'Scoil Mhuire', address_1: 'Balbriggan', eircode: 'K32AB12' },
];
const search = createSearch(schools);

describe('search', () => {
  it('ignores an empty query', () => {
    expect(search('  ')).toBeNull();
  });

  it('finds a school by name without accents', () => {
    expect(foldTerm('Ó')).toBe('o');
    expect(search('gaelscoil o doghair').rolls).toEqual(['19461J']);
  });

  it('finds schools by address and prefix', () => {
    expect(search('balbrig').rolls.sort()).toEqual(['20001A', '60010P']);
  });

  it('finds a school by roll number', () => {
    expect(search('60010p').rolls).toEqual(['60010P']);
  });

  it('finds a school by its full Eircode', () => {
    expect(search('k32 r248')).toEqual({ kind: 'eircode', rolls: ['60010P'] });
  });

  it('finds the schools in a routing key area', () => {
    expect(search('K32')).toEqual({ kind: 'area', rolls: ['60010P', '20001A'] });
  });

  it('falls back to the routing key for an Eircode that is not a school', () => {
    expect(search('K32 XY99').kind).toBe('area');
  });
});
