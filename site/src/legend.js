import { COLOUR_MODES, HP_CLASSES, classCounts } from './modes.js';

const number = new Intl.NumberFormat('en-IE');

export function setUpLegend(store) {
  const select = document.getElementById('colour-mode');
  for (const mode of COLOUR_MODES) {
    select.add(new Option(mode.label, mode.key));
  }
  select.value = store.get().colour;
  select.addEventListener('change', () => store.set({ colour: select.value }));

  const size = document.getElementById('size-mode');
  size.checked = store.get().sizeByEnrolment;
  size.addEventListener('change', () => store.set({ sizeByEnrolment: size.checked }));

  const areas = document.getElementById('areas-layer');
  areas.checked = store.get().deprivationLayer;
  areas.addEventListener('change', () => store.set({ deprivationLayer: areas.checked }));
  // The 2022 values have no "affluent" category above Affluent.
  const shown = HP_CLASSES.filter((c) => !c.value.endsWith(' Affluent') || c.value === 'Affluent');
  document.getElementById('areas-classes').replaceChildren(
    ...shown.map((c) => {
      const item = document.createElement('li');
      item.className = 'flex items-center gap-2';
      const swatch = document.createElement('span');
      swatch.className = 'inline-block h-3.5 w-5 shrink-0 border border-ink/30';
      swatch.style.backgroundColor = c.colour;
      swatch.style.opacity = '0.75';
      item.append(swatch, c.label);
      return item;
    }),
  );

  const details = document.getElementById('legend');
  details.open = window.matchMedia('(min-width: 48rem)').matches || store.get().deprivationLayer;
}

export function syncAreas(state) {
  document.getElementById('areas-layer').checked = state.deprivationLayer;
  document.getElementById('areas-key').hidden = !state.deprivationLayer;
}

// Show the classes of a mode with the number of schools in each.
export function renderLegend(mode, schools) {
  document.getElementById('colour-mode').value = mode.key;
  const counts = classCounts(mode, schools);
  const list = document.getElementById('legend-classes');
  list.replaceChildren(
    ...mode.classes
      .filter((c) => counts.get(c.value) > 0)
      .map((c) => {
        const item = document.createElement('li');
        item.className = 'flex items-center gap-2';
        const swatch = document.createElement('span');
        swatch.className = 'inline-block size-3.5 shrink-0 rounded-full border border-ink/50';
        swatch.style.backgroundColor = c.colour;
        const label = document.createElement('span');
        label.className = 'grow';
        label.textContent = c.label;
        const count = document.createElement('span');
        count.className = 'tabular-nums text-muted';
        count.textContent = number.format(counts.get(c.value));
        item.append(swatch, label, count);
        return item;
      }),
  );
  const note = document.getElementById('legend-note');
  note.textContent = mode.note ?? '';
  note.hidden = !mode.note;
}
