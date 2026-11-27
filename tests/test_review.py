import pytest

from irish_schools.review import (
    ABBREVIATION,
    APOSTROPHE,
    CAPITALS,
    PUNCTUATION,
    SPELLING,
    TYPO,
    Issue,
    Vocabulary,
    review_name,
)

VOCABULARY = Vocabulary(
    [f"{word} {i}" for word in ("Educate", "Colmcille", "Brigid") for i in range(6)]
    + ["S N Naomh", "Scoil Naomh", "Naomh Eoin", "Naomh Treasa", "Naomh Brid"]
)
SUSPECTS = {"rath": "Ráth", "mor": "Mór"}


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "S N Rath Mor",
            [Issue(SPELLING, "Rath", "Ráth"), Issue(SPELLING, "Mor", "Mór")],
        ),
        ("S N Ráth Mór", []),
        ("St Brigids NS", [Issue(APOSTROPHE, "Brigids", "Brigid's")]),
        ("St Francis NS", []),
        ("Carysfort Mxd N S", [Issue(ABBREVIATION, "Mxd", "Mixed")]),
        ("Monkstown Eucate Together NS", [Issue(TYPO, "Eucate", "Educate")]),
        ("Scoil Cholmcille", []),
        ("Drogheda ABACAS School", [Issue(CAPITALS, "ABACAS", "Abacas")]),
        ("Mount Sion CBS N S", []),
        ("Coláiste pobail Fóla", [Issue(CAPITALS, "pobail", "Pobail")]),
        ("Colaiste Na Sionna", [Issue(CAPITALS, "Na", "na")]),
        ("Scoil na nGael", []),
        ("St Fachtna's De La Salle", []),
        ("St Vincent de Paul Senior School", []),
        ("Gaelscoil de hÍde", []),
        ("Dookinella  N.S.", [Issue(PUNCTUATION, "  ", " ")]),
        ("Coole N.S,", [Issue(PUNCTUATION, ",", "")]),
        ("Scoil C.Uí Dhálaigh", [Issue(PUNCTUATION, ".", ". ")]),
        ("Scoil Aodh Rua&Nuala", [Issue(PUNCTUATION, "a&", None)]),
        ("St Joseph¿s", [Issue(CAPITALS, "s", "S"), Issue(PUNCTUATION, "¿", None)]),
    ],
)
def test_review_name(name, expected):
    assert review_name(name, VOCABULARY, SUSPECTS) == expected


@pytest.mark.parametrize("name", ["Scoil Naoimh Eoin", "S N Bhrid", "Scoil Eoin Naomh"])
def test_review_name_ignores_other_forms_of_a_word(name):
    assert review_name(name, VOCABULARY, SUSPECTS) == []


def test_review_name_finds_typo_in_slender_ending():
    assert review_name("S N Naiomh Eoin", VOCABULARY, SUSPECTS) == [
        Issue(TYPO, "Naiomh", "Naomh")
    ]
