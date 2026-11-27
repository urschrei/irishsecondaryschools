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


def write_primary_workbook(path, mainstream, special, classes):
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame([["About this data"]]).to_excel(
            writer, sheet_name="Explanatory Note", header=False, index=False
        )
        pd.DataFrame(mainstream).to_excel(
            writer, sheet_name="Mainstream", startrow=1, index=False
        )
        pd.DataFrame(classes).to_excel(
            writer, sheet_name="Mainstream by Standard", index=False
        )
        pd.DataFrame(special).to_excel(
            writer, sheet_name="Special", startrow=1, index=False
        )


def primary_row(roll, name, female, male):
    return {
        "Academic Year (Enrolment)": 2025,
        "Roll Number": roll,
        "Official Name": name,
        "Principal Name": "A Person",
        "Phone No.": "01000000",
        "Gaeltacht Indicator (Y/N)": "N",
        "Female": female,
        "Male": male,
        "Enrolment per Return": female + male,
    }


def test_read_primary_list(tmp_path):
    path = tmp_path / "primary.xlsx"
    write_primary_workbook(
        path,
        mainstream=[primary_row("00359V", "Mainstream NS", 10, 5)],
        special=[primary_row("17890H", "Special School", 3, 4)],
        classes=[
            {
                "Roll Number": "00359V",
                "Junior Infants": 7,
                "Sixth Class": 8,
                "Enrolment per Return": 15,
            }
        ],
    )
    df = dept.drop_contact_columns(dept.read_primary_list(path, 2025))
    assert df["roll_number"].tolist() == ["00359V", "17890H"]
    assert df["special_school"].tolist() == [False, True]
    assert df["total"].tolist() == [15, 7]
    assert df["gaeltacht"].tolist() == [False, False]
    assert not dept.CONTACT_COLUMNS & set(df.columns)

    classes = dept.read_class_groups(path)
    assert classes is not None
    assert classes.iloc[0][["junior_infants", "class_6"]].tolist() == [7, 8]
    assert "class_1" not in classes


def test_read_primary_list_rejects_school_on_both_lists(tmp_path):
    path = tmp_path / "primary.xlsx"
    row = primary_row("00359V", "Mainstream NS", 10, 5)
    write_primary_workbook(path, [row], [row], [{"Roll Number": "00359V"}])
    with pytest.raises(ValueError, match="both lists"):
        dept.read_primary_list(path, 2025)
