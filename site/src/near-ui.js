import { RADII } from './url.js';

// Controls for "Schools near a place". The state keeps the point as
// [longitude, latitude], the radius in kilometres, and a label for the point.
export function setUpNear(store, map) {
  const status = document.getElementById('near-status');
  const clear = document.getElementById('near-clear');
  const radius = document.getElementById('near-radius');
  for (const km of RADII) radius.add(new Option(`${km} km`, String(km)));
  radius.value = String(store.get().radius);

  // A message about the location request, shown when no point is chosen.
  let message = '';
  const round = (value) => Math.round(value * 1e5) / 1e5;
  const choose = (point, label) => {
    message = '';
    store.set({ near: point.map(round), nearLabel: label, school: null });
  };

  document.getElementById('near-me').addEventListener('click', () => {
    if (!navigator.geolocation) {
      message = 'This browser cannot give your location. Use the map centre instead.';
      status.textContent = message;
      return;
    }
    status.textContent = 'Finding your location';
    navigator.geolocation.getCurrentPosition(
      (position) => choose([position.coords.longitude, position.coords.latitude], 'your location'),
      (error) => {
        message =
          error.code === error.PERMISSION_DENIED
            ? 'The browser did not give your location. Allow location access, or use the map centre.'
            : 'Your location is not available. Use the map centre instead.';
        status.textContent = message;
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  });
  document.getElementById('near-centre').addEventListener('click', () => {
    const centre = map.getCenter();
    choose([centre.lng, centre.lat], 'the map centre');
  });
  radius.addEventListener('change', () => store.set({ radius: Number(radius.value) }));
  clear.addEventListener('click', () => store.set({ near: null, nearLabel: null }));

  return function sync(state, count) {
    radius.value = String(state.radius);
    clear.hidden = !state.near;
    if (state.near) {
      const label = state.nearLabel ?? 'the chosen point';
      status.textContent = `${count} ${count === 1 ? 'school' : 'schools'} within ${state.radius} km of ${label}, listed by distance.`;
    } else {
      status.textContent = message;
    }
  };
}
