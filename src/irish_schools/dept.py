"""Read Department of Education school lists.

The Department changes sheet names, header rows and column names from
year to year. This module finds the school lists in each workbook and
gives them one schema. Post-primary workbooks have one list. Primary
workbooks have a list of mainstream schools and a list of special
schools.
"""

import re
from pathlib import Path

import pandas as pd

# Columns that identify people or give personal contact details. The
# build never writes them. School telephone numbers are not in this set.
PERSONAL_COLUMNS = {"principal_name", "email"}

# Map a normalised header (see _normalise_header) to a column name.
# Headers that are not in this map are discarded.
HEADER_MAP = {
    "academic year": "academic_year",
    "roll number": "roll_number",
    "official school name": "name",
    "address 1": "address_1",
    "address 2": "address_2",
    "address 3": "address_3",
    "address 4": "address_4",
    "county": "county",
    "local authority": "local_authority",
    "eircode": "eircode",
    "school latitude": "latitude",
    "school longitude": "longitude",
    "school planning area": "planning_area",
    "ethos/religion": "ethos",
    "ethos": "ethos",
    "patron": "patron",
    "post primary school type": "school_type",
    "irish classification - post primary": "irish_classification",
    "school gender - post primary": "gender",
    "pupil attendance type": "attendance_type",
    "fee paying school (y/n)": "fee_paying",
    "fee charging school (y/n)": "fee_paying",
    "fee-charging school (y/n)": "fee_paying",
    "island location (y/n)": "island",
    "gaeltacht area location (y/n)": "gaeltacht",
    "deis (y/n)": "deis",
    "open/closed status": "status",
    "female": "female",
    "female enrolment": "female",
    "total girls": "female",
    "male": "male",
    "male enrolment": "male",
    "total boys": "male",
    "total": "total",
    "total pupils": "total",
    "total enrolment": "total",
    "principal name": "principal_name",
    "email": "email",
    "phone": "phone",
    # Headers in the primary lists.
    "academic year (enrolment)": "academic_year",
    "roll no.": "roll_number",
    "official name": "name",
    "address line 1": "address_1",
    "address line 2": "address_2",
    "address line 3": "address_3",
    "address line 4": "address_4",
    "address (line 1)": "address_1",
    "address (line 2)": "address_2",
    "address (line 3)": "address_3",
    "address (line 4)": "address_4",
    "county name": "county",
    "county description": "county",
    "local authority desc": "local_authority",
    "local authority description": "local_authority",
    "ethos/religion desc": "ethos",
    "ethos description": "ethos",
    "school patron": "patron",
    "school type": "school_type",
    "school type description": "school_type",
    "school level": "school_level",
    "irish classification desc": "irish_classification",
    "irish classification description": "irish_classification",
    "island ind (y/n)": "island",
    "island (y/n)": "island",
    "gaeltacht ind (y/n)": "gaeltacht",
    "gaeltacht indicator": "gaeltacht",
    "gaeltacht indicator (y/n)": "gaeltacht",
    "deis": "deis",
    "girls": "female",
    "boys": "male",
    "stats year girls": "female",
    "stats year boys": "male",
    "stats year pupils": "total",
    "enrolment per return": "total",
    "principal": "principal_name",
    "phone number": "phone",
    "phone no.": "phone",
    "email address": "email",
}

# Headers that carry the year in their text, such as "Total 2025-2026",
# "TOTAL (2019-20)" or "Count Unique Enrolments - <=30th Sept".
TOTAL_PATTERN = re.compile(r"^(total\b.*\d{4}|count unique enrolments)")

CLASS_GROUPS = {
    "junior infants": "junior_infants",
    "senior infants": "senior_infants",
    "first class": "class_1",
    "second class": "class_2",
    "third class": "class_3",
    "fourth class": "class_4",
    "fifth class": "class_5",
    "sixth class": "class_6",
    "special class": "special_class",
}

YEAR_GROUPS = ["jc1", "jc2", "jc3", "ty", "lc1", "lc2"]
_YEAR_GROUP_PROGRAMMES = [
    "junior certificate",
    "junior certificate",
    "junior certificate",
    "transition year",
    "leaving certificate",
    "leaving certificate",
]

FLAG_COLUMNS = ["fee_paying", "island", "gaeltacht", "deis"]
COUNT_COLUMNS = ["female", "male", "total"]
HEADER_SEARCH_ROWS = 12

# Spelling errors in the Department's values, by column.
VALUE_FIXES = {"school_type": {"Oridinary": "Ordinary"}}

