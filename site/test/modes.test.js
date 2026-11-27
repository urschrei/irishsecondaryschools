import { describe, expect, it } from 'vitest';
import { COLOUR_MODES, MODES_BY_KEY, classCounts, classValues, colourExpression } from '../src/modes.js';

const school = (fields) => ({ category: 'primary', ...fields });

describe('colour modes', () => {
  it('give every class a distinct value', () => {
    for (const mode of COLOUR_MODES) {
      const values = mode.classes.map((c) => c.value);
      expect(new Set(values).size).toBe(values.length);
    }
  });

  it('classify Irish-language teaching at both levels', () => {
    const irish = MODES_BY_KEY.get('irish');
    expect(irish.classify(school({ irish_classification: 'All subjects through Irish' }))).toBe('all');
    expect(irish.classify(school({ irish_classification: 'All pupils taught all subjects through Irish' }))).toBe('all');
    expect(irish.classify(school({ irish_classification: 'Some pupils taught some subjects through Irish' }))).toBe('some');
    expect(irish.classify(school({ irish_classification: 'No subjects taught through Irish' }))).toBe('none');
  });

  it('put a school without an earlier enrolment in its own change class', () => {
    const change = MODES_BY_KEY.get('change');
    expect(change.classify(school({}))).toBe('new');
    expect(change.classify(school({ change_5y_pct: -20 }))).toBe('fall_large');
    expect(change.classify(school({ change_5y_pct: 5 }))).toBe('stable');
    expect(change.classify(school({ change_5y_pct: 4300 }))).toBe('rise_large');
  });

  it('group the less common ethos values', () => {
    const ethos = MODES_BY_KEY.get('ethos');
    expect(ethos.classify(school({ ethos: 'Quaker' }))).toBe('Other');
    expect(ethos.classify(school({ ethos: 'Catholic' }))).toBe('Catholic');
  });

  it('give each school one value for each mode', () => {
    const values = classValues(school({ deis: true, nearest_school_km: 12.5 }));
    expect(values.c_deis).toBe('yes');
    expect(values.c_access).toBe('ge10');
    expect(Object.keys(values)).toHaveLength(COLOUR_MODES.length);
  });

  it('count schools by class', () => {
    const deis = MODES_BY_KEY.get('deis');
    const counts = classCounts(deis, [school({ deis: true }), school({ deis: false }), school({})]);
    expect(Object.fromEntries(counts)).toEqual({ yes: 1, no: 2 });
  });

  it('build a match expression with a fallback colour', () => {
    const expression = colourExpression(MODES_BY_KEY.get('deis'));
    expect(expression.slice(0, 2)).toEqual(['match', ['get', 'c_deis']]);
    expect(expression).toHaveLength(2 + 4 + 1);
  });
});
