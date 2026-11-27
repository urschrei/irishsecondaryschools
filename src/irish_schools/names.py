"""Give school names a standard capitalisation and spelling.

Most primary school names in the Department lists are in capital
letters. Other names are in mixed case. normalise_name converts names
in capital letters to the style of the mixed-case names, for example
"S N NA NGAEL" to "S N na nGael". Names that contain a lower-case
letter do not change.

Many names do not have accents and apostrophes. respell replaces words
with the spellings in spellings.toml, for example "Padraig" with
"Pádraig". The module review finds the possible errors that remain.
"""

import re
import tomllib
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from irish_schools.sources import ROOT

SPELLINGS = ROOT / "spellings.toml"

_VOWELS = set("AEIOUYÁÉÍÓÚ")

# Initialisms and Roman numerals that contain a vowel. Other
# initialisms have no vowel (see _case_word).
_INITIALISMS = {"ASD", "CAMHS", "CHI", "ETNS", "ETSS", "II", "III"}

# Abbreviations without a vowel that have only an initial capital.
_ABBREVIATIONS = {
    "BL",
    "BR",
    "DR",
    "FR",
    "JNR",
    "LTD",
    "MC",
    "MXD",
    "NMH",
    "RD",
    "SC",
    "SCH",
    "SCHL",
    "SNR",
    "SP",
    "ST",
    "STH",
}

# English and Irish words that are in lower case after the first word.
_MINOR_WORDS = {
    "A",
    "AGUS",
    "AN",
    "AND",
    "AR",
    "AT",
    "FOR",
    "GAN",
    "GO",
    "LE",
    "NA",
    "OF",
    "THE",
    "WITH",
}

# Irish eclipsis and the t-prefix before "s". Words that start with
# these letters always have the mutation.
_ALWAYS_MUTATED = re.compile(r"^(BHF|MB|GC|ND|NG|DT|BP|TS)(?=[^\W\d_])")

# Prefixes before a vowel that follow "na", "an" or "de": "na hUaighe",
# "na nGael", "an tAonad", "de hÍde". The words in _UNPREFIXED start
# with these letters, but the letters are not a prefix.
_VOWEL_PREFIX = {"NA": ("H", "N"), "AN": ("T",), "DE": ("H",)}
_UNPREFIXED = {"NAOINEAN", "NAOMH", "TAIRBH", "TEAGHLAIGH", "TEAMPAILL"}

_WORD = re.compile(r"[^\W\d_]+")


def _capitalise(word: str) -> str:
    return word[:1].upper() + word[1:].lower()


def _prefix_length(word: str, previous: str | None) -> int:
    """Return the number of letters in an Irish mutation prefix, or 0."""
    match = _ALWAYS_MUTATED.match(word)
    if match:
        return len(match.group(1)) - 1
    prefixes = _VOWEL_PREFIX.get(previous or "", ())
    if (
        len(word) > 1
        and word[0] in prefixes
        and word[1] in _VOWELS
        and word not in _UNPREFIXED
    ):
        return 1
    return 0


def _case_word(word: str, previous: str | None, following: str | None) -> str:
    """Return one word of a name in its standard capitalisation.

    previous and following are the words before and after it, in
    capital letters, or None at the start and end of the name.
    """
    if previous is not None:
        if word in _MINOR_WORDS:
            return word.lower()
        # "de" in "Vincent de Paul", but "De La Salle" and "Máthair Dé".
        if word == "DE" and following not in {None, "LA"}:
            return word.lower()
    if word in _ABBREVIATIONS:
        return _capitalise(word)
    if word in _INITIALISMS or not _VOWELS.intersection(word):
        return word
    if word.startswith("MC") and len(word) > 2:
        return "Mc" + _capitalise(word[2:])
    prefix = _prefix_length(word, previous)
    return word[:prefix].lower() + _capitalise(word[prefix:])


def normalise_name(name: str) -> str:
    """Return a school name in its standard capitalisation.

    A name that contains a lower-case letter is returned unchanged.
    """
    if name != name.upper():
        return name
    matches = list(_WORD.finditer(name))
    parts = []
    end = 0
    previous: str | None = None
    for i, match in enumerate(matches):
        word = match.group()
        before = name[end : match.start()]
        after = name[match.end() : match.end() + 1]
        if before.endswith("'") and previous is not None:
            # The part after an apostrophe: "JOSEPH'S", "O'TOOLE".
            cased = word.lower() if word == "S" else _capitalise(word)
        elif after == "-" and previous in _VOWEL_PREFIX and len(word) <= 2:
            # A prefix written with a hyphen: "NA H-AILLE".
            cased = word.lower()
        else:
            following = matches[i + 1].group() if i + 1 < len(matches) else None
            cased = _case_word(word, previous, following)
        parts.append(before + cased)
        end = match.end()
        previous = word
    parts.append(name[end:])
    return "".join(parts)


# A word with its apostrophes, for example "Mary's" or "O'Toole". A word
# followed by an apostrophe, such as the "O" in "Kill-O'-the-Grange",
# does not match.
_SPELLED_WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*(?![\w'’])")


def bare(word: str) -> str:
    """Return a word in lower case without accents or apostrophes."""
    decomposed = unicodedata.normalize("NFD", word)
    letters = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"['’]", "", letters).lower()


@dataclass(frozen=True)
class Spellings:
    """The tables in spellings.toml.

    words maps a bare word to its correct spelling. suspects maps a bare
    word that is possibly spelled incorrectly to a possible correct
    spelling. schools maps a roll number to the correct name of that
    school.
    """

    words: dict[str, str] = field(default_factory=dict)
    suspects: dict[str, str] = field(default_factory=dict)
    schools: dict[str, str] = field(default_factory=dict)


def load_spellings(path: Path = SPELLINGS) -> Spellings:
    with path.open("rb") as f:
        data = tomllib.load(f)
    spellings = Spellings(
        words=data.get("words", {}),
        suspects=data.get("suspects", {}),
        schools=data.get("schools", {}),
    )
    for table in ("words", "suspects"):
        for key in getattr(spellings, table):
            if key != bare(key):
                raise ValueError(f"{path}: [{table}] key {key!r} is not a bare word")
    both = spellings.words.keys() & spellings.suspects.keys()
    if both:
        raise ValueError(f"{path}: words in [words] and [suspects]: {sorted(both)}")
    for roll in spellings.schools:
        if not re.fullmatch(r"\d{5}[A-Z]", roll):
            raise ValueError(f"{path}: [schools] key {roll!r} is not a roll number")
    return spellings


def respell(name: str, words: dict[str, str]) -> str:
    """Replace each word in a name that has an entry in words.

    A word in capital letters gets the replacement in capital letters.
    """

    def replace(match: re.Match[str]) -> str:
        word = match.group()
        spelling = words.get(bare(word))
        if spelling is None:
            return word
        if len(word) > 1 and word == word.upper():
            return spelling.upper()
        return spelling

    return _SPELLED_WORD.sub(replace, name)