# Words that stay in lower case inside a title-case value.
_MINOR_WORDS = {"of", "and"}


def normalise_ethos(series: pd.Series) -> pd.Series:
    """Give ethos values one capitalisation, for example "Church of Ireland".

    The post-primary lists use capitals ("CATHOLIC") and the primary
    lists use title case ("Church Of Ireland").
    """

    def title(value: str) -> str:
        words = value.title().split(" ")
        return " ".join(
            w.lower() if i and w.lower() in _MINOR_WORDS else w
            for i, w in enumerate(words)
        )

    return series.map(title, na_action="ignore").astype("string")


def _normalise_header(value: object) -> str:
    return " ".join(str(value).split()).strip().lower()


def map_header(value: object) -> str | None:
    """Return the column name for a raw header, or None to discard it."""
    header = _normalise_header(value)
    if header in HEADER_MAP:
        return HEADER_MAP[header]
    if TOTAL_PATTERN.match(header):
        return "total"
    return None


def _find_header_row(raw: pd.DataFrame) -> int | None:
    for i in range(min(HEADER_SEARCH_ROWS, len(raw))):
        if any(map_header(v) == "roll_number" for v in raw.iloc[i]):
            return i
    return None


def _school_list_sheet(path: Path) -> tuple[str, int]:
    """Return the name and header row of the sheet that holds the list."""
    workbook = pd.ExcelFile(path, engine="calamine")
    for sheet in workbook.sheet_names:
        if _normalise_header(sheet) in {"explanatory note", "programme & year"}:
            continue
        raw = pd.read_excel(
            workbook, sheet_name=sheet, header=None, nrows=HEADER_SEARCH_ROWS
        )
        row = _find_header_row(raw)
        if row is not None:
            return str(sheet), row
    raise ValueError(f"{path}: no sheet has a 'Roll Number' header")


