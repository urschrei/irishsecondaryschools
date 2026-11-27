import pandas as pd
import pytest

from irish_schools.build import LEVELS, OUTPUT_DIR
from irish_schools.names import (
    bare,
    load_spellings,
    normalise_name,
    query_name,
    respell,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("BALLINSPITTLE N S", "Ballinspittle N S"),
        ("ST BRIGIDS MXD N S", "St Brigids Mxd N S"),
        ("ST. LOUIS GIRLS NATIONAL SCHOOL", "St. Louis Girls National School"),
        ("CONVENT OF MERCY N.S.", "Convent of Mercy N.S."),
        ("THE GLEBE NS", "The Glebe NS"),
        ("SN MHUIRE BNS", "SN Mhuire BNS"),
        ("MOUNT SION CBS N S", "Mount Sion CBS N S"),
        ("JOHN PAUL II N S", "John Paul II N S"),
        ("BL OLIVER PLUNKETT N S", "Bl Oliver Plunkett N S"),
        ("ST JOSEPH'S N.S.", "St Joseph's N.S."),
        ("ST LAURENCE O'TOOLE'S NS", "St Laurence O'Toole's NS"),
        ("KILL-O'-THE-GRANGE NS", "Kill-O'-the-Grange NS"),
        ("ARCHBISHOP MCQUAID NATIONAL SCHOOL", "Archbishop McQuaid National School"),
        ("CATHERINE MC AULEY N SC", "Catherine Mc Auley N Sc"),
        ("SCOIL MHUIRE AGUS N.TREASA", "Scoil Mhuire agus N.Treasa"),
        ("S N MUIRE GAN SMAL B", "S N Muire gan Smal B"),
        ("COLÁISTE NAOMH ÉINNE", "Coláiste Naomh Éinne"),
    ],
)
def test_normalise_name(raw, expected):
    assert normalise_name(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("MUIRE NA NGAEL NS", "Muire na nGael NS"),
        ("SCOIL NA MBRAITHRE", "Scoil na mBraithre"),
        ("GAELSCOIL NA BHFILI", "Gaelscoil na bhFili"),
        ("S N MAINISTIR O DTORNA", "S N Mainistir O dTorna"),
        ("SCOIL SEAN TSRAIDE", "Scoil Sean tSraide"),
        ("S N GLEANN NA HULADH", "S N Gleann na hUladh"),
        ("S N NA H-AILLE", "S N na h-Aille"),
        ("S N ATH NA BH-FEARCON", "S N Ath na bh-Fearcon"),
        ("AN TAONAD REAMHSCOILE", "An tAonad Reamhscoile"),
        ("GAELSCOIL DE HIDE", "Gaelscoil de hIde"),
    ],
)
def test_normalise_name_irish_prefixes(raw, expected):
    assert normalise_name(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("S N CILL NA NAOMH", "S N Cill na Naomh"),
        ("AN TEAGHLAIGH NAOFA", "An Teaghlaigh Naofa"),
        ("S N AN TRIAN", "S N an Trian"),
        ("AN HALLA", "An Halla"),
    ],
)
def test_normalise_name_without_prefix(raw, expected):
    assert normalise_name(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ST VINCENT DE PAUL SENIOR SCHOOL", "St Vincent de Paul Senior School"),
        ("ST JOHNS COLLEGE DE LA SALLE", "St Johns College De La Salle"),
        ("SCOIL MATHAIR DE", "Scoil Mathair De"),
        ("DE LACY COLLEGE", "De Lacy College"),
    ],
)
def test_normalise_name_de(raw, expected):
    assert normalise_name(raw) == expected


@pytest.mark.parametrize(
    "name",
    ["Scoil Mhuire Agus Chormaic", "SN Ath na Lionta", "ABACAS Kilbarrack", ""],
)
def test_normalise_name_keeps_mixed_case(name):
    assert normalise_name(name) == name


WORDS = {"padraig": "Pádraig", "marys": "Mary's", "mbraithre": "mBráithre"}


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("S N Naomh Padraig", "S N Naomh Pádraig"),
        ("St Marys NS", "St Mary's NS"),
        ("St Mary's NS", "St Mary's NS"),
        ("Scoil na mBraithre", "Scoil na mBráithre"),
        ("Scoil Naomh Pádraíg", "Scoil Naomh Pádraig"),
        ("SCOIL PADRAIG", "SCOIL PÁDRAIG"),
        ("St Marysn.S", "St Marysn.S"),
    ],
)
def test_respell(name, expected):
    assert respell(name, WORDS) == expected


QUERIES = {"rath": "Ráth", "o": "Ó"}


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("S N Rath Mor", "Rath or Ráth"),
        ("S N Ráth Mór", None),
        ("S N O Dubhlain Rath Rath", "O or Ó; Rath or Ráth"),
        ("Kill-O'-the-Grange NS", None),
        ("O'Carolan College", None),
        ("Rathcoffey N S", None),
    ],
)
def test_query_name(name, expected):
    assert query_name(name, QUERIES) == expected


def test_load_spellings_rejects_marked_key(tmp_path):
    path = tmp_path / "spellings.toml"
    path.write_text('[words]\n"pádraig" = "Pádraig"\n')
    with pytest.raises(ValueError, match="bare word"):
        load_spellings(path)


def test_load_spellings_rejects_word_in_both_tables(tmp_path):
    path = tmp_path / "spellings.toml"
    path.write_text('[words]\nrath = "Ráth"\n[queries]\nrath = "Ráth"\n')
    with pytest.raises(ValueError, match="\\[words\\] and \\[queries\\]"):
        load_spellings(path)


def test_load_spellings_rejects_bad_roll_number(tmp_path):
    path = tmp_path / "spellings.toml"
    path.write_text('[schools]\n"1234A" = "Scoil"\n')
    with pytest.raises(ValueError, match="roll number"):
        load_spellings(path)


def test_spellings_table_is_valid():
    spellings = load_spellings()
    for key, spelling in {**spellings.words, **spellings.queries}.items():
        assert bare(spelling) == key, key


def test_school_names_are_current_schools():
    spellings = load_spellings()
    paths = [OUTPUT_DIR / f"{level.stem}_schools.parquet" for level in LEVELS]
    if not all(path.exists() for path in paths):
        pytest.skip("run `schools build`")
    rolls = set().union(*(set(pd.read_parquet(p)["roll_number"]) for p in paths))
    assert set(spellings.schools) <= rolls
