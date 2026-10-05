import logging
from typing import Literal

import pandas as pd

from .cleaning.clean_diagnoses import clean_diagnoses
from .cleaning.clean_prescriptions import clean_prescriptions
from .cleaning.clean_problems import clean_problems
from .mapping.map_code_to_comorbidity import map_codes_to_comorbidities
from .features import build_comorbidity_features
from .schema import standardise_columns

logger = logging.getLogger(__name__)

def build_comorbidity_table(
    cohort_df: pd.DataFrame,
    diagnoses_df: pd.DataFrame | None = None,
    prescriptions_df: pd.DataFrame | None = None,
    problems_df: pd.DataFrame | None = None,
    cci_score: bool = False,
    column_map: dict | None = None,
    cutoff: Literal["admission", "discharge"] = "discharge",
) -> pd.DataFrame:
    """Build spell-level comorbidity flags and optional CCI scores from raw tables.

    Parameters
    ----------
    cohort_df : pd.DataFrame
        Cohort with subject, spell_identifier, admission_date and discharge_date.
    diagnoses_df, prescriptions_df, problems_df : pd.DataFrame, optional
        Raw iCARE evidence. At least one non-empty source is required.
        Diagnoses require subject and at least one of diagnosis_code_icd or
        diagnosis_code_snomed. Optional spell_identifier enables admission-date
        fallback when diagnosis dates are missing.
    cci_score : bool, default=False
        Include the weighted CCI score.
    column_map : dict, optional
        Partial mappings keyed by cohort, diagnoses, prescriptions or problems,
        then canonical name -> input name. Unspecified fields use iCARE defaults.
        See comorbidicare.schema.DEFAULT_COLUMN_MAP for supported fields.
        Input DataFrames are copied; column names are stripped and lowercased.

    cutoff : {"admission", "discharge"}, default="discharge"
        Use the canonical admission_date or discharge_date as the evidence cutoff.
        Evidence exactly at the selected cutoff is excluded.

    Returns
    -------
    pd.DataFrame
        One row per subject and spell with 17 binary flags and optional cci_score.
        Output names are canonical. Evidence must predate each spell's
        selected cutoff.
    """

    if cutoff not in ("admission", "discharge"):
        raise ValueError("cutoff must be 'admission' or 'discharge'.")

    logger.info('Validating input dataframes and required columns...')
    # check at least one comorbidity evidence table is provided
    if all(
        df is None or df.empty
        for df in [diagnoses_df, prescriptions_df, problems_df]
    ):
        raise ValueError("At least one comorbidity evidence table is required.")

    # check that cohort_df is provided and not empty
    if cohort_df is None or cohort_df.empty:
        raise ValueError("Cohort dataframe is required and cannot be empty.")

    cohort_df = standardise_columns(cohort_df, "cohort", column_map)
    diagnoses_df = standardise_columns(diagnoses_df, "diagnoses", column_map) if diagnoses_df is not None else None
    prescriptions_df = standardise_columns(prescriptions_df, "prescriptions", column_map) if prescriptions_df is not None else None
    problems_df = standardise_columns(problems_df, "problems", column_map) if problems_df is not None else None

    logger.info('Cleaning comorbidity evidence tables...')

    clean_diagnoses_df = None
    if diagnoses_df is not None:
        spell_dates = (
            cohort_df[["subject", "spell_identifier", "admission_date"]].copy()
            if "spell_identifier" in diagnoses_df.columns else None
        )
        clean_diagnoses_df = clean_diagnoses(
            diagnoses_df, spell_admission_dates_df=spell_dates,
        )

    clean_prescriptions_df = clean_prescriptions(prescriptions_df) if prescriptions_df is not None else None
    clean_problems_df = clean_problems(problems_df) if problems_df is not None else None

    logger.info('Mapping comorbidities to CCI conditions...')

    mapped_evidence_tables = []
    if clean_diagnoses_df is not None:
        for code_col, code_type in (("diagnosis_code_icd", "icd"), ("diagnosis_code_snomed", "snomed")):
            if code_col in clean_diagnoses_df.columns:
                mapped_evidence_tables.append(map_codes_to_comorbidities(
                    clean_diagnoses_df, code_col, code_type, "comorbidity_date", source="diagnoses",
                ))
    if clean_prescriptions_df is not None:
        mapped_evidence_tables.append(map_codes_to_comorbidities(
            clean_prescriptions_df, "medication_name_short", "medication", "order_dt_tm", source="prescriptions",
        ))
    if clean_problems_df is not None:
        mapped_evidence_tables.append(map_codes_to_comorbidities(
            clean_problems_df, "problem_code", "snomed", "problem_dt_tm", source="problems",
        ))

    logger.info('Building spell-level binary comorbidity features...')

    features_df = build_comorbidity_features(
        cohort_df=cohort_df,
        evidence_tables=mapped_evidence_tables,
        cci_score=cci_score,
        cutoff_col=f"{cutoff}_date",
    )

    logger.info('Comorbidity feature building complete.')

    return features_df
