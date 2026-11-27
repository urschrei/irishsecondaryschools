import MiniSearch from 'minisearch';

// An Eircode is a routing key, such as D07, and a four-character unique
// identifier. The letters B, G, I, J, L, M, O, Q, S, U and Z are not used.
const ROUTING_KEY = /^(?:[AC-FHKNPRTV-Y]\d{2}|D6W)$/;
const EIRCODE = /^(?:[AC-FHKNPRTV-Y]\d{2}|D6W)[0-9AC-FHKNPRTV-Y]{4}$/;

export function compactEircode(text) {
  return text.replace(/\s+/g, '').toUpperCase();
}

// Lower case, without accents, so that "o" matches "ó".
export function foldTerm(term) {
  return term.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
}

export function address(school) {
  return [school.address_1, school.address_2, school.address_3, school.address_4]
    .filter(Boolean)
    .join(', ');
}

// Return a function that finds schools for a query. The result has the
// matching roll numbers in order of relevance and the kind of match:
// "eircode" for a full Eircode, "area" for a routing key, or "text".
export function createSearch(schools) {
  const index = new MiniSearch({
    idField: 'roll_number',
    fields: ['name', 'address', 'county', 'roll_number', 'patron'],
    processTerm: foldTerm,
    searchOptions: {
      prefix: true,
      fuzzy: (term) => (term.length > 4 ? 0.2 : 0),
      combineWith: 'AND',
      boost: { name: 3, roll_number: 3 },
    },
  });
  index.addAll(
    schools.map((school) => ({
      roll_number: school.roll_number,
      name: school.name,
      address: address(school),
      county: school.county ?? '',
      patron: school.patron ?? '',
    })),
  );

  const byEircodePrefix = (prefix) =>
    schools.filter((school) => school.eircode?.startsWith(prefix)).map((s) => s.roll_number);

  return (query) => {
    const text = query.trim();
    if (!text) return null;
    const code = compactEircode(text);
    if (EIRCODE.test(code)) {
      const exact = byEircodePrefix(code);
      if (exact.length) return { kind: 'eircode', rolls: exact };
      return { kind: 'area', rolls: byEircodePrefix(code.slice(0, 3)) };
    }
    if (ROUTING_KEY.test(code)) {
      return { kind: 'area', rolls: byEircodePrefix(code) };
    }
    return { kind: 'text', rolls: index.search(text).map((result) => result.id) };
  };
}
