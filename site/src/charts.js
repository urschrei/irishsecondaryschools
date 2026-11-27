import { h, svg } from './dom.js';
import { number, schoolYear } from './labels.js';

export const GROUP_LABELS = {
  junior_infants: 'Junior infants',
  senior_infants: 'Senior infants',
  class_1: 'First class',
  class_2: 'Second class',
  class_3: 'Third class',
  class_4: 'Fourth class',
  class_5: 'Fifth class',
  class_6: 'Sixth class',
  jc1: 'First year',
  jc2: 'Second year',
  jc3: 'Third year',
  ty: 'Transition Year',
  lc1: 'Fifth year',
  lc2: 'Sixth year',
};

// Return a round number at or above value, for the top of an axis.
export function niceCeiling(value) {
  if (value <= 0) return 10;
  const power = 10 ** Math.floor(Math.log10(value));
  return (Math.ceil((value / power) * 2) / 2) * power;
}

const WIDTH = 320;
const HEIGHT = 150;
const MARGIN = { top: 10, right: 12, bottom: 22, left: 40 };

// Line chart of total enrolment by year. plcUntil is the last year whose
// figures include further-education and PLC students, or null. Charts
// that are compared can share a maximum, so that their scales agree.
export function enrolmentChart(years, totals, plcUntil, maximum = null) {
  const top = niceCeiling(maximum ?? Math.max(...totals.filter((v) => v !== null)));
  const innerW = WIDTH - MARGIN.left - MARGIN.right;
  const innerH = HEIGHT - MARGIN.top - MARGIN.bottom;
  const x = (i) => MARGIN.left + (innerW * i) / (years.length - 1);
  const y = (v) => MARGIN.top + innerH - (innerH * v) / top;

  const grid = [0, top / 2, top].map((v) =>
    svg('g', {}, [
      svg('line', { x1: MARGIN.left, x2: WIDTH - MARGIN.right, y1: y(v), y2: y(v), class: 'stroke-rule' }),
      svg('text', {
        x: MARGIN.left - 6,
        y: y(v) + 4,
        'text-anchor': 'end',
        class: 'fill-muted text-[10px]',
        text: number.format(v),
      }),
    ]),
  );

  // Break the line where a year has no figure.
  let path = '';
  totals.forEach((v, i) => {
    if (v === null) return;
    path += `${i === 0 || totals[i - 1] === null ? 'M' : 'L'}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
  });

  const marks = [];
  if (plcUntil !== null) {
    const i = years.indexOf(plcUntil);
    if (i >= 0 && i < years.length - 1 && totals[i] !== null) {
      const bx = (x(i) + x(i + 1)) / 2;
      marks.push(
        svg('line', {
          x1: bx,
          x2: bx,
          y1: MARGIN.top,
          y2: MARGIN.top + innerH,
          'stroke-dasharray': '3 3',
          class: 'stroke-muted',
        }),
      );
    }
  }

  const points = totals.map((v, i) =>
    v === null ? null : svg('circle', { cx: x(i), cy: y(v), r: 2.5, class: 'fill-sign' }),
  );

  const xLabels = [0, years.length - 1].map((i) =>
    svg('text', {
      x: x(i),
      y: HEIGHT - 6,
      'text-anchor': i === 0 ? 'start' : 'end',
      class: 'fill-muted text-[10px]',
      text: schoolYear(years[i]),
    }),
  );

  return svg(
    'svg',
    { viewBox: `0 0 ${WIDTH} ${HEIGHT}`, class: 'w-full', 'aria-hidden': 'true' },
    [
      ...grid,
      ...marks,
      svg('path', { d: path, fill: 'none', 'stroke-width': 2, class: 'stroke-sign' }),
      ...points.filter(Boolean),
      ...xLabels,
    ],
  );
}

// Table of enrolment by year, for readers who cannot see the chart.
export function enrolmentTable(years, totals) {
  return h('table', { class: 'mt-2 w-full text-sm tabular-nums' }, [
    h('thead', {}, [
      h('tr', {}, [
        h('th', { scope: 'col', class: 'text-left font-normal text-muted', text: 'School year' }),
        h('th', { scope: 'col', class: 'text-right font-normal text-muted', text: 'Pupils' }),
      ]),
    ]),
    h(
      'tbody',
      {},
      years.map((year, i) =>
        h('tr', {}, [
          h('th', { scope: 'row', class: 'text-left font-normal', text: schoolYear(year) }),
          h('td', { class: 'text-right', text: totals[i] === null ? 'Not listed' : number.format(totals[i]) }),
        ]),
      ),
    ),
  ]);
}

// Horizontal bars of enrolment by class or year group.
export function groupBars(school, groups) {
  const values = groups.map((key) => school[key]).filter((v) => v !== undefined);
  if (!values.length) return null;
  const top = Math.max(...values, 1);
  return h(
    'dl',
    { class: 'grid grid-cols-[8rem_1fr_3rem] items-center gap-x-2 gap-y-1 text-sm' },
    groups
      .filter((key) => school[key] !== undefined)
      .flatMap((key) => [
        h('dt', { text: GROUP_LABELS[key] }),
        h('dd', { class: 'h-3 rounded-sm bg-white' }, [
          h('span', {
            class: 'block h-3 rounded-sm bg-sign',
            style: `width: ${(100 * school[key]) / top}%`,
          }),
        ]),
        h('dd', { class: 'text-right tabular-nums', text: number.format(school[key]) }),
      ]),
  );
}
