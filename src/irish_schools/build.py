"""Build the published datasets."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd

from irish_schools import dept, enrich
from irish_schools.sources import ROOT, Source, load_manifest, source_by_kind

OUTPUT_DIR = ROOT / "data"
WGS84 = "EPSG:4326"
CHANGE_YEARS = 5

# Column order for the point datasets. Columns that a level or year does
# not have are left out.
POINT_COLUMNS = [
    "roll_number",
    "academic_year",
    "name",
    "address_1",
    "address_2",
    "address_3",
    "address_4",
    "eircode",
    "county",
    "local_authority",
    "planning_area",
    "special_school",
    "school_type",
    "school_level",
    "ethos",
    "patron",
    "gender",
    "attendance_type",
    "irish_classification",
    "fee_paying",
    "deis",
    "gaeltacht",
    "island",
    "female",
    "male",
    "total",
    *dept.CLASS_GROUPS.values(),
    *dept.YEAR_GROUPS,
    "latitude",
    "longitude",
]


@dataclass(frozen=True)
class Level:
    """How to read and publish one level of school."""

    kind: str
    stem: str
    read_list: Callable[[Path, int], pd.DataFrame]
    read_groups: Callable[[Path], pd.DataFrame | None]
    groups: list[str]
    # Last year whose lists include further-education colleges and
    # Post-Leaving Certificate enrolments, if any.
    last_year_with_plc: int | None = None

    def sources(self) -> list[Source]:
        lists = [s for s in load_manifest() if s.kind == self.kind]
        return sorted(lists, key=lambda s: s.academic_year or 0)

    def panel_columns(self) -> list[str]:
        columns = ["roll_number", "academic_year", "school_year", "name"]
        if self is PRIMARY:
            columns.append("special_school")
        columns += ["female", "male", "total", *self.groups]
        if self.last_year_with_plc is not None:
            columns.append("includes_plc")
        return columns


POST_PRIMARY = Level(
    kind="post_primary_list",
    stem="post_primary",
    read_list=dept.read_school_list,
    read_groups=dept.read_year_groups,
    groups=dept.YEAR_GROUPS,
    last_year_with_plc=2015,
)

PRIMARY = Level(
    kind="primary_list",
    stem="primary",
    read_list=dept.read_primary_list,
    read_groups=dept.read_class_groups,
    groups=list(dept.CLASS_GROUPS.values()),
)

LEVELS = [POST_PRIMARY, PRIMARY]


def read_year(level: Level, source: Source) -> pd.DataFrame:
    """Read one year's list, with enrolment groups, without contact columns."""
    assert source.academic_year is not None
    df = level.read_list(source.path(), source.academic_year)
    df = dept.drop_contact_columns(df)
    groups = level.read_groups(source.path())
    if groups is not None:
        df = df.merge(groups, on="roll_number", how="left", validate="one_to_one")
    return df


def school_year(academic_year: int) -> str:
    return f"{academic_year}/{(academic_year + 1) % 100:02d}"


def build_panel(level: Level, frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Return enrolment for each school and year, one row for each pair."""
    df = pd.concat(frames, ignore_index=True)
    df["school_year"] = df["academic_year"].map(school_year)
    if level.last_year_with_plc is not None:
        df["includes_plc"] = df["academic_year"] <= level.last_year_with_plc
    for column in level.groups:
        if column not in df:
            df[column] = pd.NA
        df[column] = df[column].astype("Int64")
    df = df[level.panel_columns()].sort_values(["roll_number", "academic_year"])
    return df.reset_index(drop=True)


def add_enrolment_change(points: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    """Add total enrolment five years earlier and the percentage change."""
    year = int(points["academic_year"].iloc[0])
    earlier = panel.loc[
        panel["academic_year"] == year - CHANGE_YEARS, ["roll_number", "total"]
    ].rename(columns={"total": "total_5y_earlier"})
    out = points.merge(earlier, on="roll_number", how="left", validate="one_to_one")
    change = (out["total"] - out["total_5y_earlier"]) / out["total_5y_earlier"] * 100
    out["change_5y_pct"] = change.astype("Float64").round(1)
    return out


def to_points(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Make points from latitude and longitude.

    A school without coordinates has an empty geometry.
    """
    df = df[[c for c in POINT_COLUMNS if c in df.columns]]
    located = df["latitude"].notna() & df["longitude"].notna()
    geometry = gpd.GeoSeries([None] * len(df), index=df.index, crs=WGS84)
    geometry[located] = gpd.points_from_xy(
        df.loc[located, "longitude"], df.loc[located, "latitude"], crs=WGS84
    )
    return gpd.GeoDataFrame(df, geometry=geometry, crs=WGS84)


def write_points(gdf: gpd.GeoDataFrame, stem: str, directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = [directory / f"{stem}.parquet", directory / f"{stem}.geojson"]
    columns = [c for c in gdf.columns if c != "geometry"] + ["geometry"]
    gdf = gpd.GeoDataFrame(
        gdf[columns].sort_values("roll_number").reset_index(drop=True)
    )
    gdf.to_parquet(paths[0], index=False)
    gdf.to_file(paths[1], driver="GeoJSON", write_bbox="NO", coordinate_precision=6)
    return paths


def write_panel(panel: pd.DataFrame, stem: str, directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{stem}.parquet"
    panel.to_parquet(path, index=False)
    return [path]


def build_level(
    level: Level,
    small_areas: gpd.GeoDataFrame,
    deprivation: pd.DataFrame,
    directory: Path,
) -> list[Path]:
    sources = level.sources()
    frames = [read_year(level, s) for s in sources]
    panel = build_panel(level, frames)

    points = to_points(frames[-1])
    points = gpd.GeoDataFrame(add_enrolment_change(points, panel))
    points = enrich.add_small_areas(points, small_areas)
    points = gpd.GeoDataFrame(enrich.add_deprivation(points, deprivation))
    candidates = ~points["special_school"] if "special_school" in points else None
    points = enrich.add_access(points, candidates)

    unlocated = points.loc[points.geometry.isna(), "roll_number"].tolist()
    if unlocated:
        print(f"{level.stem}: schools without coordinates: {unlocated}")
    return [
        *write_points(points, f"{level.stem}_schools", directory),
        *write_panel(panel, f"{level.stem}_enrolment", directory),
    ]


def build_all(directory: Path = OUTPUT_DIR) -> list[Path]:
    small_areas = enrich.read_small_areas(source_by_kind("small_areas").path())
    deprivation = enrich.read_deprivation(source_by_kind("deprivation").path())
    paths = []
    for level in LEVELS:
        if level.sources():
            paths += build_level(level, small_areas, deprivation, directory)
    return paths
