import { enrolmentChart } from './charts.js';
import { h } from './dom.js';
import { CATEGORY_LABELS, decimal, number, place, schoolYear } from './labels.js';
import { HP_CLASSES } from './modes.js';

export const MAX_COMPARE = 4;

// Add a roll number to the comparison, or remove it if it is there.
export function toggleCompare(rolls, roll) {
  if (rolls.includes(roll)) return rolls.filter((r) => r !== roll);
  if (rolls.length >= MAX_COMPARE) return rolls;
  return [...rolls, roll];
}

const HP_LABELS = Object.fromEntries(HP_CLASSES.map((c) => [c.value, c.label]));
const yesNo = (value) => (value === undefined ? '' : value ? 'Yes' : 'No');
const signed = (value) => (value === undefined ? 'Not listed five years earlier' : `${value > 0 ? '+' : ''}${decimal.format(value)}%`);

const ROWS = [
  ['Level', (s) => CATEGORY_LABELS[s.category]],
  ['Place', (s) => place(s)],
  ['County', (s) => s.county],
  ['Pupils', (s) => number.format(s.total ?? 0)],
  ['Girls', (s) => number.format(s.female ?? 0)],
  ['Boys', (s) => number.format(s.male ?? 0)],
  ['Change over five years', (s) => signed(s.change_5y_pct)],
  ['School type', (s) => s.school_type ?? ''],
  ['Ethos', (s) => s.ethos ?? ''],
  ['Patron', (s) => s.patron ?? ''],
  ['Teaching through Irish', (s) => s.irish_classification ?? ''],
  ['DEIS', (s) => yesNo(s.deis)],
  ['Gaeltacht', (s) => yesNo(s.gaeltacht)],
  ['Area deprivation', (s) => HP_LABELS[s.hp_category] ?? ''],
  ['Nearest school', (s) => (s.nearest_school_km === undefined ? '' : `${decimal.format(s.nearest_school_km)} km`)],
  ['Schools within 5 km', (s) => (s.schools_within_5km === undefined ? '' : number.format(s.schools_within_5km))],
];

export function setUpCompare(store, { byRoll, meta, loadEnrolment, onSelect }) {
  const firstListed = (s) =>
    s.first_listed === meta.years[0] ? `${schoolYear(s.first_listed)} or earlier` : schoolYear(s.first_listed);
  const rowsFor = () => [...ROWS, ['First listed', firstListed]];
  const bar = document.getElementById('compare-bar');
  const summary = document.getElementById('compare-summary');
  const dialog = document.getElementById('compare-dialog');
  const body = document.getElementById('compare-body');

  document.getElementById('compare-open').addEventListener('click', () => {
    render(store.get().compare);
    dialog.showModal();
  });
  document.getElementById('compare-clear').addEventListener('click', () => store.set({ compare: [] }));
  document.getElementById('compare-close').addEventListener('click', () => dialog.close());

  async function render(rolls) {
    const schools = rolls.map((roll) => byRoll.get(roll)).filter(Boolean);
    const header = h('tr', {}, [
      h('td'),
      ...schools.map((school) => {
        const name = h('button', {
          type: 'button',
          class: 'text-left font-bold text-sign underline underline-offset-2',
          text: school.name,
        });
        name.addEventListener('click', () => {
          dialog.close();
          onSelect(school.roll_number);
        });
        const remove = h('button', {
          type: 'button',
          class: 'mt-1 block text-sm text-muted underline underline-offset-2',
          'aria-label': `Remove ${school.name} from the comparison`,
          text: 'Remove',
        });
        remove.addEventListener('click', () => store.set({ compare: toggleCompare(store.get().compare, school.roll_number) }));
        return h('th', { scope: 'col', class: 'min-w-40 px-3 py-2 text-left align-top' }, [name, remove]);
      }),
    ]);
    const rows = rowsFor().map(([label, value]) =>
      h('tr', { class: 'border-t border-rule' }, [
        h('th', { scope: 'row', class: 'px-3 py-1.5 text-left align-top font-normal text-muted', text: label }),
        ...schools.map((school) => h('td', { class: 'px-3 py-1.5 align-top tabular-nums', text: value(school) })),
      ]),
    );
    const chartRow = h('tr', { class: 'border-t border-rule' }, [
      h('th', {
        scope: 'row',
        class: 'px-3 py-1.5 text-left align-top font-normal text-muted',
        text: `Pupils, ${schoolYear(meta.years[0])} to ${schoolYear(meta.years.at(-1))}, on one scale`,
      }),
      ...schools.map(() => h('td', { class: 'px-3 py-1.5' })),
    ]);
    body.replaceChildren(
      h('table', { class: 'w-full text-sm' }, [h('thead', {}, [header]), h('tbody', {}, [...rows, chartRow])]),
    );
    try {
      const enrolment = await loadEnrolment();
      const series = schools.map((school) => enrolment.schools[school.roll_number] ?? []);
      const maximum = Math.max(...series.flat().filter((v) => v !== null));
      schools.forEach((school, i) => {
        const plc = school.level === 'post_primary' ? meta.post_primary_plc_until : null;
        if (series[i].length) {
          chartRow.children[i + 1].append(enrolmentChart(enrolment.years, series[i], plc, maximum));
        }
      });
    } catch {
      // The table has the current figures without the history.
    }
  }

  return function sync(state) {
    const count = state.compare.length;
    bar.hidden = count === 0;
    summary.textContent = `${count} ${count === 1 ? 'school' : 'schools'} to compare`;
    document.getElementById('compare-open').disabled = count < 2;
    if (dialog.open) {
      if (count === 0) dialog.close();
      else render(state.compare);
    }
  };
}

// A button that adds a school to the comparison or removes it.
export function compareButton(store, school) {
  const rolls = store.get().compare;
  const included = rolls.includes(school.roll_number);
  const button = h('button', {
    type: 'button',
    class: 'button mt-3',
    text: included ? 'Remove from the comparison' : 'Add to the comparison',
  });
  if (!included && rolls.length >= MAX_COMPARE) {
    button.disabled = true;
    button.textContent = `The comparison has ${MAX_COMPARE} schools`;
  }
  button.addEventListener('click', () => {
    store.set({ compare: toggleCompare(store.get().compare, school.roll_number) });
    button.replaceWith(compareButton(store, school));
  });
  return button;
}
