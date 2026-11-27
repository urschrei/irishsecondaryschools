import { loadSchools } from './data.js';
import { DEFAULT_FILTERS, activeFilterCount, matches } from './filters.js';
import { setUpFilters } from './filters-ui.js';
import { byName, number } from './labels.js';
import { renderLegend, setUpLegend } from './legend.js';
import { createList } from './list.js';
import {
  addSchools,
  createMap,
  fitSchools,
  mapLoaded,
  schoolCollection,
  setSchoolStyle,
  showSchools,
} from './map.js';
import { MODES_BY_KEY, classValues, colourExpression, radiusExpression } from './modes.js';
import { createSearch } from './search.js';
import { createStore } from './state.js';
import { decodeState, encodeState } from './url.js';

const SEARCH_DELAY_MS = 250;

function style(state) {
  const mode = MODES_BY_KEY.get(state.colour);
  return [mode, colourExpression(mode), radiusExpression(state.sizeByEnrolment)];
}

// Return the schools that match the state, in display order.
function selectSchools(schools, search, state) {
  const filtered = schools.filter((school) => matches(school, state));
  const found = search(state.q);
  if (!found) return { found, visible: filtered.sort(byName) };
  const rank = new Map(found.rolls.map((roll, i) => [roll, i]));
  const visible = filtered.filter((school) => rank.has(school.roll_number));
  if (found.kind === 'text') {
    visible.sort((a, b) => rank.get(a.roll_number) - rank.get(b.roll_number));
  } else {
    visible.sort(byName);
  }
  return { found, visible };
}

function setUpSearch(store) {
  const input = document.getElementById('search');
  input.value = store.get().q;
  store.subscribe((state, changed) => {
    if (changed.has('q') && input.value !== state.q) input.value = state.q;
  });
  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => store.set({ q: input.value }), SEARCH_DELAY_MS);
  });
  document.getElementById('search-form').addEventListener('submit', (event) => {
    event.preventDefault();
    clearTimeout(timer);
    store.set({ q: input.value });
  });
}

async function start() {
  const status = document.getElementById('status');
  const map = createMap(document.getElementById('map'));
  const store = createStore(decodeState(window.location.search));
  try {
    const [{ schools, byRoll, meta }] = await Promise.all([loadSchools(), mapLoaded(map)]);
    for (const node of document.querySelectorAll('[data-school-year]')) {
      node.textContent = meta.school_year;
    }
    const search = createSearch(schools);
    const collection = schoolCollection(schools, (school) => ({
      total: school.total,
      ...classValues(school),
    }));
    const [, colour, radius] = style(store.get());
    addSchools(map, collection, colour, radius);
    setUpLegend(store);
    setUpSearch(store);
    const syncFilters = setUpFilters(store, schools);
    document.getElementById('filters').open = activeFilterCount(store.get()) > 0;

    const list = createList((roll) => store.set({ school: roll }));

    function update(state, changed) {
      syncFilters(state);
      const { found, visible } = selectSchools(schools, search, state);
      const [mode, colour, radius] = style(state);
      if (changed.has('colour') || changed.has('sizeByEnrolment')) {
        setSchoolStyle(map, colour, radius);
      }
      renderLegend(mode, visible);
      showSchools(map, visible.length === schools.length ? null : visible.map((s) => s.roll_number));
      list.update(visible);
      status.textContent =
        visible.length === schools.length
          ? `${number.format(schools.length)} schools`
          : `${number.format(visible.length)} of ${number.format(schools.length)}`;
      const narrowed = found || activeFilterCount(state) > 0;
      const refit = changed.has('initial') || changed.has('q') || [...changed].some((key) => key in DEFAULT_FILTERS);
      if (refit && narrowed && visible.length && !state.school) fitSchools(map, visible);
      if (changed.has('school') && state.school) {
        const school = byRoll.get(state.school);
        if (school?.coordinates) map.flyTo({ center: school.coordinates, zoom: Math.max(map.getZoom(), 13) });
      }
    }

    update(store.get(), new Set(['initial']));
    store.subscribe(update);

    // Keep the URL in step with the state. A new school gets a history
    // entry, so that the Back button returns to the previous view.
    let restoring = false;
    store.subscribe((state, changed) => {
      if (restoring) return;
      const url = `${window.location.pathname}${encodeState(state)}`;
      if (changed.has('school')) window.history.pushState(null, '', url);
      else window.history.replaceState(null, '', url);
    });
    window.addEventListener('popstate', () => {
      restoring = true;
      store.set(decodeState(window.location.search));
      restoring = false;
    });
  } catch (error) {
    status.textContent = `The school data did not load. ${error.message}`;
    throw error;
  }
}

start();
