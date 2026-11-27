"""Check the published datasets in data/."""

import geopandas as gpd
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
