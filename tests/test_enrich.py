import math

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point

from irish_schools.enrich import (
    EARTH_RADIUS_KM,
    ITM,
    WGS84,
    add_access,
    ed_key,
    great_circle_km,
)

# Points on the meridian at 7 degrees west, given as kilometres north of
# 53 degrees north. On a meridian, great-circle distance is the arc length.
LON = -7.0


def north(km):
    return 53.0 + math.degrees(km / EARTH_RADIUS_KM)


def test_ed_key_strips_leading_zeros():
    ids = pd.Series(["057103", "57103", "047235/04702719", "47235/4702719"])
    keys = ed_key(ids).tolist()
    assert keys[0] == keys[1] == "57103"
    assert keys[2] == keys[3] == "47235/4702719"
    assert ed_key(pd.Series([None], dtype="string")).isna().all()


def make_points(roll_numbers, kilometres):
    return gpd.GeoDataFrame(
        {"roll_number": roll_numbers},
        geometry=[Point(LON, north(km)) for km in kilometres],
        crs=WGS84,
    )


def test_great_circle_km():
    dublin = np.radians([-6.2603, 53.3498])
    galway = np.radians([-9.0568, 53.2707])
    km = great_circle_km(dublin[0], dublin[1], galway[0], galway[1])
    assert km == pytest.approx(186.0, abs=0.05)
    assert great_circle_km(dublin[0], dublin[1], dublin[0], dublin[1]) == 0


def test_add_access():
    points = make_points(["A", "B", "C"], [0, 1, 20])
    out = add_access(points)
    assert out["nearest_school"].tolist() == ["B", "A", "B"]
    assert out["nearest_school_km"].tolist() == [1.0, 1.0, 19.0]
    assert out["schools_within_5km"].tolist() == [1, 1, 0]


def test_add_access_reads_projected_points():
    points = make_points(["A", "B", "C"], [0, 1, 20]).to_crs(ITM)
    out = add_access(points)
    assert out["nearest_school_km"].tolist() == [1.0, 1.0, 19.0]
    assert out.crs == points.crs


def test_add_access_with_shared_coordinates():
    points = make_points(["A", "B", "C"], [0, 0, 3])
    out = add_access(points)
    assert out["nearest_school"].tolist() == ["B", "A", "A"]
    assert out["nearest_school_km"].tolist() == [0.0, 0.0, 3.0]
    assert out["schools_within_5km"].tolist() == [2, 2, 2]


def test_add_access_skips_unlocated_and_non_candidates():
    points = make_points(["A", "B", "C"], [0, 0.5, 2])
    points.loc[2, "geometry"] = None
    candidates = pd.Series([True, False, True])
    out = add_access(points, candidates)
    # B is not a candidate and C has no location, so A has no nearest
    # school. C has no location, so it has no measures.
    assert out["nearest_school"].isna().tolist() == [True, False, True]
    assert out.loc[1, "nearest_school"] == "A"
    assert out.loc[1, "nearest_school_km"] == 0.5
    assert out["schools_within_5km"].tolist()[:2] == [0, 1]
