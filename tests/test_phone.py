import pandas as pd
import pytest

from irish_schools.phone import normalise_phone, normalise_phones


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("018411594", "+35318411594"),
        ("01 2801522", "+35312801522"),
        ("021-4631973", "+353214631973"),
        ("063 81877", "+3536381877"),
        ("0871234567", "+353871234567"),
        ("749737366", "+353749737366"),
        ("35312861649", "+35312861649"),
        ("01 6272166/6272200", "+35316272166;+35316272200"),
        ("01 6272166/01 6272166", "+35316272166"),
    ],
)
def test_normalise_phone(value, expected):
    assert normalise_phone(value) == expected


@pytest.mark.parametrize("value", ["123", "not a number", "01 234"])
def test_normalise_phone_rejects_invalid(value):
    assert normalise_phone(value) is None


def test_normalise_phones_reports_invalid():
    values = pd.Series(["018411594", None, "123"], dtype="string")
    normalised, invalid = normalise_phones(values)
    assert normalised.tolist()[0] == "+35318411594"
    assert normalised.isna().tolist() == [False, True, True]
    assert invalid == ["123"]
