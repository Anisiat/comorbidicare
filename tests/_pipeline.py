"""End-to-end tests for the high-level pipeline.

These describe how ``build_comorbidity_table`` should behave when given raw
iCARE tables. They are the "does the headline feature actually run" check.
"""

import importlib

import pandas as pd
import pytest

from comorbidicare.features import CCI_COMORBIDITIES


def test_pipeline_module_imports():
    """The pipeline module must import without error."""
    module = importlib.import_module("comorbidicare.pipeline")
    assert hasattr(module, "build_comorbidity_table")


def test_end_to_end_flags_and_cci_score(
    cohort_df, raw_diagnoses_df, raw_problems_df, raw_prescriptions_df
):
    """Raw iCARE tables in, one row per spell with flags and a CCI score out."""
    from comorbidicare.pipeline import build_comorbidity_table

    features = build_comorbidity_table(
        cohort_df=cohort_df,
        diagnoses_df=raw_diagnoses_df,
        prescriptions_df=raw_prescriptions_df,
        problems_df=raw_problems_df,
        cutoff_col="discharge_date",
        cci_score=True,
    )

    assert list(features.columns) == [
        "subject",
        "spell_identifier",
        *CCI_COMORBIDITIES,
        "cci_score",
    ]
    assert len(features) == 2

    s1 = features.set_index("subject").loc["s1"]
    assert s1["myocardial_infarction"] == 1  # from ICD diagnosis
    assert s1["peripheral_vascular_disease"] == 1  # from SNOMED problem
    assert s1["chronic_pulmonary_disease"] == 1  # from medication
    assert s1["cci_score"] == 3

    s2 = features.set_index("subject").loc["s2"]
    assert s2[list(CCI_COMORBIDITIES)].sum() == 0
    assert s2["cci_score"] == 0


def test_single_evidence_table_is_enough(cohort_df, raw_problems_df):
    """Users may provide only one of the three source tables."""
    from comorbidicare.pipeline import build_comorbidity_table

    features = build_comorbidity_table(
        cohort_df=cohort_df,
        problems_df=raw_problems_df,
    )

    assert "cci_score" not in features.columns
    s1 = features.set_index("subject").loc["s1"]
    assert s1["peripheral_vascular_disease"] == 1
    assert s1["myocardial_infarction"] == 0


def test_undated_diagnosis_falls_back_to_spell_admission_date(cohort_df):
    """A diagnosis with no date should borrow its spell's admission date.

    Uses the raw iCARE ``spell_identifier`` column. Most iCARE diagnosis dates
    are missing, so this fallback is what makes diagnosis evidence usable.
    """
    from comorbidicare.pipeline import build_comorbidity_table

    cohort = pd.concat(
        [
            pd.DataFrame(
                {
                    "subject": ["s1"],
                    "spell_identifier": ["A0"],
                    "admission_date": ["2024-02-01"],
                    "discharge_date": ["2024-02-05"],
                }
            ),
            cohort_df,
        ],
        ignore_index=True,
    )
    diagnoses = pd.DataFrame(
        {
            "subject": ["s1"],
            "spell_identifier": ["A0"],
            "diagnosis_code_icd": ["I21.0"],
            "diagnosis_date": [None],
        }
    )

    features = build_comorbidity_table(cohort_df=cohort, diagnoses_df=diagnoses)

    later_spell = features.set_index("spell_identifier").loc["A1"]
    assert later_spell["myocardial_infarction"] == 1


def test_requires_at_least_one_evidence_table(cohort_df):
    from comorbidicare.pipeline import build_comorbidity_table

    with pytest.raises(ValueError, match="At least one"):
        build_comorbidity_table(cohort_df=cohort_df)


def test_cohort_missing_required_column_raises(raw_problems_df):
    from comorbidicare.pipeline import build_comorbidity_table

    cohort = pd.DataFrame(
        {"subject": ["s1"], "admission_date": ["2025-06-01"]}
    )  # no spell_identifier, no discharge_date

    with pytest.raises(ValueError, match="missing required column"):
        build_comorbidity_table(cohort_df=cohort, problems_df=raw_problems_df)
