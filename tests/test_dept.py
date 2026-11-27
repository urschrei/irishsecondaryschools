import pandas as pd
import pytest

from irish_schools import dept, sources


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("Roll Number", "roll_number"),
        ("  Ethos/Religion ", "ethos"),
        ("Fee Charging School (Y/N)", "fee_paying"),
        ("Gaeltacht Area\nLocation (Y/N)", "gaeltacht"),
        ("Total 2025-2026", "total"),
        ("TOTAL (2019-20)", "total"),
        ("Count Unique Enrolments - <=30th Sept", "total"),
        ("Total Girls", "female"),
        ("ID", None),
        ("ETB Name", None),
    ],
)
def test_map_header(header, expected):
    assert dept.map_header(header) == expected


def write_workbook(path, rows, header_offset=0, programme=None):
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame([["About this data"]]).to_excel(
            writer, sheet_name="Explanatory Note", header=False, index=False
        )
        pd.DataFrame(rows).to_excel(
            writer,
            sheet_name="School Lists",
            startrow=header_offset,
            index=False,
        )
        if programme is not None:
            programme.to_excel(
                writer, sheet_name="Programme & Year", header=False, index=False
            )


ROWS = [
    {
        "Roll Number": " 60010p ",
        "Official School Name": "Girls School",
        "Principal Name": "MS. A",
        "Email": "a@example.ie",
        "DEIS (Y/N)": "Y",
        "FEMALE": 100,
        "MALE": None,
        "Total 2025-2026": 100,
    },
    {
        "Roll Number": "60020S",
        "Official School Name": "Mixed School",
        "Principal Name": "MR. B",
        "Email": "b@example.ie",
        "DEIS (Y/N)": "N",
        "FEMALE": 10,
        "MALE": 20,
        "Total 2025-2026": None,
    },
    {"Roll Number": None, "Official School Name": "Total"},
]


def test_read_school_list(tmp_path):
    path = tmp_path / "list.xlsx"
    write_workbook(path, ROWS, header_offset=1)
    df = dept.read_school_list(path, 2025)

    assert df["roll_number"].tolist() == ["60010P", "60020S"]
    assert df["academic_year"].tolist() == [2025, 2025]
    assert df["deis"].tolist() == [True, False]
    assert df["male"].tolist() == [0, 20]
    assert df["total"].tolist() == [100, 30]


def test_drop_contact_columns(tmp_path):
    path = tmp_path / "list.xlsx"
    write_workbook(path, ROWS)
    df = dept.drop_contact_columns(dept.read_school_list(path, 2025))
    assert not dept.CONTACT_COLUMNS & set(df.columns)


def test_read_school_list_rejects_duplicates(tmp_path):
    path = tmp_path / "list.xlsx"
    write_workbook(path, [ROWS[1], ROWS[1]])
    with pytest.raises(ValueError, match="duplicate"):
        dept.read_school_list(path, 2025)


def test_read_year_groups(tmp_path):
    programme = pd.DataFrame(
        [
            [None, None, *["JUNIOR CERTIFICATE"] * 3, "TRANSITION YEAR"]
            + ["LEAVING CERTIFICATE", "LEAVING CERTIFICATE (incl. repeats)", None],
            ["Roll Number", "Official School Name"]
            + ["Year 1", "Year 2", "Year 3", "Year 1", "Year 1", "Year 2", "Total"],
            ["60020S", "Mixed School", 1, 2, 3, 4, 5, 6, 21],
        ]
    )
    path = tmp_path / "list.xlsx"
    write_workbook(path, ROWS, programme=programme)
    df = dept.read_year_groups(path)
    assert df is not None
    assert df.iloc[0][dept.YEAR_GROUPS].tolist() == [1, 2, 3, 4, 5, 6]


def downloaded_lists():
    return [
        s
        for s in sources.load_manifest()
        if s.kind == "post_primary_list" and s.path().exists()
    ]


@pytest.mark.parametrize("source", downloaded_lists(), ids=lambda s: s.id)
def test_downloaded_list_is_consistent(source):
    df = dept.read_school_list(source.path(), source.academic_year)
    assert len(df) > 650
    assert df["total"].notna().all()
    assert (df["female"] + df["male"] == df["total"]).all()
