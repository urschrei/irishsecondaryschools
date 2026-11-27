"""Add area attributes to school points."""

from pathlib import Path

import geopandas as gpd
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
        .map(lambda parts: "/".join(p.strip().lstrip("0") for p in parts))
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
    identifier.
    """
    joined = gpd.sjoin(
        points.to_crs(ITM), small_areas, predicate="within", how="left"
    ).drop(columns="index_right")
    joined = joined.sort_values("small_area")
    joined = joined[~joined.index.duplicated(keep="first")].sort_index()
    if joined["small_area"].isna().any():
        missing = joined.loc[joined["small_area"].isna(), "roll_number"].tolist()
        raise ValueError(f"schools outside all Small Areas: {missing}")
    return gpd.GeoDataFrame(joined.to_crs(points.crs))


def add_deprivation(points: pd.DataFrame, deprivation: pd.DataFrame) -> pd.DataFrame:
    """Add the Pobal HP Deprivation Index 2022 of the school's ED."""
    keyed = points.assign(ed_key=ed_key(points["ed_id"]))
    out = keyed.merge(deprivation, on="ed_key", how="left", validate="many_to_one")
    if out["hp_relative_index"].isna().any():
        missing = out.loc[out["hp_relative_index"].isna(), "ed_id"].unique()
        raise ValueError(f"no deprivation score for EDs {list(missing)}")
    return out.drop(columns="ed_key")
