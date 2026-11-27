// Distances and shapes on the WGS 84 ellipsoid, approximated by a sphere.

const EARTH_RADIUS_KM = 6371.0088;
const toRadians = (degrees) => (degrees * Math.PI) / 180;

// Return the great-circle distance in kilometres between two [lon, lat] points.
export function distanceKm([lon1, lat1], [lon2, lat2]) {
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(a));
}

// Return a GeoJSON polygon that approximates a circle of radius km.
export function circle([lon, lat], km, steps = 72) {
  const angular = km / EARTH_RADIUS_KM;
  const lat1 = toRadians(lat);
  const lon1 = toRadians(lon);
  const ring = [];
  for (let i = 0; i <= steps; i += 1) {
    const bearing = (2 * Math.PI * i) / steps;
    const lat2 = Math.asin(
      Math.sin(lat1) * Math.cos(angular) + Math.cos(lat1) * Math.sin(angular) * Math.cos(bearing),
    );
    const lon2 =
      lon1 +
      Math.atan2(
        Math.sin(bearing) * Math.sin(angular) * Math.cos(lat1),
        Math.cos(angular) - Math.sin(lat1) * Math.sin(lat2),
      );
    ring.push([(lon2 * 180) / Math.PI, (lat2 * 180) / Math.PI]);
  }
  return { type: 'Polygon', coordinates: [ring] };
}
