// Load the viewer data that `schools web` writes to public/data.

const DATA_PATH = './data/';

export async function loadJson(name) {
  const response = await fetch(DATA_PATH + name);
  if (!response.ok) {
    throw new Error(`Cannot load ${name}: HTTP ${response.status}`);
  }
  return response.json();
}

// Primary schools on the special-school list are a separate category.
export function category(school) {
  if (school.level === 'post_primary') return 'post_primary';
  return school.special_school ? 'special' : 'primary';
}

export function toSchools(collection) {
  return collection.features.map((feature) => {
    const school = { ...feature.properties };
    school.coordinates = feature.geometry?.coordinates ?? null;
    school.category = category(school);
    return school;
  });
}

export async function loadSchools() {
  const [collection, meta] = await Promise.all([
    loadJson('schools.geojson'),
    loadJson('meta.json'),
  ]);
  const schools = toSchools(collection);
  const byRoll = new Map(schools.map((school) => [school.roll_number, school]));
  return { schools, byRoll, meta };
}
