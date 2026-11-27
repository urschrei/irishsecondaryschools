# Irish schools

Open datasets of the primary and post-primary schools aided by the Department of Education, with locations, enrolment history, area deprivation and access measures.

The current data is for the 2025/26 school year: 3,216 primary schools, of which 149 are special schools, and 721 post-primary schools.

## Files

| File | Contents |
| --- | --- |
| `data/primary_schools.geojson` | Point data for primary schools in the 2025/26 school year. |
| `data/primary_schools.parquet` | data as GeoParquet. |
| `data/primary_enrolment.parquet` | Enrolment for each primary school and year, 2011/12 to 2025/26. |
| `data/post_primary_schools.geojson` | Point data for post-primary schools in the 2025/26 school year. |
| `data/post_primary_schools.parquet` | data as GeoParquet. |
| `data/post_primary_enrolment.parquet` | Enrolment for each post-primary school and year, 2011/12 to 2025/26. |
| `irish_secondary_schools_geocoded_2022.geojson` | The 2021/22 post-primary dataset from 2022. Not updated. |

`roll_number` is the Department's unique identifier for a school, which can be used to join the files to each other and to other Department datasets.

## Map viewer

The `site/` directory holds a map of the schools. It searches by name, address, roll number or Eircode, filters by the attributes of a school, lists the schools near a place, and compares up to four schools. For each school it shows enrolment since 2011/12, distances to other schools, and the deprivation score of the area. It can download the schools that match a search or filters as GeoJSON.

The workflow in `.github/workflows/pages.yml` publishes the viewer to GitHub Pages when `main` changes. The base map is from OpenFreeMap, with data from OpenStreetMap contributors.

## Columns in the school files

### From the Department of Education lists

