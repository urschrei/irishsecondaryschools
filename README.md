# What is This
A `geojson` file containing data about Irish secondary schools.

# FAQ

## How many schools are in this list?
728

## Where did you get the data
https://www.gov.ie/en/collection/post-primary-schools/  

Specifically:
> The source for this data is the National School Annual Census for 2021/2022, which is returned via the Primary Online Database (POD). This includes both the Mainstream Census and the Special School Annual Census. Data is anchored on the census date of 30th September 2021. **Note that only schools aided by the Department of Education are included in this list**. This data is provisional and was published in December 2021. Final data will be published in June 2022. The final data will replace the provisional data.

## No, I meant the _spatial_ data
I collated data from a variety of sources. I won't be elaborating on this.

## Is there a license for this data?
The school data is published as open data by the Irish government. I'm licensing my contributions as CC0. See the license file for more detail. 

## Are you accepting responsibility for any errors?
I am not. The spatial data in this dataset should not be considered canonical.

## I found an error in the dataset
Please open an [issue](https://github.com/urschrei/irishsecondaryschools/issues) and I'll fix it.

## A school is missing
Please open an [issue](https://github.com/urschrei/irishsecondaryschools/issues) and I'll fix it.

## Why are you doing this?
I needed the locations of all Irish secondary schools 'aided by the Department of Education'

## I want to contribute some data
Wonderful. Please open a [Pull Request](https://github.com/urschrei/irishsecondaryschools/pulls).

## Is there a canonical unique ID per school?
Yes: `Roll Number`. This will be available for any school dataset published by the Department of Education.

# Headers

| Header      |
| ----------- |
| Roll Number      |
| Official School Name   |
| Principal Name   |
| Address 1   |
| Address 2   |
| Address 3   |
| Address 4   |
| Eircode   |
| Email   |
| Phone   |
| Fee-Charging School (Y/N)   |
| Post Primary School Type   |
| Irish Classification - Post Primary   |
| Ethos/Religion   |
| Count Unique Enrolments - <=30th Sept   |
| total   |
| latitude   |
| longitude   |
