import { CATEGORY_LABELS } from './labels.js';
import { CATEGORIES, DEFAULT_FILTERS, FLAGS, activeFilterCount, filterOptions } from './filters.js';
import { MODES_BY_KEY } from './modes.js';

const TEXT_DELAY_MS = 300;

const SELECTS = [
  { key: 'county', label: 'County', any: 'All counties' },
  { key: 'ethos', label: 'Ethos', any: 'Any ethos' },
  { key: 'type', label: 'School type', any: 'Any type' },
  { key: 'irish', label: 'Teaching through Irish', any: 'Any' },
  { key: 'gender', label: 'Pupils (post-primary)', any: 'Any' },
];

const CONTROL = 'w-full rounded border border-rule bg-white px-2 py-1.5';

function element(tag, attributes = {}, children = []) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (name === 'text') node.textContent = value;
    else node.setAttribute(name, value);
  }
  node.append(...children);
  return node;
}

function checkbox(name, value, label) {
  return element('label', { class: 'flex items-center gap-2' }, [
    element('input', { type: 'checkbox', name, value, class: 'size-4 accent-sign' }),
    label,
  ]);
}

function buildForm(form, options) {
  const levels = element('fieldset', { class: 'space-y-1' }, [
    element('legend', { class: 'mb-1 font-bold', text: 'Level' }),
    ...CATEGORIES.map((c) => checkbox('categories', c, CATEGORY_LABELS[c])),
  ]);

  const irishOptions = MODES_BY_KEY.get('irish').classes.map((c) => [c.value, c.label]);
  const genderLabels = { Boys: 'Boys only', Girls: 'Girls only', Mixed: 'Mixed' };
  const selects = element(
    'div',
    { class: 'grid grid-cols-2 gap-3' },
    SELECTS.map(({ key, label, any }) => {
      const values =
        key === 'irish'
          ? irishOptions
          : options[key].map((v) => [v, key === 'gender' ? genderLabels[v] ?? v : v]);
      const select = element('select', { id: `filter-${key}`, name: key, class: CONTROL }, [
        new Option(any, ''),
        ...values.map(([value, text]) => new Option(text, value)),
      ]);
      return element('div', {}, [
        element('label', { for: `filter-${key}`, class: 'block text-sm text-muted', text: label }),
        select,
      ]);
    }),
  );

  const patron = element('div', {}, [
    element('label', { for: 'filter-patron', class: 'block text-sm text-muted', text: 'Patron' }),
    element('input', {
      id: 'filter-patron',
      name: 'patron',
      type: 'text',
      list: 'patron-options',
      autocomplete: 'off',
      class: CONTROL,
    }),
    element(
      'datalist',
      { id: 'patron-options' },
      options.patron.map((p) => new Option(p, p)),
    ),
  ]);

  const flags = element('fieldset', { class: 'space-y-1' }, [
    element('legend', { class: 'mb-1 font-bold', text: 'Show only' }),
    ...FLAGS.map((flag) => checkbox(flag.key, '1', flag.label)),
  ]);

  const enrolment = element('fieldset', { class: 'grid grid-cols-2 gap-3' }, [
    element('legend', { class: 'mb-1 font-bold', text: 'Enrolment' }),
    ...['min', 'max'].map((key) =>
      element('div', {}, [
        element('label', {
          for: `filter-${key}`,
          class: 'block text-sm text-muted',
          text: key === 'min' ? 'At least' : 'At most',
        }),
        element('input', {
          id: `filter-${key}`,
          name: key,
          type: 'number',
          min: '0',
          step: '1',
          inputmode: 'numeric',
          class: CONTROL,
        }),
      ]),
    ),
  ]);

  const reset = element('button', {
    type: 'reset',
    class: 'rounded border border-sign px-3 py-1.5 text-sign hover:bg-white',
    text: 'Clear filters',
  });

  form.replaceChildren(levels, selects, patron, flags, enrolment, reset);
}

function readForm(form) {
  const data = new FormData(form);
  const number = (key) => {
    const value = data.get(key);
    if (value === null || value === '') return null;
    const n = Math.round(Number(value));
    return Number.isFinite(n) && n >= 0 ? n : null;
  };
  return {
    categories: CATEGORIES.filter((c) => data.getAll('categories').includes(c)),
    ...Object.fromEntries(SELECTS.map(({ key }) => [key, data.get(key) ?? ''])),
    patron: (data.get('patron') ?? '').trim(),
    min: number('min'),
    max: number('max'),
    ...Object.fromEntries(FLAGS.map((flag) => [flag.key, data.get(flag.key) === '1'])),
  };
}

export function setUpFilters(store, schools) {
  const form = document.getElementById('filter-form');
  const count = document.getElementById('filter-count');
  buildForm(form, filterOptions(schools));

  let timer;
  const apply = () => {
    clearTimeout(timer);
    store.set(readForm(form));
  };
  form.addEventListener('change', apply);
  form.addEventListener('input', (event) => {
    if (event.target.type === 'text' || event.target.type === 'number') {
      clearTimeout(timer);
      timer = setTimeout(apply, TEXT_DELAY_MS);
    }
  });
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    apply();
  });
  form.addEventListener('reset', (event) => {
    event.preventDefault();
    clearTimeout(timer);
    store.set(DEFAULT_FILTERS);
  });

  // Show the filters of a state in the form controls.
  return function sync(state) {
    for (const box of form.querySelectorAll('input[name="categories"]')) {
      box.checked = state.categories.includes(box.value);
    }
    for (const { key } of SELECTS) form.elements[key].value = state[key];
    if (document.activeElement !== form.elements.patron) form.elements.patron.value = state.patron;
    for (const key of ['min', 'max']) {
      if (document.activeElement !== form.elements[key]) form.elements[key].value = state[key] ?? '';
    }
    for (const flag of FLAGS) form.elements[flag.key].checked = state[flag.key];
    const active = activeFilterCount(state);
    count.textContent = active ? `(${active} on)` : '';
  };
}
