import { loadJson } from './data.js';
import { h } from './dom.js';

const CONTENTS = {
  'primary_schools.geojson': 'Primary schools, including special schools, as points.',
  'primary_schools.parquet': 'Primary schools as GeoParquet.',
  'primary_enrolment.parquet': 'Enrolment of each primary school in each year from 2011/12.',
  'post_primary_schools.geojson': 'Post-primary schools as points.',
  'post_primary_schools.parquet': 'Post-primary schools as GeoParquet.',
  'post_primary_enrolment.parquet': 'Enrolment of each post-primary school in each year from 2011/12.',
};

const size = new Intl.NumberFormat('en-IE', { maximumFractionDigits: 1 });

export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 ** 2) return `${size.format(bytes / 1024)} KB`;
  return `${size.format(bytes / 1024 ** 2)} MB`;
}

async function start() {
  const status = document.getElementById('files-status');
  try {
    const meta = await loadJson('meta.json');
    for (const node of document.querySelectorAll('[data-school-year]')) {
      node.textContent = meta.school_year;
    }
    document.getElementById('files').replaceChildren(
      ...meta.downloads.map((download) =>
        h('tr', { class: 'border-t border-rule' }, [
          h('td', { class: 'px-3 py-2' }, [
            h('a', {
              href: `./downloads/${download.file}`,
              download: download.file,
              class: 'text-sign underline underline-offset-2',
              text: download.file,
            }),
          ]),
          h('td', { class: 'px-3 py-2', text: CONTENTS[download.file] ?? '' }),
          h('td', { class: 'px-3 py-2 text-right whitespace-nowrap tabular-nums', text: formatBytes(download.bytes) }),
        ]),
      ),
    );
    document.getElementById('checksums').replaceChildren(
      ...meta.downloads.flatMap((download) => [
        h('dt', { class: 'font-bold', text: download.file }),
        h('dd', {}, [h('code', { class: 'break-all', text: download.sha256 })]),
      ]),
    );
  } catch (error) {
    status.textContent = `The file list did not load. ${error.message}`;
    throw error;
  }
}

start();
