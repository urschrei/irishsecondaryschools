import { loadJson, loadSchools } from './data.js';
import { createDetail } from './detail.js';
import { DEFAULT_FILTERS, activeFilterCount, matches } from './filters.js';
import { setUpFilters } from './filters-ui.js';
import { byName, number } from './labels.js';
import { renderLegend, setUpLegend } from './legend.js';
import { createList } from './list.js';
import {
  addSchools,
  addSelection,
  createMap,
  fitSchools,
  mapLoaded,
  onSchoolClick,
  schoolCollection,
  setSchoolStyle,
  setSelection,
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

    addSelection(map);
    const select = (roll) => store.set({ school: roll });
    onSchoolClick(map, select, (roll) => byRoll.get(roll)?.name ?? roll);
    const list = createList(select);

    let enrolment;
    const detail = createDetail({
      byRoll,
      meta,
      loadEnrolment: () => (enrolment ??= loadJson('enrolment.json')),
      onSelect: select,
      onClose: () => store.set({ school: null }),
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && store.get().school) store.set({ school: null });
    });

    function showDetail(state, previous) {
      const school = state.school ? byRoll.get(state.school) : null;
      setSelection(map, school, school ? byRoll.get(school.nearest_school) : null);
      if (school) {
        detail.show(school);
        if (school.coordinates) {
          map.flyTo({ center: school.coordinates, zoom: Math.max(map.getZoom(), 12) });
        }
        return;
      }
      detail.hide();
      // Return focus to the school in the list, or to the search box.
      const button = previous && document.querySelector(`#result-list button[data-roll="${previous}"]`);
      (button ?? document.getElementById('search')).focus({ preventScroll: !button });
    }

    let previousSchool = null;
    let visible = schools;
    function update(state, changed) {
      const selectionChanged =
        changed.has('initial') || changed.has('q') || [...changed].some((key) => key in DEFAULT_FILTERS);
      const [mode, colour, radius] = style(state);
      if (changed.has('colour') || changed.has('sizeByEnrolment')) {
        setSchoolStyle(map, colour, radius);
      }
      if (selectionChanged) {
        syncFilters(state);
        const selected = selectSchools(schools, search, state);
        visible = selected.visible;
        showSchools(map, visible.length === schools.length ? null : visible.map((s) => s.roll_number));
        list.update(visible);
        status.textContent =
          visible.length === schools.length
            ? `${number.format(schools.length)} schools`
            : `${number.format(visible.length)} of ${number.format(schools.length)}`;
        const narrowed = selected.found || activeFilterCount(state) > 0;
        if (narrowed && visible.length && !state.school) fitSchools(map, visible);
      }
      if (selectionChanged || changed.has('colour')) renderLegend(mode, visible);
      if (changed.has('school') || (changed.has('initial') && state.school)) {
        showDetail(state, previousSchool);
        previousSchool = state.school;
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