| Column | Level | Description |
| --- | --- | --- |
| `roll_number` | Both | Department roll number, for example `60010P`. |
| `academic_year` | Both | First calendar year of the school year. `2025` is 2025/26. |
| `name` | Both | School name. The Department name with a standard capitalisation and spelling: see [School names](#school-names). |
| `address_1` to `address_4` | Both | Postal address. |
| `eircode` | Both | Eircode. |
| `phone` | Both | School telephone number in E.164 form, for example `+35318411594`. Where a school has more than one number, they are separated by `;`. |
| `county`, `local_authority` | Both | County and local authority. |
| `planning_area` | Both | Department school planning area. |
| `special_school` | Primary | `true` for schools on the Department's list of special schools. |
| `school_type` | Both | Primary: Ordinary, or Ordinary with Special Classes. Empty for special schools. Post-primary: Secondary, Vocational, Community or Comprehensive. |
| `school_level` | Primary | All Through, Junior or Senior. Empty for special schools. |
| `ethos`, `patron` | Both | Ethos and patron body. |
| `gender` | Post-primary | Boys, Girls or Mixed. |
| `attendance_type` | Post-primary | Day, Boarding or Mixed. |
| `irish_classification` | Both | Use of Irish as a teaching language. |
| `fee_paying` | Post-primary | `true` or `false`. |
| `deis`, `gaeltacht`, `island` | Both | `true` or `false`. |
| `female`, `male`, `total` | Both | Enrolment on 30 September. |
| `junior_infants`, `senior_infants`, `class_1` to `class_6` | Primary | Enrolment by class. Mainstream schools only. |
| `jc1`, `jc2`, `jc3`, `ty`, `lc1`, `lc2` | Post-primary | Enrolment by year group: Junior Cycle years 1 to 3, Transition Year, Leaving Certificate years 1 and 2. `lc2` includes repeat students. |
| `latitude`, `longitude` | Both | Location given by the Department, WGS 84. |

### Added by this project

| Column | Description |
| --- | --- |
| `name_query` | Words in `name` that are possibly spelled incorrectly, with an alternative spelling, for example `Rath or Ráth`. Empty if there are none. |
| `total_5y_earlier` | `total` five school years earlier. Empty if the school was not listed then. |
| `change_5y_pct` | Percentage change from `total_5y_earlier` to `total`. |
| `small_area` | 2022 CSO Small Area that contains the school. |
| `urban_area` | CSO urban area of that Small Area. Empty for rural Small Areas. |
| `ed_id`, `ed_name` | 2022 Electoral Division (ED) of that Small Area. |
| `hp_relative_index` | Pobal HP Deprivation Index 2022, relative score, for the ED. Lower scores show more deprivation. |
| `hp_absolute_index` | Pobal HP Deprivation Index 2022, absolute score, for the ED. |
| `hp_category` | Pobal label for the relative score. The 2022 ED values run from "Extremely Disadvantaged" to "Affluent". |
| `nearest_school` | `roll_number` of the nearest other school at the same level. For primary schools, only mainstream schools count. |
| `nearest_school_km` | Great-circle distance to that school, in kilometres. |
| `schools_within_5km` | Number of other schools at the same level within a great-circle distance of 5 km. For primary schools, only mainstream schools count. |

## School names

The build changes the Department names in two ways:

1. It converts names in capital letters to mixed case, for example `S N NA NGAEL` to `S N na nGael`. Names that the Department gives in mixed case keep their capitalisation.
2. It applies the tables in `spellings.toml`:
   - `[words]` gives the correct spelling of words that the Department lists often give without accents or apostrophes, for example `Padraig` to `Pádraig` and `Marys` to `Mary's`.
   - `[queries]` lists words that are possibly spelled incorrectly but that have more than one possible correct spelling, for example `Rath`, which can be `Ráth`. The build does not change these words. It records them in `name_query`.
   - `[schools]` gives the correct name of a single school, by roll number. It replaces the name in each year that the school has its current name. A school in this table has an empty `name_query`.

To correct a name in `name_query`, add the school to `[schools]` and run `schools build`.

## Columns in the enrolment files

| Column | Level | Description |
| --- | --- | --- |
| `roll_number`, `academic_year`, `name` | Both | As in the school files. `name` is the name in that year. |
| `school_year` | Both | School year as text, for example `2025/26`. |
| `special_school` | Primary | As in the school files. |
| `female`, `male`, `total` | Both | Enrolment on 30 September. |
| `junior_infants` to `class_6` | Primary | Enrolment by class. Available from 2020/21. |
| `special_class` | Primary | Enrolment in special classes. Available from 2020/21 to 2024/25. From 2025/26, the Department counts these pupils in their class. |
| `jc1` to `lc2` | Post-primary | Enrolment by year group. Available from 2020/21. |
| `includes_plc` | Post-primary | `true` for years whose lists include further-education colleges and Post-Leaving Certificate (PLC) enrolment. |

## Limitations of the data

- **Change in definition in 2016/17, post-primary.** Up to 2015/16, the post-primary lists include further-education colleges and PLC students. From 2016/17 they do not. Total enrolment falls by 7% between those years for this reason. Do not compare totals across this break without `includes_plc`.
- **Schools without a location.** The Department gives no coordinates for two special schools that opened in 2025/26: Lucan Community Special School (`20595W`) and Belmayne Community Special School (`20596B`). Their geometry and derived columns are empty.
- **Five-year change for new schools.** A school that opened in the last five years shows a large `change_5y_pct`. The figure does not describe growth of an established school.
- **Deprivation describes the area.** The index applies to the ED that contains the school building. It does not describe the pupils of the school. Use `deis` for the Department's classification of the school.
- **Generalised boundaries.** The Small Areas are generalised to 20 m. A school very near a boundary can fall in the adjacent Small Area.
- **Great-circle distance.** The access measures use the great-circle distance on a sphere with the mean radius of the Earth, 6,371.0088 km. They do not use the road network or travel time. Junior and senior primary schools often share a campus, so many primary schools have a nearest school at 0 km.
- **Temporary sites.** Some new schools operate from temporary buildings. The Department location can be the temporary site.
- **Corrected values.** The build corrects the value "Oridinary" in the primary `school_type` to "Ordinary". It gives `ethos` values one capitalisation at both levels, for example "Church of Ireland": the post-primary lists use capitals.

## Sources and licence

| Source | Publisher | Licence |
| --- | --- | --- |
| [Primary school lists](https://www.gov.ie/en/department-of-education/collections/primary-schools-enrolment-figures/), 2011/12 to 2025/26 | Department of Education | CC BY 4.0 |
| [Post-primary school lists](https://www.gov.ie/en/department-of-education/collections/post-primary-schools-enrolment-figures/), 2011/12 to 2025/26 | Department of Education | CC BY 4.0 |
| [HP Deprivation Index scores 2022](https://data.gov.ie/dataset/pobal-hp-deprivation-index-scores-2022) | Pobal | CC BY 4.0 |
| [CSO Small Areas 2022, generalised 20 m](https://data-osi.opendata.arcgis.com/datasets/9472cff586d74f2ba3c240d4344c5720_0) | Tailte Éireann | CC BY 4.0 |

`sources.toml` records the URL and SHA-256 checksum of each source file.

The files in `data/` are derived from these sources. When you use them, attribute the Department of Education, Pobal and Tailte Éireann. The code in this repository and the author's contributions to the data are dedicated to the public domain under CC0. See `LICENSE`.

## The 2022 dataset

`irish_secondary_schools_geocoded_2022.geojson` contains the 728 post-primary schools in the 2021/22 list. At that time the Department did not publish locations. The locations came from the schooldays.ie school map, joined on roll number, with 16 schools placed by hand. The Department has published locations since 2023/24, and the files in `data/` use them.

## Building the data

Prerequisites: [uv](https://docs.astral.sh/uv/).

1. Download and verify the source files into `sources/`:

   ```sh
   uv run schools fetch
   ```

2. Build the files in `data/`:

   ```sh
   uv run schools build
   ```

3. Run the tests. They check the reader and the built files:

   ```sh
   uv run pytest
   ```

To add a new school year, add a `[[source]]` entry to `sources.toml` with the file URL, the `kind` (`primary_list` or `post_primary_list`), the `academic_year` and the SHA-256 checksum. Then run the steps above. The Department changes column names from year to year. If the build fails on a new header, add it to `HEADER_MAP` in `src/irish_schools/dept.py`.

## Building the viewer

Prerequisites: [uv](https://docs.astral.sh/uv/) and Node.js 24.

1. Build the files in `data/`, as above. `schools build` also writes the Electoral Division layer to `site/public/areas/`. Commit this file with the data: the publishing workflow does not download the source files.

2. Write the viewer data, and copies of the files in `data/` for download, to `site/public/`:

   ```sh
   uv run schools web
   ```

3. Install the packages and start a development server:

   ```sh
   cd site
   npm ci
   npm run dev
   ```

4. Before you commit a change to the viewer, run `npm run lint`, `npm test` and `npm run build` in `site/`.

## Reporting an error

Open an [issue](https://github.com/urschrei/irishsecondaryschools/issues). For an error in a school's details or location, include its roll number. Errors in the Department's data are best reported to the Department at statistics@education.gov.ie.