def _clean_roll_number(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.upper()


def _clean_flag(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip().str.upper()
    return values.map({"Y": True, "N": False}).astype("boolean")


def _primary_sheets(path: Path) -> list[tuple[str, int, bool]]:
    """Return name, header row and special-school flag of each list sheet."""
    workbook = pd.ExcelFile(path, engine="calamine")
    found = []
    for sheet in workbook.sheet_names:
        name = _normalise_header(sheet)
        if "standard" in name:
            continue
        if name.startswith("mainstream"):
            special = False
        elif name.startswith("special"):
            special = True
        else:
            continue
        raw = pd.read_excel(
            workbook, sheet_name=sheet, header=None, nrows=HEADER_SEARCH_ROWS
        )
        row = _find_header_row(raw)
        if row is None:
            raise ValueError(f"{path}: sheet {sheet!r} has no 'Roll Number' header")
        found.append((str(sheet), row, special))
    if [special for _, _, special in found] != [False, True]:
        raise ValueError(f"{path}: expected one mainstream and one special sheet")
    return found


def read_school_list(path: Path, academic_year: int) -> pd.DataFrame:
    """Read one year's post-primary school list.

    The result has one row for each roll number. Enrolment counts are
    integers; a missing female or male count is zero when the other
    count is present.
    """
    sheet, header_row = _school_list_sheet(path)
    return _read_sheet(path, sheet, header_row, academic_year)


def read_primary_list(path: Path, academic_year: int) -> pd.DataFrame:
    """Read one year's primary school lists, mainstream and special.

    The column special_school is True for schools on the special list.
    """
    frames = []
    for sheet, header_row, special in _primary_sheets(path):
        df = _read_sheet(path, sheet, header_row, academic_year)
        df["special_school"] = special
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    if df["roll_number"].duplicated().any():
        dupes = df.loc[df["roll_number"].duplicated(), "roll_number"].tolist()
        raise ValueError(f"{path}: roll numbers on both lists {dupes}")
    return df


def _read_sheet(
    path: Path, sheet: str, header_row: int, academic_year: int
) -> pd.DataFrame:
    raw = pd.read_excel(
        path, sheet_name=sheet, header=header_row, dtype=object, engine="calamine"
    )

    columns: dict[str, str] = {}
    for header in raw.columns:
        name = map_header(header)
        if name is not None and name not in columns.values():
            columns[header] = name
    df = raw[list(columns)].rename(columns=columns)

    df["roll_number"] = _clean_roll_number(df["roll_number"])
    df = df[df["roll_number"].str.fullmatch(r"\d{5}[A-Z]", na=False)].copy()
    df["academic_year"] = academic_year

    for column in FLAG_COLUMNS:
        if column in df:
            df[column] = _clean_flag(df[column])

    for column in COUNT_COLUMNS:
        if column in df:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    if "female" in df and "male" in df:
        either = df["female"].notna() | df["male"].notna()
        df.loc[either, ["female", "male"]] = df.loc[either, ["female", "male"]].fillna(
            0
        )
        computed = df["female"] + df["male"]
        df["total"] = df["total"].fillna(computed) if "total" in df else computed
    for column in COUNT_COLUMNS:
        if column in df:
            df[column] = df[column].astype("Int64")

    for column in ("latitude", "longitude"):
        if column in df:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    text = df.columns.difference(
        ["academic_year", *FLAG_COLUMNS, *COUNT_COLUMNS, "latitude", "longitude"]
    )
    for column in text:
        df[column] = df[column].astype("string").str.strip()
    for column, fixes in VALUE_FIXES.items():
        if column in df:
            df[column] = df[column].replace(fixes)
    if "ethos" in df:
        df["ethos"] = normalise_ethos(df["ethos"])

    if df["roll_number"].duplicated().any():
        dupes = df.loc[df["roll_number"].duplicated(), "roll_number"].tolist()
        raise ValueError(f"{path}: duplicate roll numbers {dupes}")
    return df.reset_index(drop=True)


def read_year_groups(path: Path) -> pd.DataFrame | None:
    """Read enrolment by year group from the 'Programme & Year' sheet.

    Return None if the workbook has no such sheet.
    """
    workbook = pd.ExcelFile(path, engine="calamine")
    if "Programme & Year" not in workbook.sheet_names:
        return None
    raw = pd.read_excel(workbook, sheet_name="Programme & Year", header=None)
    header_row = _find_header_row(raw)
    if header_row is None or header_row == 0:
        raise ValueError(f"{path}: cannot find the year-group header")

    programmes = raw.iloc[header_row - 1].map(_normalise_header)
    positions = [i for i, p in enumerate(programmes) if p.endswith("certificate")]
    positions += [i for i, p in enumerate(programmes) if p == "transition year"]
    positions += [
        i for i, p in enumerate(programmes) if p.startswith("leaving certificate (")
    ]
    positions.sort()
    found = [programmes.iloc[i].split(" (")[0] for i in positions]
    if found != _YEAR_GROUP_PROGRAMMES:
        raise ValueError(f"{path}: unexpected year-group headers {found}")

    roll_col = next(
        i for i, v in enumerate(raw.iloc[header_row]) if map_header(v) == "roll_number"
    )
    body = raw.iloc[header_row + 1 :]
    df = pd.DataFrame({"roll_number": _clean_roll_number(body.iloc[:, roll_col])})
    for name, position in zip(YEAR_GROUPS, positions, strict=True):
        df[name] = pd.to_numeric(body.iloc[:, position], errors="coerce").astype(
            "Int64"
        )
    df = df[df["roll_number"].str.fullmatch(r"\d{5}[A-Z]", na=False)]
    return df.reset_index(drop=True)


def read_class_groups(path: Path) -> pd.DataFrame | None:
    """Read mainstream enrolment by class from the 'by Standard' sheet.

    Return None if the workbook has no such sheet.
    """
    workbook = pd.ExcelFile(path, engine="calamine")
    sheets = [s for s in workbook.sheet_names if "standard" in _normalise_header(s)]
    if not sheets:
        return None
    raw = pd.read_excel(workbook, sheet_name=sheets[0], header=None)
    header_row = _find_header_row(raw)
    if header_row is None:
        raise ValueError(f"{path}: cannot find the class header")
    headers = [_normalise_header(v) for v in raw.iloc[header_row]]
    roll_col = next(
        i for i, v in enumerate(raw.iloc[header_row]) if map_header(v) == "roll_number"
    )
    body = raw.iloc[header_row + 1 :]
    df = pd.DataFrame({"roll_number": _clean_roll_number(body.iloc[:, roll_col])})
    for header, name in CLASS_GROUPS.items():
        if header in headers:
            values = body.iloc[:, headers.index(header)]
            df[name] = pd.to_numeric(values, errors="coerce").astype("Int64")
    df = df[df["roll_number"].str.fullmatch(r"\d{5}[A-Z]", na=False)]
    return df.reset_index(drop=True)


def drop_personal_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in df.columns if c in PERSONAL_COLUMNS])
