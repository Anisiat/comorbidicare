import pandas as pd

from .cleaning._utils import _clean_identifier, _parse_dates

CCI_WEIGHTS = {
"myocardial_infarction": 1,
"congestive_heart_failure": 1,
"peripheral_vascular_disease": 1,
"cerebrovascular_disease": 1,
"dementia": 1,
"chronic_pulmonary_disease": 1,
"rheumatic_disease": 1,
"peptic_ulcer_disease": 1,
"mild_liver_disease": 1,
"diabetes_without_complication": 1,
"diabetes_with_complication": 2,
"hemiplegia_or_paraplegia": 2,
"renal_disease": 2,
"malignancy": 2,
"moderate_or_severe_liver_disease": 3,
"metastatic_solid_tumor": 6,
"aids_hiv": 6,
}

CCI_COMORBIDITIES = tuple(CCI_WEIGHTS)

def _calculate_cci_score(df):
    """Calculate CCI score while preserving original condition flags."""

    df = df.copy()
    scoring_df = df.copy()

    scoring_df.loc[
        scoring_df["diabetes_with_complication"] == 1,
        "diabetes_without_complication",
    ] = 0

    scoring_df.loc[
        scoring_df["moderate_or_severe_liver_disease"] == 1,
        "mild_liver_disease",
    ] = 0

    scoring_df.loc[
        scoring_df["metastatic_solid_tumor"] == 1,
        "malignancy",
    ] = 0

    df["cci_score"] = sum(
        scoring_df[condition] * weight
        for condition, weight in CCI_WEIGHTS.items()
    )

    return df


