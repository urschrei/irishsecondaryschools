import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from irish_schools.enrich import ITM, add_access, ed_key


def test_ed_key_strips_leading_zeros():
    ids = pd.Series(["057103", "57103", "047235/04702719", "47235/4702719"])
    keys = ed_key(ids).tolist()
    assert keys[0] == keys[1] == "57103"
    assert keys[2] == keys[3] == "47235/4702719"
    assert ed_key(pd.Series([None], dtype="string")).isna().all()


def make_points(roll_numbers, coordinates):
    return gpd.GeoDataFrame(
        {"roll_number": roll_numbers},
        geometry=[Point(x, y) for x, y in coordinates],
        crs=ITM,
    )


def test_add_access():
    points = make_points(
        ["A", "B", "C"], [(700000, 700000), (701000, 700000), (720000, 700000)]
    )
    out = add_access(points)
    assert out["nearest_school"].tolist() == ["B", "A", "B"]
    assert out["nearest_school_km"].tolist() == [1.0, 1.0, 19.0]
    assert out["schools_within_5km"].tolist() == [1, 1, 0]


def test_add_access_with_shared_coordinates():
    points = make_points(
        ["A", "B", "C"], [(700000, 700000), (700000, 700000), (703000, 700000)]
    )
    out = add_access(points)
    assert out["nearest_school"].tolist() == ["B", "A", "A"]
    assert out["nearest_school_km"].tolist() == [0.0, 0.0, 3.0]
    assert out["schools_within_5km"].tolist() == [2, 2, 2]


def test_add_access_skips_unlocated_and_non_candidates():
    points = make_points(
        ["A", "B", "C"], [(700000, 700000), (700500, 700000), (702000, 700000)]
    )
    points.loc[2, "geometry"] = None
    candidates = pd.Series([True, False, True])
    out = add_access(points, candidates)
    # B is not a candidate and C has no location, so A has no nearest
    # school. C has no location, so it has no measures.
    assert out["nearest_school"].isna().tolist() == [True, False, True]
    assert out.loc[1, "nearest_school"] == "A"
    assert out.loc[1, "nearest_school_km"] == 0.5
    assert out["schools_within_5km"].tolist()[:2] == [0, 1]
