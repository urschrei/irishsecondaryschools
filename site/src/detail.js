import { GROUP_LABELS, enrolmentChart, enrolmentTable, groupBars } from './charts.js';
import { h } from './dom.js';
import { CATEGORY_LABELS, decimal, number, pupils, schoolYear } from './labels.js';
import { HP_CLASSES } from './modes.js';

const PRIMARY_GROUPS = Object.keys(GROUP_LABELS).filter((key) => !/^(jc|ty|lc)/.test(key));
const POST_PRIMARY_GROUPS = ['jc1', 'jc2', 'jc3', 'ty', 'lc1', 'lc2'];

const GENDER = { Boys: 'Boys', Girls: 'Girls', Mixed: 'Girls and boys' };
const ATTENDANCE = { Day: 'Day pupils', Boarding: 'Boarding pupils', Mixed: 'Day and boarding pupils' };
const HP_LABELS = Object.fromEntries(HP_CLASSES.map((c) => [c.value, c.label]));

const yesNo = (value) => (value === undefined ? undefined : value ? 'Yes' : 'No');

// "BALLINTEMPLE (CORK)" becomes "Ballintemple (Cork)".
export function titleCase(text) {
  return text.toLowerCase().replace(/(^|[\s(-])(\p{L})/gu, (_, before, letter) => before + letter.toUpperCase());
}

export function coordinateKey(coordinates) {
  return coordinates ? coordinates.join(',') : null;
}

function heading(text) {
  return h('h3', { class: 'mt-6 mb-2 font-bold', text });
}

function facts(rows) {
  return h(
    'dl',
    { class: 'grid grid-cols-[minmax(7rem,auto)_1fr] gap-x-4 gap-y-1 text-sm' },
    rows
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .flatMap(([label, value]) => [
        h('dt', { class: 'text-muted', text: label }),
        h('dd', {}, [value]),
      ]),
  );
}

function schoolButton(school, extra, onSelect) {
  const button = h('button', {
    type: 'button',
    class: 'text-left text-sign underline underline-offset-2',
    text: school.name,
  });
  button.addEventListener('click', () => onSelect(school.roll_number));
  return h('span', {}, [button, extra ? ` ${extra}` : null]);
}

function changeText(school, years) {
  const earlier = schoolYear(years.at(-1) - 5);
  if (school.change_5y_pct === undefined) return `Not listed in ${earlier}.`;
  const pct = school.change_5y_pct;
  const direction = pct > 0 ? 'Up' : pct < 0 ? 'Down' : 'No change';
  const amount = pct === 0 ? '' : ` ${decimal.format(Math.abs(pct))}%`;
  return `${direction}${amount} from ${number.format(school.total_5y_earlier)} in ${earlier}.`;
}

function genderSplit(school) {
  const parts = [];
  if (school.female) parts.push(`${number.format(school.female)} girls`);
  if (school.male) parts.push(`${number.format(school.male)} boys`);
  return parts.length ? `${parts.join(', ')}.` : '';
}

function contact(school) {
  const lines = [school.address_1, school.address_2, school.address_3, school.address_4].filter(Boolean);
  const phones = (school.phone ?? '').split(';').filter(Boolean);
  const displays = (school.phone_display ?? '').split('; ');
  return h('div', { class: 'mt-3 space-y-1 text-sm' }, [
    h('address', { class: 'not-italic' }, lines.flatMap((line, i) => (i ? [h('br'), line] : [line]))),
    school.eircode ? h('p', { text: `Eircode ${school.eircode}` }) : null,
    ...phones.map((e164, i) =>
      h('p', {}, [
        h('a', {
          href: `tel:${e164}`,
          class: 'text-sign underline underline-offset-2',
          text: displays[i] ?? e164,
        }),
      ]),
    ),
  ]);
}

export function createDetail({ byRoll, meta, loadEnrolment, onSelect, onClose, extras }) {
  const panel = document.getElementById('detail');
  const browse = document.getElementById('browse');
  const atLocation = new Map();
  for (const school of byRoll.values()) {
    const key = coordinateKey(school.coordinates);
    if (!key) continue;
    if (!atLocation.has(key)) atLocation.set(key, []);
    atLocation.get(key).push(school);
  }

  async function enrolmentSection(school) {
    const section = h('section', { 'aria-labelledby': 'detail-enrolment' }, [
      h('h3', { id: 'detail-enrolment', class: 'mt-6 mb-2 font-bold', text: `Enrolment, ${meta.school_year}` }),
      h('p', { class: 'text-2xl font-bold tabular-nums', text: pupils(school.total ?? 0) }),
      h('p', {
        class: 'text-sm text-muted',
        text: `${genderSplit(school)} ${changeText(school, meta.years)}`,
      }),
    ]);
    try {
      const enrolment = await loadEnrolment();
      const totals = enrolment.schools[school.roll_number];
      if (totals) {
        const plc = school.level === 'post_primary' ? meta.post_primary_plc_until : null;
        section.append(
          h('figure', { class: 'mt-3' }, [
            enrolmentChart(enrolment.years, totals, plc),
            h('figcaption', { class: 'text-xs text-muted' }, [
              `Pupils on 30 September of each school year, ${schoolYear(enrolment.years[0])} to ${schoolYear(enrolment.years.at(-1))}.`,
              plc ? ` Up to ${schoolYear(plc)}, left of the dashed line, the figures include further-education and PLC students.` : '',
            ]),
          ]),
          h('details', { class: 'mt-1 text-sm' }, [
            h('summary', { class: 'cursor-pointer text-sign', text: 'Show the figures' }),
            enrolmentTable(enrolment.years, totals),
          ]),
        );
      }
    } catch (error) {
      section.append(h('p', { class: 'text-sm', text: `The enrolment history did not load. ${error.message}` }));
    }
    const groups = school.level === 'post_primary' ? POST_PRIMARY_GROUPS : PRIMARY_GROUPS;
    const bars = groupBars(school, groups);
    if (bars) {
      section.append(
        h('h4', {
          class: 'mt-4 mb-2 text-sm font-bold',
          text: school.level === 'post_primary' ? 'By year group' : 'By class',
        }),
        bars,
      );
    }
    return section;
  }

  function areaSection(school) {
    if (!school.ed_name) return null;
    const score = school.hp_relative_index;
    return h('section', {}, [
      heading('Area'),
      facts([
        ['Urban area', school.urban_area ?? 'None (rural area)'],
        ['Electoral Division', titleCase(school.ed_name)],
        [
          'Deprivation',
          `${HP_LABELS[school.hp_category] ?? school.hp_category}, relative score ${score > 0 ? '+' : ''}${decimal.format(score)}`,
        ],
      ]),
      h('p', {
        class: 'mt-2 text-xs text-muted',
        text: 'Pobal HP Deprivation Index 2022. The index describes the Electoral Division that contains the school, not its pupils. For the Department’s classification of the school, see DEIS.',
      }),
    ]);
  }

  function nearbySection(school) {
    const rows = [];
    const nearest = school.nearest_school && byRoll.get(school.nearest_school);
    if (nearest) {
      rows.push([
        'Nearest school',
        schoolButton(nearest, `(${decimal.format(school.nearest_school_km)} km)`, onSelect),
      ]);
    }
    if (school.schools_within_5km !== undefined) {
      rows.push(['Within 5 km', `${number.format(school.schools_within_5km)} other schools`]);
    }
    const shared = (atLocation.get(coordinateKey(school.coordinates)) ?? []).filter(
      (other) => other.roll_number !== school.roll_number,
    );
    const sameSite = shared.length
      ? h('div', { class: 'mt-3 text-sm' }, [
          h('p', { class: 'text-muted', text: 'At the same location:' }),
          h(
            'ul',
            { class: 'mt-1 space-y-1' },
            shared.map((other) => h('li', {}, [schoolButton(other, null, onSelect)])),
          ),
        ])
      : null;
    if (!rows.length && !sameSite) return null;
    const note =
      school.level === 'primary'
        ? 'Great-circle distances to other primary schools. Special schools are not counted.'
        : 'Great-circle distances to other post-primary schools.';
    return h('section', {}, [
      heading('Nearby schools'),
      facts(rows),
      h('p', { class: 'mt-2 text-xs text-muted', text: note }),
      extras?.nearby?.(school) ?? null,
      sameSite,
    ]);
  }

  function aboutSection(school) {
    return h('section', {}, [
      heading('About the school'),
      facts([
        ['Roll number', school.roll_number],
        ['School type', school.school_type],
        ['School level', school.school_level],
        ['Ethos', school.ethos],
        ['Patron', school.patron],
        ['Teaching through Irish', school.irish_classification],
        ['Pupils', GENDER[school.gender]],
        ['Attendance', ATTENDANCE[school.attendance_type]],
        ['Fee-paying', school.level === 'post_primary' ? yesNo(school.fee_paying) : undefined],
        ['DEIS', yesNo(school.deis)],
        ['Gaeltacht', yesNo(school.gaeltacht)],
        ['Island', yesNo(school.island)],
        ['First listed', school.first_listed === meta.years[0] ? `${schoolYear(school.first_listed)} or earlier` : schoolYear(school.first_listed)],
      ]),
    ]);
  }

  let current = null;

  return {
    async show(school) {
      current = school.roll_number;
      const back = h('button', {
        type: 'button',
        class: 'text-sign underline underline-offset-2',
        text: 'Back to the list',
      });
      back.addEventListener('click', onClose);
      const title = h('h2', { id: 'detail-name', tabindex: '-1', class: 'mt-3 text-2xl font-bold', text: school.name });
      const header = h('header', {}, [
        back,
        title,
        h('p', { class: 'text-muted', text: CATEGORY_LABELS[school.category] }),
        school.coordinates
          ? null
          : h('p', {
              class: 'mt-2 text-sm',
              text: 'The Department gives no location for this school, so it is not on the map.',
            }),
        contact(school),
        extras?.actions?.(school) ?? null,
      ]);
      const enrolment = h('div');
      panel.replaceChildren(header, enrolment, aboutSection(school), areaSection(school) ?? '', nearbySection(school) ?? '');
      browse.hidden = true;
      panel.hidden = false;
      panel.scrollTop = 0;
      document.getElementById('panel').scrollTop = 0;
      title.focus({ preventScroll: true });
      const section = await enrolmentSection(school);
      if (current === school.roll_number) enrolment.replaceWith(section);
    },
    hide() {
      current = null;
      panel.hidden = true;
      browse.hidden = false;
    },
  };
}
