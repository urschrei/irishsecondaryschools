import pandas as pd

from irish_schools.build import apply_spellings, review_names
from irish_schools.names import Spellings


def frame(year, rows):
    return pd.DataFrame(
        {
            "roll_number": [roll for roll, _ in rows],
            "academic_year": year,
            "name": pd.Series([name for _, name in rows], dtype="string"),
        }
    )


def test_apply_spellings():
    spellings = Spellings(
        words={"padraig": "Pádraig"},
        schools={"00002B": "S N Ráth Mór"},
    )
    frames = [
        frame(2024, [("00001A", "S N Padraig"), ("00002B", "S N Rath Mor")]),
        frame(2025, [("00001A", "S N Padraig"), ("00002B", "S N Rath Mor")]),
        frame(2026, [("00002B", "S N Rath Mor"), ("00003C", "Rath N S")]),
    ]
    frames[0].loc[1, "name"] = "Rath Mor N S"
    out = apply_spellings(frames, spellings)

    assert out[1]["name"].tolist() == ["S N Pádraig", "S N Ráth Mór"]
    # The override applies only in years with the current name.
    assert out[0]["name"].tolist() == ["S N Pádraig", "Rath Mor N S"]
    assert out[2]["name"].tolist() == ["S N Ráth Mór", "Rath N S"]


def test_review_names():
    spellings = Spellings(suspects={"rath": "Ráth"}, schools={"00002B": "S N Rath"})
    schools = frame(2025, [("00001A", "S N Rath Mor"), ("00002B", "S N Rath")])
    out = review_names(schools, schools["name"], spellings)
    assert out.to_dict("records") == [
        {
            "roll_number": "00001A",
            "name": "S N Rath Mor",
            "kind": "spelling",
            "text": "Rath",
            "suggestion": "Ráth",
        }
    ]
