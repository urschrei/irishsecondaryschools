"""Check the published datasets in data/."""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from irish_schools import dept
from irish_schools.build import OUTPUT_DIR

POINTS = OUTPUT_DIR / "post_primary_schools.parquet"
# Republic of Ireland, with a margin for islands.
IRELAND = box(-10.7, 51.3, -5.9, 55.5)

pytestmark = pytest.mark.skipif(not POINTS.exists(), reason="run `schools build`")


@pytest.fixture(scope="module")
def points():
    return gpd.read_parquet(POINTS)


def test_roll_numbers_are_unique(points):
    assert points["roll_number"].is_unique
    assert points["roll_number"].str.fullmatch(r"\d{5}[A-Z]").all()


def test_points_are_in_ireland(points):
    assert points.crs.to_epsg() == 4326
    assert points.within(IRELAND).all()


def test_no_contact_columns(points):
    assert not dept.CONTACT_COLUMNS & set(points.columns)


def test_one_academic_year(points):
    assert points["academic_year"].nunique() == 1


PANEL = OUTPUT_DIR / "post_primary_enrolment.parquet"


@pytest.fixture(scope="module")
def panel():
    return pd.read_parquet(PANEL)


def test_panel_has_one_row_per_school_and_year(panel):
    assert not panel.duplicated(["roll_number", "academic_year"]).any()


def test_panel_counts_add_up(panel):
    assert (panel["female"] + panel["male"] == panel["total"]).all()
    groups = panel.dropna(subset=dept.YEAR_GROUPS)
    assert (groups[dept.YEAR_GROUPS].sum(axis=1) == groups["total"]).all()


def test_panel_flags_plc_years(panel):
    assert panel.loc[panel["includes_plc"], "academic_year"].max() == 2015


def test_points_match_latest_panel_year(points, panel):
    latest = panel[panel["academic_year"] == panel["academic_year"].max()]
    assert set(latest["roll_number"]) == set(points["roll_number"])


def test_every_school_has_area_and_deprivation(points):
    for column in ("small_area", "ed_id", "hp_relative_index", "hp_category"):
        assert points[column].notna().all(), column
