import { MODES_BY_KEY } from './modes.js';

export const CATEGORIES = ['primary', 'special', 'post_primary'];

export const FLAGS = [
  { key: 'deis', label: 'DEIS schools', test: (school) => school.deis === true },
  { key: 'gaeltacht', label: 'In the Gaeltacht', test: (school) => school.gaeltacht === true },
  { key: 'island', label: 'On an island', test: (school) => school.island === true },
  { key: 'fee', label: 'Fee-paying', test: (school) => school.fee_paying === true },
  {
    key: 'boarding',
    label: 'With boarding places',
    test: (school) => school.attendance_type === 'Boarding' || school.attendance_type === 'Mixed',
  },
];

export const DEFAULT_FILTERS = {
  categories: CATEGORIES,
  county: '',
  ethos: '',
  patron: '',
  type: '',
  irish: '',
  gender: '',
  min: null,
  max: null,
  ...Object.fromEntries(FLAGS.map((flag) => [flag.key, false])),
};

const irishGroup = MODES_BY_KEY.get('irish').classify;

export function matches(school, filters) {
  if (!filters.categories.includes(school.category)) return false;
  if (filters.county && school.county !== filters.county) return false;
  if (filters.ethos && school.ethos !== filters.ethos) return false;
  if (filters.patron && !school.patron?.toLowerCase().includes(filters.patron.toLowerCase())) {
    return false;
  }
  if (filters.type && school.school_type !== filters.type) return false;
  if (filters.irish && irishGroup(school) !== filters.irish) return false;
  if (filters.gender && school.gender !== filters.gender) return false;
  if (filters.min !== null && (school.total ?? 0) < filters.min) return false;
  if (filters.max !== null && (school.total ?? 0) > filters.max) return false;
  return FLAGS.every((flag) => !filters[flag.key] || flag.test(school));
}

// Return the number of filters that differ from the defaults.
export function activeFilterCount(filters) {
  return Object.keys(DEFAULT_FILTERS).filter((key) => {
    if (key === 'categories') return filters.categories.length !== CATEGORIES.length;
    return filters[key] !== DEFAULT_FILTERS[key];
  }).length;
}

function distinct(schools, field) {
  const values = new Set(schools.map((school) => school[field]).filter(Boolean));
  return [...values].sort((a, b) => a.localeCompare(b, 'en-IE'));
}

export function filterOptions(schools) {
  return {
    county: distinct(schools, 'county'),
    ethos: distinct(schools, 'ethos'),
    patron: distinct(schools, 'patron'),
    type: distinct(schools, 'school_type'),
    gender: distinct(schools, 'gender'),
  };
}