def build_comorbidity_features(
    cohort_df: pd.DataFrame,
    evidence_tables: list[pd.DataFrame],
    cci_score: bool = False,
    cutoff_col: str = "discharge_date",
) -> pd.DataFrame:
    """Build spell-level binary comorbidity features from mapped evidence.

    Combines one or more mapped comorbidity evidence tables, retains
    evidence recorded before each spell-specific cutoff date, and returns
    one row per subject and spell with binary comorbidity indicators.

    Parameters
    ----------
    cohort_df : pd.DataFrame
        Canonical cohort containing ``subject``, ``spell_identifier``, and
        the date column selected by ``cutoff_col``.
    evidence_tables : list[pd.DataFrame]
        One or more mapped comorbidity tables containing ``subject``,
        ``comorbidity``, and ``comorbidity_date``.
    cci_score : bool, default=False
        Include CCI score in output table.

    cutoff_col : str, default="discharge_date"
        Cohort date column defining the evidence cutoff, e.g. admission_date.

    Returns
    -------
    pd.DataFrame
        One row per subject and spell with 17 CCI binary comorbidity columns
        and, when requested, an additional ``cci_score`` column.

    Raises
    ------
    ValueError
        If required columns are missing, no evidence tables are supplied,
        cutoff dates are missing or invalid, or matched evidence contains
        unrecognised comorbidity labels.

    Notes
    -----
    Dates are normalised to timezone-naive UTC; naive inputs are treated as UTC.
    Subject and spell identifiers are normalised to strings.
    Evidence dates must be strictly earlier than the cutoff. Records missing
    a subject, comorbidity, or usable evidence date do not contribute flags.
    Scoring excludes the less severe diabetes, liver disease, or malignancy
    category when its more severe counterpart is present, while preserving
    the original binary flags. No age adjustment is applied.
    """

    if cutoff_col in {"subject", "spell_identifier", "comorbidity", "comorbidity_date"}:
        raise ValueError("cutoff_col must name a separate cohort date column.")

    required_cohort_columns = {
        'subject',
        'spell_identifier',
        cutoff_col,
    }

    missing_columns = required_cohort_columns - set(cohort_df.columns)
    if missing_columns:
        raise ValueError(
            f"cohort_df is missing required columns: {missing_columns}"
        )

    if not evidence_tables:
        raise ValueError("At least one comorbidity evidence table is required.")

    required_evidence_columns = [
        'subject',
        'comorbidity',
        'comorbidity_date',
    ]

    for i, table in enumerate(evidence_tables):
        missing_columns = set(required_evidence_columns) - set(table.columns)

        if missing_columns:
            raise ValueError(
                f"Evidence table {i} is missing required columns: "
                f"{missing_columns}"
            )


    # Combine evidence from all available sources.
    evidence = pd.concat(
        [table[required_evidence_columns] for table in evidence_tables],
        ignore_index=True,
    )

    # Standardise dates.
    cohort = cohort_df[
        ['subject', 'spell_identifier', cutoff_col]
    ].copy()

    cohort[cutoff_col] = _parse_dates(cohort[cutoff_col])

    evidence['comorbidity_date'] = _parse_dates(evidence['comorbidity_date'])

    # Cleaners produce string identifiers; normalise cohort and direct evidence alike.
    for column in ("subject", "spell_identifier"):
        cohort[column] = _clean_identifier(cohort[column])
        if cohort[column].isna().any():
            raise ValueError(f"cohort_df contains missing {column} identifiers.")
    evidence["subject"] = _clean_identifier(evidence["subject"])

    # Each subject/spell must have exactly one cutoff, or evidence could leak
    # across contradictory copies of the same output row.
    cohort = cohort.drop_duplicates()
    if cohort.duplicated(["subject", "spell_identifier"]).any():
        raise ValueError("cohort_df contains conflicting cutoff dates for the same subject and spell.")

    # Reject records that are missing a usable cutoff date.
    if cohort[cutoff_col].isna().any():
        raise ValueError(
            f"cohort_df contains missing or invalid values in '{cutoff_col}'."
        )

    # Remove records that cannot contribute a mapped comorbidity.
    evidence = evidence.dropna(
        subset=['subject', 'comorbidity', 'comorbidity_date']
    )

    # Give each evidence record the cutoff date for every spell
    # belonging to that subject.
    evidence = evidence.merge(
        cohort,
        on='subject',
        how="inner",
    )

    # Check that all comorbidities in the evidence are recognised.
    observed_comorbidities = set(
    evidence['comorbidity'].dropna().unique()
    )

    unknown_comorbidities = (
        observed_comorbidities - set(CCI_COMORBIDITIES)
    )

    if unknown_comorbidities:
        raise ValueError(
            "Evidence contains unknown comorbidities: "
            f"{sorted(unknown_comorbidities)}"
        )

    # Only evidence strictly before the spell cutoff contributes.
    past_evidence = evidence[
        evidence['comorbidity_date'] < evidence[cutoff_col]
    ].copy()

    # Multiple codes/sources for the same comorbidity only need to
    # contribute one positive flag.
    past_evidence = past_evidence.drop_duplicates(
        subset=['subject', 'spell_identifier', 'comorbidity']
    )

    past_evidence["present"] = 1

    # Convert long comorbidity evidence into binary wide features.
    features = past_evidence.pivot_table(
        index=['subject', 'spell_identifier'],
        columns='comorbidity',
        values="present",
        aggfunc="max",
        fill_value=0,
    )

    # Guarantee that every expected comorbidity column exists,
    # even if no patient in this dataset has that condition.
    features = features.reindex(
        columns=CCI_COMORBIDITIES,
        fill_value=0,
    )

    features = features.reset_index()

    # Add spells with no historical comorbidity evidence.
    features = cohort[
        ['subject', 'spell_identifier']
    ].drop_duplicates().merge(
        features,
        on=['subject', 'spell_identifier'],
        how="left",
    )

    features[list(CCI_COMORBIDITIES)] = (
        features[list(CCI_COMORBIDITIES)]
        .fillna(0)
        .astype("int8")
    )

    if cci_score:
        features = _calculate_cci_score(features)

    return features
