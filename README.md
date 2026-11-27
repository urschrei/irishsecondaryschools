# Irish post-primary schools

Open datasets of the post-primary schools aided by the Department of Education, with locations, enrolment history, area deprivation and access measures.

The current data is for the 2025/26 school year: 721 schools.

## Files

| File | Contents |
| --- | --- |
| `data/post_primary_schools.geojson` | One point for each school in the latest school year. |
| `data/post_primary_schools.parquet` | The same data as GeoParquet. |
| `data/post_primary_schools.csv` | The same data without geometry. Use `latitude` and `longitude`. |
| `data/post_primary_enrolment.csv` | Enrolment for each school and year, 2011/12 to 2025/26. |
| `data/post_primary_enrolment.parquet` | The same data as Parquet. |
| `irish_secondary_schools_geocoded_2022.geojson` | The 2021/22 dataset from 2022. It is not updated. |

`roll_number` is the Department's identifier for a school. Use it to join the files to each other and to other Department datasets.

The files do not contain the names, email addresses or telephone numbers of principals or schools.

## Columns in the school files

### From the Department of Education list

| Column | Description |
| --- | --- |
| `roll_number` | Department roll number, for example `60010P`. |
| `academic_year` | First calendar year of the school year. `2025` is 2025/26. |
| `name` | Official school name. |
| `address_1` to `address_4` | Postal address. |
| `eircode` | Eircode. |
| `county`, `local_authority` | County and local authority. |
| `planning_area` | Department school planning area. |
| `school_type` | Secondary, Vocational, Community or Comprehensive. |
| `ethos`, `patron` | Ethos and patron body. |
| `gender` | Boys, Girls or Mixed. |
| `attendance_type` | Day, Boarding or Mixed. |
| `irish_classification` | Use of Irish as a teaching language. |
| `fee_paying`, `deis`, `gaeltacht`, `island` | `true` or `false`. |
| `female`, `male`, `total` | Enrolment on 30 September. |
| `jc1`, `jc2`, `jc3`, `ty`, `lc1`, `lc2` | Enrolment by year group: Junior Cycle years 1 to 3, Transition Year, Leaving Certificate years 1 and 2. `lc2` includes repeat students. |
| `latitude`, `longitude` | Location given by the Department, WGS 84. |

### Added by this project

| Column | Description |
| --- | --- |
| `total_5y_earlier` | `total` five school years earlier. Empty if the school was not listed then. |
| `change_5y_pct` | Percentage change from `total_5y_earlier` to `total`. |
| `small_area` | 2022 CSO Small Area that contains the school. |
| `urban_area` | CSO urban area of that Small Area. Empty for rural Small Areas. |
| `ed_id`, `ed_name` | 2022 Electoral Division (ED) of that Small Area. |
| `hp_relative_index` | Pobal HP Deprivation Index 2022, relative score, for the ED. Lower scores show more deprivation. |
| `hp_absolute_index` | Pobal HP Deprivation Index 2022, absolute score, for the ED. |
| `hp_category` | Pobal label for the relative score. The 2022 ED values run from "Extremely Disadvantaged" to "Affluent". |
| `nearest_school` | `roll_number` of the nearest other post-primary school. |
| `nearest_school_km` | Straight-line distance to that school, in kilometres. |
| `schools_within_5km` | Number of other post-primary schools within 5 km in a straight line. |

## Columns in the enrolment files

| Column | Description |
| --- | --- |
| `roll_number`, `academic_year`, `name` | As in the school files. `name` is the name in that year. |
| `school_year` | School year as text, for example `2025/26`. |
| `female`, `male`, `total` | Enrolment on 30 September. |
| `jc1` to `lc2` | Enrolment by year group. Available from 2020/21. |
| `includes_plc` | `true` for years whose lists include further-education colleges and Post-Leaving Certificate (PLC) enrolment. |

## Limitations of the data

- **Change in definition in 2016/17.** Up to 2015/16, the Department lists include further-education colleges and PLC students. From 2016/17 they do not. Total enrolment falls by 7% between those years for this reason. Do not compare totals across this break without `includes_plc`.
- **Five-year change for new schools.** A school that opened in the last five years with one year group shows a large `change_5y_pct`. The figure does not describe growth of an established school.
- **Deprivation describes the area.** The index applies to the ED that contains the school building. It does not describe the pupils of the school. Use `deis` for the Department's classification of the school.
- **Generalised boundaries.** The Small Areas are generalised to 20 m. A school very near a boundary can fall in the adjacent Small Area.
- **Straight-line distance.** The access measures do not use the road network or travel time.
- **Temporary sites.** Some new schools operate from temporary buildings. The Department location can be the temporary site.

## Sources and licence

| Source | Publisher | Licence |
| --- | --- | --- |
| [Post-primary school lists](https://www.gov.ie/en/department-of-education/collections/post-primary-schools-enrolment-figures/), 2011/12 to 2025/26 | Department of Education | CC BY 4.0 |
| [HP Deprivation Index scores 2022](https://data.gov.ie/dataset/pobal-hp-deprivation-index-scores-2022) | Pobal | CC BY 4.0 |
| [CSO Small Areas 2022, generalised 20 m](https://data-osi.opendata.arcgis.com/datasets/9472cff586d74f2ba3c240d4344c5720_0) | Tailte Éireann | CC BY 4.0 |

`sources.toml` records the URL and SHA-256 checksum of each source file.

The files in `data/` are derived from these sources. When you use them, attribute the Department of Education, Pobal and Tailte Éireann. The code in this repository and the author's contributions to the data are dedicated to the public domain under CC0. See `LICENSE`.

## The 2022 dataset

`irish_secondary_schools_geocoded_2022.geojson` contains the 728 schools in the 2021/22 list. At that time the Department did not publish locations. The locations came from the schooldays.ie school map, joined on roll number, with 16 schools placed by hand. The Department has published locations since 2023/24, and the files in `data/` use them.

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

To add a new school year, add a `[[source]]` entry to `sources.toml` with the file URL, the `academic_year` and its SHA-256 checksum. Then run the steps above. The Department changes column names from year to year. If the build fails on a new header, add it to `HEADER_MAP` in `src/irish_schools/dept.py`.

## Reporting an error

Open an [issue](https://github.com/urschrei/irishsecondaryschools/issues). For an error in a school's details or location, include its roll number. Errors in the Department's data are best reported to the Department at statistics@education.gov.ie.
