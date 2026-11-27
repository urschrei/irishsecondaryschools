// Colour modes for the school markers. Each mode puts every school in one
// class, and each class has a label and a colour. The map, the legend and
// the tests all read these definitions.

const NEUTRAL = '#9aa7b0';

function irishGroup(value) {
  if (!value || value.startsWith('No ')) return 'none';
  return value.startsWith('All ') ? 'all' : 'some';
}

function changeClass(school) {
  if (school.change_5y_pct === undefined) return 'new';
  const pct = school.change_5y_pct;
  if (pct <= -20) return 'fall_large';
  if (pct < -5) return 'fall';
  if (pct <= 5) return 'stable';
  if (pct < 20) return 'rise';
  return 'rise_large';
}

function accessClass(school) {
  const km = school.nearest_school_km;
  if (km === undefined) return 'none';
  if (km < 1) return 'lt1';
  if (km < 3) return 'lt3';
  if (km < 5) return 'lt5';
  if (km < 10) return 'lt10';
  return 'ge10';
}

const ETHOS_CLASSES = new Set([
  'Catholic',
  'Multi Denominational',
  'Church of Ireland',
  'Inter Denominational',
]);

// Pobal HP Deprivation Index labels, from most affluent to most deprived.
export const HP_CLASSES = [
  { value: 'Extremely Affluent', label: 'Extremely affluent', colour: '#053061' },
  { value: 'Very Affluent', label: 'Very affluent', colour: '#2166ac' },
  { value: 'Affluent', label: 'Affluent', colour: '#4393c3' },
  { value: 'Marginally Above Average', label: 'Marginally above average', colour: '#b5d4e9' },
  { value: 'Marginally Below Average', label: 'Marginally below average', colour: '#f9cdb4' },
  { value: 'Disadvantaged', label: 'Disadvantaged', colour: '#e58268' },
  { value: 'Very Disadvantaged', label: 'Very disadvantaged', colour: '#c43c39' },
  { value: 'Extremely Disadvantaged', label: 'Extremely disadvantaged', colour: '#67001f' },
];

export const COLOUR_MODES = [
  {
    key: 'level',
    label: 'School level',
    classify: (school) => school.category,
    classes: [
      { value: 'primary', label: 'Primary', colour: '#0072b2' },
      { value: 'special', label: 'Special', colour: '#cc79a7' },
      { value: 'post_primary', label: 'Post-primary', colour: '#d55e00' },
    ],
  },
  {
    key: 'ethos',
    label: 'Ethos',
    classify: (school) => (ETHOS_CLASSES.has(school.ethos) ? school.ethos : 'Other'),
    classes: [
      { value: 'Catholic', label: 'Catholic', colour: '#56b4e9' },
      { value: 'Church of Ireland', label: 'Church of Ireland', colour: '#009e73' },
      { value: 'Multi Denominational', label: 'Multi-denominational', colour: '#d55e00' },
      { value: 'Inter Denominational', label: 'Inter-denominational', colour: '#e69f00' },
      { value: 'Other', label: 'Other', colour: '#000000' },
    ],
  },
  {
    key: 'deis',
    label: 'DEIS',
    classify: (school) => (school.deis ? 'yes' : 'no'),
    classes: [
      { value: 'yes', label: 'DEIS school', colour: '#d55e00' },
      { value: 'no', label: 'Not DEIS', colour: NEUTRAL },
    ],
  },
  {
    key: 'irish',
    label: 'Teaching through Irish',
    classify: (school) => irishGroup(school.irish_classification),
    classes: [
      { value: 'all', label: 'All subjects', colour: '#009e73' },
      { value: 'some', label: 'Some subjects or pupils', colour: '#e69f00' },
      { value: 'none', label: 'None', colour: NEUTRAL },
    ],
  },
  {
    key: 'deprivation',
    label: 'Area deprivation (Pobal HP Index)',
    note: 'The index describes the Electoral Division that contains the school, not its pupils.',
    classify: (school) => school.hp_category ?? 'none',
    classes: HP_CLASSES,
  },
  {
    key: 'change',
    label: 'Enrolment change over five years',
    note: 'A school that opened in the last five years has no earlier figure.',
    classify: changeClass,
    classes: [
      { value: 'fall_large', label: 'Fall of 20% or more', colour: '#b2182b' },
      { value: 'fall', label: 'Fall of 5% to 20%', colour: '#ef8a62' },
      { value: 'stable', label: 'Within 5%', colour: '#f7f7f7' },
      { value: 'rise', label: 'Rise of 5% to 20%', colour: '#67a9cf' },
      { value: 'rise_large', label: 'Rise of 20% or more', colour: '#2166ac' },
      { value: 'new', label: 'Not listed five years earlier', colour: '#000000' },
    ],
  },
  {
    key: 'access',
    label: 'Distance to the nearest school',
    note: 'Straight-line distance to the nearest school at the same level.',
    classify: accessClass,
    classes: [
      { value: 'lt1', label: 'Less than 1 km', colour: '#d9f0d3' },
      { value: 'lt3', label: '1 to 3 km', colour: '#a6dba0' },
      { value: 'lt5', label: '3 to 5 km', colour: '#5aae61' },
      { value: 'lt10', label: '5 to 10 km', colour: '#1b7837' },
      { value: 'ge10', label: '10 km or more', colour: '#00441b' },
    ],
  },
];

export const MODES_BY_KEY = new Map(COLOUR_MODES.map((mode) => [mode.key, mode]));

export function classProperty(mode) {
  return `c_${mode.key}`;
}

// Return the class value of each mode for one school, for the map source.
export function classValues(school) {
  return Object.fromEntries(
    COLOUR_MODES.map((mode) => [classProperty(mode), mode.classify(school)]),
  );
}

export function colourExpression(mode) {
  const pairs = mode.classes.flatMap((c) => [c.value, c.colour]);
  return ['match', ['get', classProperty(mode)], ...pairs, NEUTRAL];
}

// Return the number of schools in each class of a mode.
export function classCounts(mode, schools) {
  const counts = new Map(mode.classes.map((c) => [c.value, 0]));
  for (const school of schools) {
    const value = mode.classify(school);
    if (counts.has(value)) counts.set(value, counts.get(value) + 1);
  }
  return counts;
}

// Marker radius in pixels. With sizeByEnrolment, the area of a marker is
// proportional to the enrolment of the school.
export function radiusExpression(sizeByEnrolment) {
  if (!sizeByEnrolment) {
    return ['interpolate', ['linear'], ['zoom'], 6, 2.5, 10, 5, 14, 8];
  }
  const scaled = (factor, minimum) => ['max', minimum, ['*', factor, ['sqrt', ['get', 'total']]]];
  return ['interpolate', ['linear'], ['zoom'], 6, scaled(0.11, 1.5), 10, scaled(0.25, 2.5), 14, scaled(0.45, 3)];
}
