"""Check the published datasets in data/."""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from irish_schools import dept
from irish_schools.build import LEVELS, OUTPUT_DIR, Level

# Republic of Ireland, with a margin for islands.
IRELAND = box(-10.7, 51.3, -5.9, 55.5)


def built(level: Level) -> bool:
    return (OUTPUT_DIR / f"{level.stem}_schools.parquet").exists()


pytestmark = pytest.mark.parametrize(
    "level",
    [
        pytest.param(
            lv, marks=pytest.mark.skipif(not built(lv), reason="run `schools build`")
        )
        for lv in LEVELS
    ],
    ids=lambda lv: lv.stem,
)


def points_of(level: Level) -> gpd.GeoDataFrame:
    return gpd.read_parquet(OUTPUT_DIR / f"{level.stem}_schools.parquet")


def panel_of(level: Level) -> pd.DataFrame:
    return pd.read_parquet(OUTPUT_DIR / f"{level.stem}_enrolment.parquet")


def test_roll_numbers_are_unique(level):
    points = points_of(level)
    assert points["roll_number"].is_unique
    assert points["roll_number"].str.fullmatch(r"\d{5}[A-Z]").all()


def test_points_are_in_ireland(level):
    points = points_of(level)
    located = points[points.geometry.notna()]
    assert points.crs.to_epsg() == 4326
    assert located.within(IRELAND).all()
    # The Department gives coordinates for nearly every school.
    assert len(located) >= len(points) - 5


def test_no_personal_columns(level):
    assert not dept.PERSONAL_COLUMNS & set(points_of(level).columns)


def test_one_academic_year(level):
    assert points_of(level)["academic_year"].nunique() == 1


def test_located_schools_have_area_and_deprivation(level):
    points = points_of(level)
    located = points[points.geometry.notna()]
    for column in ("small_area", "ed_id", "hp_relative_index", "hp_category"):
        assert located[column].notna().all(), column


def test_nearest_school_is_another_listed_school(level):
    points = points_of(level)
    located = points[points.geometry.notna()]
    assert (located["nearest_school"] != located["roll_number"]).all()
    assert located["nearest_school"].isin(points["roll_number"]).all()
    assert (located["nearest_school_km"] >= 0).all()


def test_panel_has_one_row_per_school_and_year(level):
    panel = panel_of(level)
    assert not panel.duplicated(["roll_number", "academic_year"]).any()


def test_panel_counts_add_up(level):
    panel = panel_of(level)
    assert (panel["female"] + panel["male"] == panel["total"]).all()
    groups = panel[panel[level.groups].notna().any(axis=1)]
    assert (groups[level.groups].sum(axis=1) == groups["total"]).all()


def test_points_match_latest_panel_year(level):
    panel = panel_of(level)
    latest = panel[panel["academic_year"] == panel["academic_year"].max()]
    assert set(latest["roll_number"]) == set(points_of(level)["roll_number"])


def test_post_primary_panel_flags_plc_years(level):
    if level.last_year_with_plc is None:
        pytest.skip("no PLC break at this level")
    panel = panel_of(level)
    flagged = panel.loc[panel["includes_plc"], "academic_year"]
    assert flagged.max() == level.last_year_with_plc


def test_phone_numbers_are_e164(level):
    phones = points_of(level)["phone"].dropna()
    assert phones.str.fullmatch(r"\+353\d{7,9}(;\+353\d{7,9})*").all()
