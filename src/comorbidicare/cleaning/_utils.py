"""Shared helpers for cleaning source tables."""

from numbers import Real, Integral

import pandas as pd


MISSING_TEXT_VALUES = frozenset({"", "none", "null", "nan", "n/a", "na"})


def _clean_optional_string(
    values: pd.Series,
    *,
    lowercase: bool = False,
) -> pd.Series:
    """Normalise whitespace and case-insensitive missing-value markers.

    Preserve actual missing values and return nullable strings. Text retains
    its case unless ``lowercase`` is requested.
    """

    # Collapse whitespace while preserving missing values.
    cleaned = (
        values.astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    if lowercase:
        cleaned = cleaned.str.lower()

    # Match missing markers without changing the output case.
    return cleaned.mask(cleaned.str.lower().isin(MISSING_TEXT_VALUES), pd.NA)


def _parse_dates(values: pd.Series) -> pd.Series:
    """Parse mixed date formats to UTC, returning timezone-naive UTC timestamps.

    Naive inputs are treated as UTC; local timestamps must be localised by callers
    before input. Invalid values become NaT, as in the public cleaners.
    """
    return pd.to_datetime(values, errors="coerce", format="mixed", utc=True).dt.tz_localize(None)


def _clean_snomed_codes(values: pd.Series) -> pd.Series:
    """Remove integer-valued decimal suffixes without converting codes to floats."""
    return _clean_optional_string(values).str.replace(r"^(\d+)\.0+$", r"\1", regex=True)


def _clean_identifier(values: pd.Series) -> pd.Series:
    """Normalise numeric IDs consistently without changing textual leading zeros."""
    values = values.map(
        lambda value: str(int(value))
        if isinstance(value, Real) and not isinstance(value, Integral)
        and pd.notna(value) and float(value).is_integer()
        else value
    )
    return _clean_optional_string(values)
