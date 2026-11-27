import { loadSchools } from './data.js';
import { renderLegend, setUpLegend } from './legend.js';
import { addSchools, createMap, mapLoaded, schoolCollection, setSchoolStyle } from './map.js';
import { MODES_BY_KEY, classValues, colourExpression, radiusExpression } from './modes.js';
import { createStore } from './state.js';

const number = new Intl.NumberFormat('en-IE');

function style(state) {
  const mode = MODES_BY_KEY.get(state.colour);
  return [mode, colourExpression(mode), radiusExpression(state.sizeByEnrolment)];
}

async function start() {
  const status = document.getElementById('status');
  const map = createMap(document.getElementById('map'));
  const store = createStore({ colour: 'level', sizeByEnrolment: false });
  try {
    const [{ schools, meta }] = await Promise.all([loadSchools(), mapLoaded(map)]);
    for (const node of document.querySelectorAll('[data-school-year]')) {
      node.textContent = meta.school_year;
    }
    const collection = schoolCollection(schools, (school) => ({
      total: school.total,
      ...classValues(school),
    }));
    const [mode, colour, radius] = style(store.get());
    addSchools(map, collection, colour, radius);
    setUpLegend(store);
    renderLegend(mode, schools);
    store.subscribe((state) => {
      const [mode, colour, radius] = style(state);
      setSchoolStyle(map, colour, radius);
      renderLegend(mode, schools);
    });
    status.textContent = `${number.format(schools.length)} schools`;
  } catch (error) {
    status.textContent = `The school data did not load. ${error.message}`;
    throw error;
  }
}

start();
