// Fields that the viewer adds to each school for display. They are not
// in the exported files.
const VIEWER_FIELDS = new Set(['coordinates', 'category', 'phone_display']);

// Return the schools as a GeoJSON feature collection with the fields of
// the published data.
export function schoolsGeoJSON(schools) {
  return {
    type: 'FeatureCollection',
    features: schools.map((school) => ({
      type: 'Feature',
      geometry: school.coordinates ? { type: 'Point', coordinates: school.coordinates } : null,
      properties: Object.fromEntries(Object.entries(school).filter(([key]) => !VIEWER_FIELDS.has(key))),
    })),
  };
}

export function downloadFile(contents, filename, type) {
  const blob = new Blob([contents], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
