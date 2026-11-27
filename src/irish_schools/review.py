"""Find school names that possibly have errors.

The checks find possible errors that the build does not correct: words
with more than one possible spelling, possible typing errors, missing
apostrophes, unusual capitalisation, shortened words and incorrect
punctuation. Each possible error is an Issue. A person must examine
each issue and, if necessary, add the correct name to the [schools]
table in spellings.toml.
"""

import collections
import re
from collections.abc import Iterable
from dataclasses import dataclass

from irish_schools.names import bare

# Kinds of issue.
SPELLING = "spelling"
TYPO = "typo"
APOSTROPHE = "apostrophe"
CAPITALS = "capitals"
ABBREVIATION = "abbreviation"
PUNCTUATION = "punctuation"

_WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*(?![\w'’])")

# Shortened words. The usual Department abbreviations (N S, NS, S N, SN,
# St) and the single letters that show the pupils (B, C, G, M) are not
# in this set.
_ABBREVIATIONS = {
    "bl": "Blessed",
    "br": "Brother",
    "buac": "Buachaillí",
    "con": "Convent",
    "denom": "Denominational",
    "inf": "Infant",
    "jnr": "Junior",
    "jun": "Junior",
    "mxd": "Mixed",
    "nais": "Náisiúnta",
    "nfa": "Naofa",
    "nmh": "Naomh",
    "paroc": "Parochial",
    "sc": None,
    "sch": "School",
    "schl": "School",
    "sen": "Senior",
    "ser": None,
    "snr": "Senior",
    "sois": "Sóisearach",
    "sp": "Special",
    "spec": "Special",
}

# Words in lower case after the first word, as normalise_name gives them.
_MINOR_WORDS = {
    "a",
    "agus",
    "an",
    "and",
    "ar",
    "at",
    "for",
    "gan",
    "go",
    "le",
    "na",
    "of",
    "the",
    "with",
}

# A lower-case Irish prefix before a capital: "nGael", "tSlí", "bhFilí".
_PREFIXED = re.compile(r"^(?:bh|[bdghmnt])[A-ZÁÉÍÓÚ]")
# Initialisms in names that are in capital letters.
_INITIALISMS = {"ASD", "CAMHS", "CBS", "CHI", "CNS", "ETNS", "ETSS", "II", "III"}
_VOWELS = set("AEIOUYÁÉÍÓÚ")
_PERSON = {"st", "saint"}

# Characters that school names usually contain.
_USUAL = re.compile(r"[^\w\s'’.,&()/\-]")


@dataclass(frozen=True)
class Issue:
    """One possible error in a name.

    text is the part of the name that has the possible error. suggestion
    is a possible correction of text, or None if there is no suggestion.
    """

    kind: str
    text: str
    suggestion: str | None = None


class Vocabulary:
    """The words in a set of school names, with the number of names that
    contain each word."""

    def __init__(self, names: Iterable[str]) -> None:
        self.counts: collections.Counter[str] = collections.Counter()
        spellings: dict[str, collections.Counter[str]] = collections.defaultdict(
            collections.Counter
        )
        for name in set(names):
            for word in set(_WORD.findall(name)):
                key = word.lower()
                self.counts[key] += 1
                spellings[key][word] += 1
        self._spelling = {k: c.most_common(1)[0][0] for k, c in spellings.items()}

    def spelling(self, word: str) -> str:
        """Return the most frequent capitalisation of a word."""
        return self._spelling.get(word.lower(), word)

    def frequent_neighbour(self, word: str, minimum: int = 5) -> str | None:
        """Return a frequent word that is one edit from a word, or None.

        The first letter does not change. Edits that add or remove the
        lenition "h" or an Irish prefix do not count, because they give
        a different form of the same word.
        """
        key = word.lower()
        best = None
        for candidate in {key[0] + edit for edit in _edits(key[1:])}:
            if self.counts[candidate] >= minimum and not _same_word(key, candidate):
                if best is None or self.counts[candidate] > self.counts[best]:
                    best = candidate
        return None if best is None else self.spelling(best)


_ALPHABET = "abcdefghijklmnopqrstuvwxyzáéíóú'"


def _edits(word: str) -> set[str]:
    """Return the strings one deletion, insertion, substitution or
    transposition from a word."""
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = {a + b[1:] for a, b in splits if b}
    transposes = {a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1}
    replaces = {a + c + b[1:] for a, b in splits if b for c in _ALPHABET}
    inserts = {a + c + b for a, b in splits for c in _ALPHABET}
    return (deletes | transposes | replaces | inserts) - {word}


def _same_word(a: str, b: str) -> bool:
    """Return True if two words differ only by accents, lenition, an
    Irish prefix or a slender ending ("Naomh" and "Naoimh")."""
    a, b = bare(a), bare(b)
    if a == b:
        return True
    short, long = sorted((a, b), key=len)
    if len(long) != len(short) + 1:
        return False
    if long[0] in "bcdfgmpst" and long[1] == "h" and long[0] + long[2:] == short:
        return True
    if long[0] in "hnt" and long[1:] == short:
        return True
    tail = re.search(r"[^aeiouy]+$", short)
    if tail is not None and tail.start() > 0:
        j = tail.start()
        return long == short[:j] + "i" + short[j:]
    return False


def review_name(
    name: str, vocabulary: Vocabulary, suspects: dict[str, str]
) -> list[Issue]:
    """Return the possible errors in a school name."""
    issues: list[Issue] = []
    words = list(_WORD.finditer(name))
    for i, match in enumerate(words):
        word = match.group()
        key = word.lower()
        previous = words[i - 1].group().lower() if i else None

        alternative = suspects.get(bare(word))
        if alternative is not None and alternative != word:
            issues.append(Issue(SPELLING, word, alternative))
            continue

        if key in _ABBREVIATIONS:
            issues.append(Issue(ABBREVIATION, word, _ABBREVIATIONS[key]))
            continue

        if (
            previous in _PERSON
            and key.endswith("s")
            and not key.endswith(("'s", "ss"))
            and vocabulary.counts[key[:-1]] >= 2
        ):
            issues.append(Issue(APOSTROPHE, word, word[:-1] + "'s"))
            continue

        capitals = _capitals(word, first=i == 0)
        if capitals is not None:
            issues.append(Issue(CAPITALS, word, capitals))
            continue

        if vocabulary.counts[key] <= 1 and len(key) >= 5:
            neighbour = vocabulary.frequent_neighbour(word)
            if neighbour is not None:
                issues.append(Issue(TYPO, word, neighbour))

    issues += _punctuation(name)
    return issues


def _capitals(word: str, first: bool) -> str | None:
    """Return the usual capitalisation of a word, or None if the word
    already has it."""
    if len(word) > 2 and word == word.upper():
        if word in _INITIALISMS or not _VOWELS.intersection(word):
            return None
        return word.capitalize()
    lower = word.lower()
    if word[0].islower():
        if first or (lower not in _MINOR_WORDS and not _PREFIXED.match(word)):
            return word[0].upper() + word[1:]
    elif not first and lower in _MINOR_WORDS and word != word.upper():
        return lower
    return None


def _punctuation(name: str) -> list[Issue]:
    checks = [
        (r"\s{2,}", " "),
        (r"^\s+|\s+$", ""),
        (r"\(\s+", "("),
        (r"\s+\)", ")"),
        (r"\s*,\s*$", ""),
        (r"\s,", ","),
        (r"[^\W\d_]\d|\d[^\W\d_]", None),
        (r"\S&|&\S", None),
        (r"(?<=[^\W\d_])\.(?=[^\W\d_]{2,})", ". "),
    ]
    issues = [
        Issue(PUNCTUATION, m.group(), replacement)
        for pattern, replacement in checks
        for m in re.finditer(pattern, name)
    ]
    issues += [Issue(PUNCTUATION, m.group()) for m in _USUAL.finditer(name)]
    return issues
