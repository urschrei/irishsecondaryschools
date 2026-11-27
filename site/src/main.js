import { loadSchools } from './data.js';
import { addSchools, createMap, mapLoaded, schoolCollection } from './map.js';

const LEVEL_COLOURS = [
  'match',
  ['get', 'category'],
  'primary',
  '#0072b2',
  'special',
  '#cc79a7',
  'post_primary',
  '#d55e00',
  '#777777',
];

async function start() {
  const status = document.getElementById('status');
  const map = createMap(document.getElementById('map'));
  try {
    const [{ schools, meta }] = await Promise.all([loadSchools(), mapLoaded(map)]);
    for (const node of document.querySelectorAll('[data-school-year]')) {
      node.textContent = meta.school_year;
    }
    const collection = schoolCollection(schools, (school) => ({ category: school.category }));
    addSchools(map, collection, LEVEL_COLOURS);
    status.textContent = `${schools.length.toLocaleString('en-IE')} schools`;
  } catch (error) {
    status.textContent = `The school data did not load. ${error.message}`;
    throw error;
  }
}

start();
