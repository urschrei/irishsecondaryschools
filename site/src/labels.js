// Labels and number formats shared by the list, detail and comparison views.

export const number = new Intl.NumberFormat('en-IE');
export const decimal = new Intl.NumberFormat('en-IE', { maximumFractionDigits: 1 });

export const CATEGORY_LABELS = {
  primary: 'Primary',
  special: 'Special school',
  post_primary: 'Post-primary',
};

const COUNTY_LINE = /^co\.?\s/i;

// Return the town or district of a school: the last address line that is
// not a county.
export function place(school) {
  const lines = [school.address_1, school.address_2, school.address_3, school.address_4]
    .filter(Boolean)
    .filter((line) => !COUNTY_LINE.test(line));
  return lines.at(-1) ?? school.county ?? '';
}

export function pupils(count) {
  return `${number.format(count)} ${count === 1 ? 'pupil' : 'pupils'}`;
}

export function schoolYear(year) {
  return `${year}/${String((year + 1) % 100).padStart(2, '0')}`;
}

export function byName(a, b) {
  return a.name.localeCompare(b.name, 'en-IE');
}
