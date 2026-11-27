import { distanceKm } from './geo.js';

// Return the schools within radiusKm of a point, nearest first, and a map
// of roll number to distance. Schools without a location are left out.
export function schoolsNear(schools, point, radiusKm) {
  const distances = new Map();
  for (const school of schools) {
    if (!school.coordinates) continue;
    const km = distanceKm(point, school.coordinates);
    if (km <= radiusKm) distances.set(school.roll_number, km);
  }
  const near = schools
    .filter((school) => distances.has(school.roll_number))
    .sort((a, b) => distances.get(a.roll_number) - distances.get(b.roll_number));
  return { near, distances };
}
