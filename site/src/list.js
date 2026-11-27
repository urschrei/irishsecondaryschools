import { CATEGORY_LABELS, number, place, pupils } from './labels.js';

const PAGE_SIZE = 50;

// Render the result list, PAGE_SIZE schools at a time. Until a search,
// filter or place narrows the schools, the list shows guidance and a
// button that lists all schools.
export function createList(onSelect) {
  const list = document.getElementById('result-list');
  const more = document.getElementById('show-more');
  let schools = [];
  let shown = PAGE_SIZE;
  let describe = () => '';
  let narrowed = false;
  let listAll = false;

  function prompt() {
    const li = document.createElement('li');
    li.className = 'space-y-3 px-5 py-4';
    const text = document.createElement('p');
    text.className = 'text-muted';
    text.textContent =
      'Search, filter or choose a place to list schools here, or select a school on the map.';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'button';
    button.textContent = `List all ${number.format(schools.length)} schools`;
    button.addEventListener('click', () => {
      listAll = true;
      render();
      list.querySelector('button[data-roll]')?.focus();
    });
    li.append(text, button);
    return li;
  }

  function item(school) {
    const li = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.roll = school.roll_number;
    button.className = 'block w-full px-5 py-2.5 text-left hover:bg-white focus-visible:bg-white';
    const name = document.createElement('span');
    name.className = 'block font-bold';
    name.textContent = school.name;
    const details = document.createElement('span');
    details.className = 'block text-sm text-muted';
    details.textContent = [
      describe(school),
      place(school),
      CATEGORY_LABELS[school.category].toLowerCase(),
      pupils(school.total ?? 0),
    ]
      .filter(Boolean)
      .join(', ');
    button.append(name, details);
    li.append(button);
    return li;
  }

  function render() {
    if (!narrowed && !listAll) {
      list.replaceChildren(prompt());
      more.hidden = true;
      return;
    }
    if (!schools.length) {
      const empty = document.createElement('li');
      empty.className = 'px-5 py-3 text-muted';
      empty.textContent = 'No schools match the search and filters. Change the search, or clear the filters.';
      list.replaceChildren(empty);
      more.hidden = true;
      return;
    }
    list.replaceChildren(...schools.slice(0, shown).map(item));
    const remaining = schools.length - shown;
    more.hidden = remaining <= 0;
    more.textContent = `Show ${Math.min(PAGE_SIZE, remaining)} more`;
  }

  list.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-roll]');
    if (button) onSelect(button.dataset.roll);
  });
  more.addEventListener('click', () => {
    const first = shown;
    shown += PAGE_SIZE;
    render();
    list.children[first]?.querySelector('button').focus();
  });

  return {
    // describeSchool returns text to show before the place, such as a
    // distance. isNarrowed is true when a search, filter or place applies.
    update(next, { describeSchool = () => '', isNarrowed = true } = {}) {
      schools = next;
      describe = describeSchool;
      if (isNarrowed) listAll = false;
      narrowed = isNarrowed;
      shown = PAGE_SIZE;
      render();
    },
  };
}
