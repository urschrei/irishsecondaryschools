"""Add area attributes to school points."""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

# Irish Transverse Mercator. Distances in this CRS are in metres.
ITM = "EPSG:2157"

SMALL_AREA_COLUMNS = {
    "SA_GEOGID_2022": "small_area",
    "SA_URBAN_AREA_FLAG": "urban",
    "SA_URBAN_AREA_NAME": "urban_area",
    "ED_ID_STR": "ed_id",
    "ED_ENGLISH": "ed_name",
}

DEPRIVATION_COLUMNS = {
    "Index22_ED_std_rel_wt": "hp_relative_index",
    "Index22_ED_std_abs_wt": "hp_absolute_index",
    "Index22_ED_rel_wt_lab": "hp_category",
}


def read_small_areas(path: Path) -> gpd.GeoDataFrame:
    sa = gpd.read_file(path, columns=list(SMALL_AREA_COLUMNS))
    sa = sa.rename(columns=SMALL_AREA_COLUMNS).to_crs(ITM)
    sa["urban"] = sa["urban"].astype(bool)
    sa.loc[~sa["urban"], "urban_area"] = None
    return gpd.GeoDataFrame(sa.drop(columns="urban"))


def ed_key(ids: pd.Series) -> pd.Series:
    """Return an Electoral Division key without leading zeros.

    The Pobal file stores ED identifiers as numbers, which removes the
    leading zero that the CSO identifiers have. Some identifiers join
    several EDs with "/".
    """
    return (
        ids.astype("string")
        .str.split("/")
        .map(
            lambda parts: "/".join(p.strip().lstrip("0") for p in parts),
            na_action="ignore",
        )
        .astype("string")
    )


def read_deprivation(path: Path) -> pd.DataFrame:
    hp = pd.read_csv(path, dtype={"ED_ID_STR": str}, encoding="cp1252")
    hp["ed_key"] = ed_key(hp["ED_ID_STR"])
    if not hp["ed_key"].is_unique:
        raise ValueError(f"{path}: duplicate Electoral Division identifiers")
    return hp[["ed_key", *DEPRIVATION_COLUMNS]].rename(columns=DEPRIVATION_COLUMNS)


def add_small_areas(
    points: gpd.GeoDataFrame, small_areas: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Add the 2022 Small Area, urban area and ED that contain each point.

    A point on a shared boundary takes the Small Area with the lowest
    identifier. Points without geometry get empty values.
    """
    joined = gpd.sjoin(
        points.to_crs(ITM), small_areas, predicate="within", how="left"
    ).drop(columns="index_right")
    joined = joined.sort_values("small_area")
    joined = joined[~joined.index.duplicated(keep="first")].sort_index()
    outside = joined["small_area"].isna() & joined.geometry.notna()
    if outside.any():
        missing = joined.loc[outside, "roll_number"].tolist()
        raise ValueError(f"schools outside all Small Areas: {missing}")
    return gpd.GeoDataFrame(joined.to_crs(points.crs))


def add_deprivation(points: pd.DataFrame, deprivation: pd.DataFrame) -> pd.DataFrame:
    """Add the Pobal HP Deprivation Index 2022 of the school's ED."""
    keyed = points.assign(ed_key=ed_key(points["ed_id"]))
    out = keyed.merge(deprivation, on="ed_key", how="left", validate="many_to_one")
    unscored = out["hp_relative_index"].isna() & out["ed_id"].notna()
    if unscored.any():
        missing = out.loc[unscored, "ed_id"].unique()
        raise ValueError(f"no deprivation score for EDs {list(missing)}")
    return out.drop(columns="ed_key")


ACCESS_RADIUS_KM = 5
# Mean radius of the Earth (IUGG), in kilometres. The web viewer uses the
# same value.
EARTH_RADIUS_KM = 6371.0088
WGS84 = "EPSG:4326"
_CHUNK = 512


def great_circle_km(
    lon1: np.ndarray, lat1: np.ndarray, lon2: np.ndarray, lat2: np.ndarray
) -> np.ndarray:
    """Return great-circle distances in kilometres, with the haversine formula.

    The arguments are in radians, and broadcast against each other.
    """
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def add_access(
    points: gpd.GeoDataFrame, candidates: pd.Series | None = None
) -> gpd.GeoDataFrame:
    """Add great-circle access measures between schools.

    nearest_school: roll number of the nearest other candidate school.
    nearest_school_km: distance to that school.
    schools_within_5km: number of other candidate schools within 5 km.

    candidates is a boolean mask of the schools to count. If it is None,
    all schools are candidates. Points without geometry get empty values.
    """
    if candidates is None:
        candidates = pd.Series(True, index=points.index)
    located = points.geometry.notna() & ~points.geometry.is_empty
    targets = points.index[candidates & located]

    lonlat = points.geometry.to_crs(WGS84)
    radians = np.radians(np.column_stack([lonlat.x, lonlat.y]))
    target_pos = points.index.get_indexer(targets)
    target_rad = radians[target_pos]
    target_rolls = points["roll_number"].to_numpy()[target_pos]

    nearest = pd.Series(pd.NA, index=points.index, dtype="string")
    nearest_km = pd.Series(np.nan, index=points.index, dtype="Float64")
    within = pd.Series(pd.NA, index=points.index, dtype="Int64")

    sources = points.index[located] if len(targets) else points.index[:0]
    source_pos = points.index.get_indexer(sources)
    for start in range(0, len(sources), _CHUNK):
        rows = source_pos[start : start + _CHUNK]
        distance = great_circle_km(
            radians[rows, 0][:, None],
            radians[rows, 1][:, None],
            target_rad[None, :, 0],
            target_rad[None, :, 1],
        )
        # Exclude each school by position, not by geometry: some schools
        # share coordinates.
        distance[rows[:, None] == target_pos[None, :]] = np.inf
        index = sources[start : start + _CHUNK]
        within[index] = (distance <= ACCESS_RADIUS_KM).sum(axis=1)
        # A school whose only candidate is itself has no nearest school.
        found = np.isfinite(distance.min(axis=1))
        nearest[index[found]] = target_rolls[distance[found].argmin(axis=1)]
        nearest_km[index[found]] = distance[found].min(axis=1).round(2)

    out = points.copy()
    out["nearest_school"] = nearest
    out["nearest_school_km"] = nearest_km
    out["schools_within_5km"] = within
    return out
