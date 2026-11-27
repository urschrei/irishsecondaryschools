import pandas as pd

from irish_schools.enrich import ed_key


def test_ed_key_strips_leading_zeros():
    ids = pd.Series(["057103", "57103", "047235/04702719", "47235/4702719"])
    keys = ed_key(ids).tolist()
    assert keys[0] == keys[1] == "57103"
    assert keys[2] == keys[3] == "47235/4702719"
