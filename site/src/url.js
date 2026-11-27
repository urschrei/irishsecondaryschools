import { CATEGORIES, DEFAULT_FILTERS, FLAGS } from './filters.js';
import { MODES_BY_KEY } from './modes.js';

export const DEFAULT_VIEW = {
  q: '',
  colour: 'level',
  sizeByEnrolment: false,
  school: null,
  near: null,
  // Text for the chosen point, such as "your location". Not kept in the URL.
  nearLabel: null,
  radius: 5,
  compare: [],
  deprivationLayer: false,
};

export const DEFAULT_STATE = { ...DEFAULT_VIEW, ...DEFAULT_FILTERS };

const TEXT_KEYS = ['q', 'county', 'ethos', 'patron', 'type', 'irish', 'gender', 'school'];
const ROLL = /^\d{5}[A-Z]$/;
const RADII = [1, 2, 5, 10, 20];

// Return the query string for a state. Default values are left out.
export function encodeState(state) {
  const params = new URLSearchParams();
  for (const key of TEXT_KEYS) {
    if (state[key]) params.set(key, state[key]);
  }
  if (state.categories.length !== CATEGORIES.length) {
    params.set('level', state.categories.join(','));
  }
  for (const key of ['min', 'max']) {
    if (state[key] !== null) params.set(key, String(state[key]));
  }
  for (const flag of FLAGS) {
    if (state[flag.key]) params.set(flag.key, '1');
  }
  if (state.colour !== DEFAULT_VIEW.colour) params.set('colour', state.colour);
  if (state.sizeByEnrolment) params.set('size', '1');
  if (state.near) {
    params.set('near', state.near.map((v) => v.toFixed(5)).join(','));
    params.set('radius', String(state.radius));
  }
  if (state.compare.length) params.set('compare', state.compare.join(','));
  if (state.deprivationLayer) params.set('areas', '1');
  const query = params.toString();
  return query ? `?${query}` : '';
}

function count(value) {
  if (value === null || value === '') return null;
  const n = Number(value);
  return Number.isInteger(n) && n >= 0 ? n : null;
}

// Return the state for a query string. Values that are not valid are
// replaced by their defaults.
export function decodeState(search) {
  const params = new URLSearchParams(search);
  const state = { ...DEFAULT_STATE };
  for (const key of TEXT_KEYS) {
    if (params.has(key)) state[key] = params.get(key);
  }
  if (state.school && !ROLL.test(state.school)) state.school = null;
  if (params.has('level')) {
    const levels = params.get('level').split(',').filter((c) => CATEGORIES.includes(c));
    state.categories = CATEGORIES.filter((c) => levels.includes(c));
  }
  state.min = count(params.get('min'));
  state.max = count(params.get('max'));
  for (const flag of FLAGS) state[flag.key] = params.get(flag.key) === '1';
  if (MODES_BY_KEY.has(params.get('colour'))) state.colour = params.get('colour');
  state.sizeByEnrolment = params.get('size') === '1';
  const near = (params.get('near') ?? '').split(',').map(Number);
  if (near.length === 2 && near.every(Number.isFinite)) {
    state.near = near;
    const radius = Number(params.get('radius'));
    state.radius = RADII.includes(radius) ? radius : DEFAULT_VIEW.radius;
  }
  if (params.has('compare')) {
    state.compare = params.get('compare').split(',').filter((roll) => ROLL.test(roll)).slice(0, 4);
  }
  state.deprivationLayer = params.get('areas') === '1';
  return state;
}

export { RADII };
