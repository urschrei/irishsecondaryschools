import { COLOUR_MODES, classCounts } from './modes.js';

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

  const details = document.getElementById('legend');
  details.open = window.matchMedia('(min-width: 48rem)').matches;
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
