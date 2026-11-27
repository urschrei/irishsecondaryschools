"""Write the data files for the web viewer in site/."""

import hashlib
import json
import math
import shutil
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from irish_schools import enrich, phone
from irish_schools.build import LEVELS, OUTPUT_DIR, Level, school_year
from irish_schools.sources import ROOT, source_by_kind

SITE_PUBLIC = ROOT / "site" / "public"

# Columns that the viewer does not show or filter on.
OMIT_COLUMNS = {
    "academic_year",
    "latitude",
    "longitude",
    "small_area",
    "ed_id",
    "hp_absolute_index",
}

# Decimal places for coordinates: 5 places is approximately 1 m.
COORDINATE_PRECISION = 5

DOWNLOAD_SUFFIXES = {".geojson", ".parquet"}

# Douglas-Peucker tolerance for the ED boundaries, in metres, and the
# decimal places of their coordinates (4 places is approximately 10 m).
ED_TOLERANCE_M = 50
ED_COORDINATE_PRECISION = 4


def _clean(value: object) -> object:
    """Return a JSON value, or None for a missing value."""
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def school_features(level: Level, points: gpd.GeoDataFrame, panel: pd.DataFrame):
    """Return a GeoJSON feature for each school, without empty properties."""
    first_listed = panel.groupby("roll_number")["academic_year"].min()
    columns = [c for c in points.columns if c not in OMIT_COLUMNS | {"geometry"}]
    features = []
    for values in points.to_dict("records"):
        properties = {"level": level.stem}
        for column in columns:
            value = _clean(values[column])
            if value is not None:
                properties[column] = value
        if "phone" in properties:
            properties["phone_display"] = phone.national_format(
                str(properties["phone"])
            )
        properties["first_listed"] = int(first_listed[values["roll_number"]])
        geom = values["geometry"]
        geometry = None
        if geom is not None and not geom.is_empty:
            geometry = {
                "type": "Point",
                "coordinates": [
                    round(geom.x, COORDINATE_PRECISION),
                    round(geom.y, COORDINATE_PRECISION),
                ],
            }
        features.append(
            {"type": "Feature", "geometry": geometry, "properties": properties}
        )
    return features


def enrolment_series(
    panel: pd.DataFrame, rolls: pd.Series, years: list[int]
) -> dict[str, list[object]]:
    """Return total enrolment for each roll number and year.

    A year in which the school was not listed has the value None.
    """
    wide = (
        panel[panel["roll_number"].isin(rolls)]
        .pivot(index="roll_number", columns="academic_year", values="total")
        .reindex(columns=years)
    )
    return {
        str(roll): [_clean(v) for v in values]
        for roll, values in zip(wide.index, wide.to_numpy().tolist(), strict=True)
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_downloads(source: Path, directory: Path) -> list[dict[str, object]]:
    """Copy the published datasets and return their names, sizes and checksums."""
    directory.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for path in sorted(source.iterdir()):
        if path.suffix not in DOWNLOAD_SUFFIXES:
            continue
        shutil.copyfile(path, directory / path.name)
        manifest.append(
            {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        )
    return manifest


def _write_json(data: object, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    return path


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


def write_deprivation_layer(path: Path) -> Path:
    small_areas = enrich.read_small_areas(source_by_kind("small_areas").path())
    deprivation = enrich.read_deprivation(source_by_kind("deprivation").path())
    eds = deprivation_layer(small_areas, deprivation)
    path.parent.mkdir(parents=True, exist_ok=True)
    eds.to_file(
        path,
        driver="GeoJSON",
        write_bbox="NO",
        coordinate_precision=ED_COORDINATE_PRECISION,
    )
    return path


def build_site_data(
    source: Path = OUTPUT_DIR, public: Path = SITE_PUBLIC
) -> list[Path]:
    """Write the viewer data to public/data and the downloads to public/downloads."""
    loaded = []
    for level in LEVELS:
        points_path = source / f"{level.stem}_schools.parquet"
        if points_path.exists():
            panel = pd.read_parquet(source / f"{level.stem}_enrolment.parquet")
            loaded.append((level, gpd.read_parquet(points_path), panel))
    if not loaded:
        raise FileNotFoundError(f"no datasets in {source}: run `schools build`")

    years = sorted({int(y) for _, _, p in loaded for y in p["academic_year"]})
    features = []
    enrolment: dict[str, list[object]] = {}
    for level, points, panel in loaded:
        features += school_features(level, points, panel)
        enrolment |= enrolment_series(panel, points["roll_number"], years)
    current_year = int(loaded[0][1]["academic_year"].iloc[0])
    plc_until = next(
        (lv.last_year_with_plc for lv, _, _ in loaded if lv.last_year_with_plc),
        None,
    )

    data = public / "data"
    meta = {
        "school_year": school_year(current_year),
        "years": years,
        "post_primary_plc_until": plc_until,
        "downloads": copy_downloads(source, public / "downloads"),
    }
    return [
        _write_json(
            {"type": "FeatureCollection", "features": features},
            data / "schools.geojson",
        ),
        _write_json({"years": years, "schools": enrolment}, data / "enrolment.json"),
        _write_json(meta, data / "meta.json"),
        write_deprivation_layer(data / "ed_deprivation.geojson"),
    ]
