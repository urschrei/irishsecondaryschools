"""Build the published datasets."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from irish_schools import dept
from irish_schools.sources import ROOT, Source, load_manifest

OUTPUT_DIR = ROOT / "data"
WGS84 = "EPSG:4326"

# Column order for the point dataset. Columns that a year does not have
# are left out.
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
    "school_type",
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
    *dept.YEAR_GROUPS,
    "latitude",
    "longitude",
]


def post_primary_sources() -> list[Source]:
    lists = [s for s in load_manifest() if s.kind == "post_primary_list"]
    return sorted(lists, key=lambda s: s.academic_year or 0)


def read_year(source: Source) -> pd.DataFrame:
    """Read one year's list, with year groups, without contact columns."""
    assert source.academic_year is not None
    df = dept.drop_contact_columns(
        dept.read_school_list(source.path(), source.academic_year)
    )
    groups = dept.read_year_groups(source.path())
    if groups is not None:
        df = df.merge(groups, on="roll_number", how="left", validate="one_to_one")
    return df


def build_points(source: Source) -> gpd.GeoDataFrame:
    df = read_year(source)
    if df[["latitude", "longitude"]].isna().any().any():
        missing = df.loc[df["latitude"].isna(), "roll_number"].tolist()
        raise ValueError(f"{source.id}: schools without coordinates: {missing}")
    df = df[[c for c in POINT_COLUMNS if c in df.columns]]
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs=WGS84,
    )


def write_points(gdf: gpd.GeoDataFrame, stem: str, directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = [
        directory / f"{stem}.parquet",
        directory / f"{stem}.geojson",
        directory / f"{stem}.csv",
    ]
    gdf = gpd.GeoDataFrame(gdf.sort_values("roll_number").reset_index(drop=True))
    gdf.to_parquet(paths[0], index=False)
    gdf.to_file(paths[1], driver="GeoJSON", write_bbox="NO", coordinate_precision=6)
    gdf.drop(columns="geometry").to_csv(paths[2], index=False)
    return paths


def build_all(directory: Path = OUTPUT_DIR) -> list[Path]:
    latest = post_primary_sources()[-1]
    points = build_points(latest)
    return write_points(points, "post_primary_schools", directory)
