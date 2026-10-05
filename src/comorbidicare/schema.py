"""Explicit raw-input column adapters (canonical name -> input name)."""

import pandas as pd

from .cleaning.clean_diagnoses import CODE_COLUMNS, REQUIRED_COLUMNS as DIAGNOSIS_REQUIRED
from .cleaning.clean_prescriptions import REQUIRED_COLUMNS as PRESCRIPTION_REQUIRED
from .cleaning.clean_problems import REQUIRED_COLUMNS as PROBLEM_REQUIRED


# Keys are canonical names; values are the expected raw input names.
# Identity mappings make existing iCARE names work without configuration.
# This lists supported fields, including optional ones; requirements are checked below.
DEFAULT_COLUMN_MAP = {
    "cohort": {name: name for name in (
        "subject", "spell_identifier", "admission_date", "discharge_date",
    )},
    "diagnoses": {name: name for name in (
        "subject", "spell_identifier", "diagnosis_code_icd", "diagnosis_code_snomed",
        "diagnosis_date", "diagnosis_desc_icd", "diagnosis_desc_snomed", "admission_date",
    )},
    "prescriptions": {name: name for name in (
        "subject", "medication_name_short", "order_dt_tm",
    )},
    "problems": {name: name for name in (
        "subject", "problem_code", "problem_dt_tm", "problem_desc",
    )},
}


def _validate_column_map(column_map: dict | None) -> None:
    # No overrides means the default schema applies to every table.
    if column_map is None:
        return
    if not isinstance(column_map, dict):
        raise ValueError("column_map must be a dictionary keyed by table name.")
    # Validate every configured table so misspelled table/field names are not ignored.
    for table, overrides in column_map.items():
        if table not in DEFAULT_COLUMN_MAP:
            raise ValueError(f"Unknown table {table!r} in column_map.")
        if not isinstance(overrides, dict):
            raise ValueError(f"column_map[{table!r}] must be a dictionary.")
        for canonical, source in overrides.items():
            if canonical not in DEFAULT_COLUMN_MAP[table]:
                raise ValueError(f"Unknown canonical column {canonical!r} for {table}.")
            if not isinstance(source, str) or not source.strip():
                raise ValueError(f"Input column for {table}.{canonical} must be a non-empty string.")
        # Dictionary union creates a new mapping: right-hand overrides win,
        # while unspecified fields retain defaults and caller dictionaries stay intact.
        merged = DEFAULT_COLUMN_MAP[table] | overrides
        # Check that no two canonical fields map to the same input column
        sources = [name.strip().lower() for name in merged.values()]
        if len(sources) != len(set(sources)):
            raise ValueError(f"Multiple canonical fields in {table} map to the same input column.")


def standardise_columns(
    df: pd.DataFrame,
    table: str,
    column_map: dict | None = None,
) -> pd.DataFrame:
    """Copy, rename and validate one raw table using partial overrides.

    ``column_map`` is keyed by table, then canonical name -> input name.
    Names are stripped and lowercased, as in the existing iCARE cleaners;
    Extra columns are retained. Explicitly mapped inputs must exist, 
    including optional fields when explicitly configured.

    Diagnoses require either coding system; dates and descriptions are optional.
    The pipeline uses diagnosis spell IDs for admission fallback when present.
    """
    if table not in DEFAULT_COLUMN_MAP:
        raise ValueError(f"Unknown table {table!r}; expected one of {list(DEFAULT_COLUMN_MAP)}.")
    
    _validate_column_map(column_map)

    # Select only this table's overrides; absent tables use an empty override dict.
    overrides = (column_map or {}).get(table, {})
    # Merge into a new dictionary without modifying defaults or the user's mapping.
    mapping = DEFAULT_COLUMN_MAP[table] | overrides
    # Work on a copy and preserve the cleaners' existing case/whitespace handling.
    result = df.copy()
    result.columns = result.columns.astype("string").str.strip().str.lower()
    # For example, "SUBJECT" and " subject " would become the same column name.
    if result.columns.duplicated().any():
        raise ValueError(f"Duplicate columns in {table} after normalisation.")
    # An explicit override must point to a real column, even for an optional field.
    for canonical, source in overrides.items():
        if source.strip().lower() not in result.columns:
            raise ValueError(
                f"{table}: input column {source!r} mapped to {canonical!r} is missing; "
                f"check column_map[{table!r}]."
            )
    # pandas expects input -> output names, so reverse our canonical -> input map.
    # Columns outside the map pass through unchanged (apart from normalisation).
    result = result.rename(columns={source.strip().lower(): canonical for canonical, source in mapping.items()})
    # Catch collisions with existing columns, e.g. patient_id -> subject when
    # an unmapped subject column is also present.
    if result.columns.duplicated().any():
        raise ValueError(f"column_map creates duplicate canonical columns in {table} after renaming source columns.")
    # Reuse cleaner requirements for evidence tables; every listed cohort field
    # is required. Diagnosis spell IDs are optional and enable admission fallback.
    required = {
        "cohort": set(DEFAULT_COLUMN_MAP["cohort"]),
        "diagnoses": DIAGNOSIS_REQUIRED,
        "prescriptions": PRESCRIPTION_REQUIRED,
        "problems": PROBLEM_REQUIRED,
    }[table]
    # Compare requirements with the renamed columns so errors use canonical names.
    missing = sorted(required - set(result.columns))
    if missing:
        raise ValueError(
            f"{table} is missing required columns: {missing}. "
            f"Supply canonical names or column_map[{table!r}] "
            "with canonical_name: input_column_name entries."
        )
    # Diagnoses need at least one code system, not necessarily both.
    if table == "diagnoses" and not CODE_COLUMNS.intersection(result.columns):
        raise ValueError(
            "diagnoses requires at least one of 'diagnosis_code_icd' or "
            "'diagnosis_code_snomed'; supply it directly or through column_map['diagnoses']."
        )
    return result
