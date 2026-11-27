import { loadJson, loadSchools } from './data.js';
import { createDetail } from './detail.js';
import { DEFAULT_FILTERS, activeFilterCount, matches } from './filters.js';
import { setUpFilters } from './filters-ui.js';
import { byName, decimal, number } from './labels.js';
import { renderLegend, setUpLegend } from './legend.js';
import { createList } from './list.js';
import {
  addNear,
  addSchools,
  addSelection,
  createMap,
  fitSchools,
  mapLoaded,
  onSchoolClick,
  schoolCollection,
  setNear,
  setSchoolStyle,
  setSelection,
  showSchools,
} from './map.js';
import { MODES_BY_KEY, classValues, colourExpression, radiusExpression } from './modes.js';
import { schoolsNear } from './near.js';
import { setUpNear } from './near-ui.js';
import { createSearch } from './search.js';
import { createStore } from './state.js';
import { decodeState, encodeState } from './url.js';

const SEARCH_DELAY_MS = 250;

function style(state) {
  const mode = MODES_BY_KEY.get(state.colour);
  return [mode, colourExpression(mode), radiusExpression(state.sizeByEnrolment)];
}

// Return the schools that match the state, in display order. Near a
// point, the order is by distance, and distances has each distance in km.
function selectSchools(schools, search, state) {
  let visible = schools.filter((school) => matches(school, state));
  const found = search(state.q);
  if (found) {
    const rank = new Map(found.rolls.map((roll, i) => [roll, i]));
    visible = visible.filter((school) => rank.has(school.roll_number));
    if (found.kind === 'text') visible.sort((a, b) => rank.get(a.roll_number) - rank.get(b.roll_number));
    else visible.sort(byName);
  } else {
    visible.sort(byName);
  }
  if (!state.near) return { found, visible, distances: null };
  const { near, distances } = schoolsNear(visible, state.near, state.radius);
  return { found, visible: near, distances };
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

    addNear(map);
    addSelection(map);
    const syncNear = setUpNear(store, map);
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
      extras: {
        nearby(school) {
          if (!school.coordinates) return null;
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'button mt-3';
          button.textContent = 'Show all schools within 5 km';
          button.addEventListener('click', () =>
            store.set({ near: school.coordinates, nearLabel: school.name, radius: 5, school: null }),
          );
          return button;
        },
      },
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
      const nearChanged = changed.has('near') || changed.has('radius');
      const selectionChanged =
        changed.has('initial') ||
        changed.has('q') ||
        nearChanged ||
        [...changed].some((key) => key in DEFAULT_FILTERS);
      const [mode, colour, radius] = style(state);
      if (changed.has('colour') || changed.has('sizeByEnrolment')) {
        setSchoolStyle(map, colour, radius);
      }
      if (selectionChanged) {
        syncFilters(state);
        const selected = selectSchools(schools, search, state);
        visible = selected.visible;
        showSchools(map, visible.length === schools.length ? null : visible.map((s) => s.roll_number));
        const { distances } = selected;
        list.update(visible, distances ? (school) => `${decimal.format(distances.get(school.roll_number))} km` : undefined);
        syncNear(state, visible.length);
        status.textContent =
          visible.length === schools.length
            ? `${number.format(schools.length)} schools`
            : `${number.format(visible.length)} of ${number.format(schools.length)}`;
        if (nearChanged || (changed.has('initial') && state.near)) {
          setNear(map, state.near, state.radius);
        } else if (!state.near && !state.school && visible.length) {
          if (selected.found || activeFilterCount(state) > 0) fitSchools(map, visible);
        }
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
