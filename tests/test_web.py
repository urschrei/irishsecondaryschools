"""Check the web viewer data written by `schools web`."""

import json

import geopandas as gpd
import pytest

from irish_schools import dept, web
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
