import { CATEGORY_LABELS, place, pupils } from './labels.js';

const PAGE_SIZE = 50;

// Render the result list, PAGE_SIZE schools at a time.
export function createList(onSelect) {
  const list = document.getElementById('result-list');
  const more = document.getElementById('show-more');
  let schools = [];
  let shown = PAGE_SIZE;
  let describe = () => '';

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
    // describeSchool returns text to show before the place, such as a distance.
    update(next, describeSchool = () => '') {
      schools = next;
      describe = describeSchool;
      shown = PAGE_SIZE;
      render();
    },
  };
}
