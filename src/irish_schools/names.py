"""Give school names in capital letters a standard capitalisation.

Most primary school names in the Department lists are in capital
letters. Other names are in mixed case. This module converts names in
capital letters to the style of the mixed-case names, for example
"S N NA NGAEL" to "S N na nGael". Names that contain a lower-case
letter do not change. The module changes only capitalisation: it does
not add missing apostrophes or accents.
"""

import re

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
