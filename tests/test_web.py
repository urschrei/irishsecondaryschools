"""Check the web viewer data written by `schools web`."""

import json

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from irish_schools import dept, enrich, web
from irish_schools.build import LEVELS, OUTPUT_DIR

pytestmark = pytest.mark.skipif(
    not all((OUTPUT_DIR / f"{lv.stem}_schools.parquet").exists() for lv in LEVELS),
    reason="run `schools build`",
)


@pytest.fixture(scope="module")
def public(tmp_path_factory):
    directory = tmp_path_factory.mktemp("public")
    web.build_site_data(public=directory)
    return directory


def read(public, name):
    return json.loads((public / "data" / name).read_text())


def test_every_school_has_a_feature(public):
    features = read(public, "schools.geojson")["features"]
    expected = sum(
        len(gpd.read_parquet(OUTPUT_DIR / f"{lv.stem}_schools.parquet"))
        for lv in LEVELS
    )
    rolls = [f["properties"]["roll_number"] for f in features]
    assert len(rolls) == expected
    assert len(set(rolls)) == expected


def test_properties_have_no_empty_or_personal_values(public):
    for feature in read(public, "schools.geojson")["features"]:
        properties = feature["properties"]
        assert None not in properties.values()
        assert not dept.PERSONAL_COLUMNS & set(properties)
        assert properties["level"] in {lv.stem for lv in LEVELS}
        assert 2011 <= properties["first_listed"] <= 2025


def test_unlocated_schools_have_null_geometry(public):
    features = read(public, "schools.geojson")["features"]
    unlocated = [f for f in features if f["geometry"] is None]
    assert len(unlocated) <= 5


def test_enrolment_has_one_value_per_year(public):
    enrolment = read(public, "enrolment.json")
    features = read(public, "schools.geojson")["features"]
    assert len(enrolment["schools"]) == len(features)
    for series in enrolment["schools"].values():
        assert len(series) == len(enrolment["years"])
        # Every school in the current list has a value for the current year.
        assert series[-1] is not None


def test_downloads_match_their_checksums(public):
    meta = read(public, "meta.json")
    assert meta["school_year"] == "2025/26"
    assert meta["post_primary_plc_until"] == 2015
    names = {d["file"] for d in meta["downloads"]}
    assert {f"{lv.stem}_schools.geojson" for lv in LEVELS} <= names
    for download in meta["downloads"]:
        path = public / "downloads" / download["file"]
        assert path.stat().st_size == download["bytes"]
        assert web.sha256(path) == download["sha256"]


def test_deprivation_layer_scores_every_ed():
    small_areas = gpd.GeoDataFrame(
        {
            "ed_id": ["01001", "01001", "02002"],
            "ed_name": ["A", "A", "B"],
        },
        geometry=[box(0, 0, 1000, 1000), box(1000, 0, 2000, 1000), box(0, 0, 5, 5)],
        crs=enrich.ITM,
    )
    deprivation = pd.DataFrame(
        {
            "ed_key": ["1001", "2002"],
            "hp_relative_index": [1.5, -12.0],
            "hp_absolute_index": [2.0, -10.0],
            "hp_category": ["Marginally Above Average", "Disadvantaged"],
        }
    )
    eds = web.deprivation_layer(small_areas, deprivation)
    assert eds.crs.to_epsg() == 4326
    assert list(eds["ed_name"]) == ["A", "B"]
    assert eds["hp_category"].notna().all()
    assert "hp_absolute_index" not in eds


def test_deprivation_layer_file(public):
    eds = gpd.read_file(public / "data" / "ed_deprivation.geojson")
    assert len(eds) > 3000
    assert eds["hp_category"].notna().all()
