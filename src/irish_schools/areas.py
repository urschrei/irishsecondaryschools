"""Write the Electoral Division deprivation layer for the web viewer."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from irish_schools import enrich
from irish_schools.sources import ROOT

# The layer is built from the source files, which CI does not download,
# so `schools build` writes it to a tracked path in the site.
AREAS_PATH = ROOT / "site" / "public" / "areas" / "ed_deprivation.geojson"

# Douglas-Peucker tolerance for the ED boundaries, in metres, and the
# decimal places of their coordinates (4 places is approximately 10 m).
ED_TOLERANCE_M = 50
ED_COORDINATE_PRECISION = 4


def deprivation_layer(
    small_areas: gpd.GeoDataFrame, deprivation: pd.DataFrame
) -> gpd.GeoDataFrame:
    """Return ED boundaries with the Pobal HP Deprivation Index 2022.

    The EDs are the union of their Small Areas, so they match the areas
    that the school files use.
    """
    keyed = small_areas.assign(ed_key=enrich.ed_key(small_areas["ed_id"]))
    eds = keyed.dissolve(by="ed_key", as_index=False)[["ed_key", "ed_name", "geometry"]]
    eds["geometry"] = eds.simplify(ED_TOLERANCE_M, preserve_topology=True)
    eds = eds.merge(deprivation, on="ed_key", how="left", validate="one_to_one")
    unscored = eds.loc[eds["hp_relative_index"].isna(), "ed_key"].tolist()
    if unscored:
        raise ValueError(f"no deprivation score for EDs {unscored}")
    columns = ["ed_name", "hp_relative_index", "hp_category", "geometry"]
    return gpd.GeoDataFrame(eds[columns]).to_crs(4326)


def write_deprivation_layer(
    small_areas: gpd.GeoDataFrame, deprivation: pd.DataFrame, path: Path = AREAS_PATH
) -> Path:
    eds = deprivation_layer(small_areas, deprivation)
    path.parent.mkdir(parents=True, exist_ok=True)
    eds.to_file(
        path,
        driver="GeoJSON",
        write_bbox="NO",
        coordinate_precision=ED_COORDINATE_PRECISION,
    )
    return path
