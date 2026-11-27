"""Normalise Irish telephone numbers to E.164 form."""

import re

import pandas as pd
import phonenumbers

_SEPARATORS = re.compile(r"[\s\-().]")


def _to_e164(digits: str) -> str | None:
    if digits.startswith("353"):
        digits = "+" + digits
    elif not digits.startswith(("0", "+")):
        # Spreadsheet software removes the leading zero from numbers
        # stored as numbers.
        digits = "0" + digits
    try:
        number = phonenumbers.parse(digits, "IE")
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(number):
        return None
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def normalise_phone(value: str) -> str | None:
    """Return the numbers in value in E.164 form, joined with ";".

    A number after "/" that is shorter than the first number takes the
    leading digits of the first number: "01 6272166/6272200" gives two
    Dublin numbers. Return None if a number is not a valid Irish number.
    """
    parts = [_SEPARATORS.sub("", p) for p in value.split("/")]
    first = parts[0]
    numbers = []
    for part in parts:
        if len(part) < len(first):
            part = first[: len(first) - len(part)] + part
        number = _to_e164(part)
        if number is None:
            return None
        numbers.append(number)
    return ";".join(dict.fromkeys(numbers))


def normalise_phones(values: pd.Series) -> tuple[pd.Series, list[str]]:
    """Normalise a column of telephone numbers.

    Return the normalised column and the values that are not valid
    numbers. Invalid values become empty.
    """
    present = values.dropna()
    normalised = present.map(normalise_phone)
    invalid = present[normalised.isna()].tolist()
    return normalised.reindex(values.index).astype("string"), invalid
