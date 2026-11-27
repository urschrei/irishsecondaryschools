"""Read Department of Education post-primary school lists.

The Department changes sheet names, header rows and column names from
year to year. This module finds the school list in each workbook and
gives it one schema.
"""

import re
from pathlib import Path

import pandas as pd

# Columns that identify people or give contact details. The build never
# writes them.
CONTACT_COLUMNS = {"principal_name", "email", "phone"}

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
}

# Headers that carry the year in their text, such as "Total 2025-2026",
# "TOTAL (2019-20)" or "Count Unique Enrolments - <=30th Sept".
TOTAL_PATTERN = re.compile(r"^(total\b.*\d{4}|count unique enrolments)")

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
        if any(_normalise_header(v) == "roll number" for v in raw.iloc[i]):
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


def read_school_list(path: Path, academic_year: int) -> pd.DataFrame:
    """Read one year's post-primary school list.

    The result has one row for each roll number. Enrolment counts are
    integers; a missing female or male count is zero when the other
    count is present.
    """
    sheet, header_row = _school_list_sheet(path)
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
        i
        for i, v in enumerate(raw.iloc[header_row])
        if _normalise_header(v) == "roll number"
    )
    body = raw.iloc[header_row + 1 :]
    df = pd.DataFrame({"roll_number": _clean_roll_number(body.iloc[:, roll_col])})
    for name, position in zip(YEAR_GROUPS, positions, strict=True):
        df[name] = pd.to_numeric(body.iloc[:, position], errors="coerce").astype(
            "Int64"
        )
    df = df[df["roll_number"].str.fullmatch(r"\d{5}[A-Z]", na=False)]
    return df.reset_index(drop=True)


def drop_contact_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in df.columns if c in CONTACT_COLUMNS])
