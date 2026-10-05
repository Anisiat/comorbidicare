from copy import deepcopy
import inspect

import pandas as pd
import pytest

from comorbidicare.pipeline import build_comorbidity_table

def test_requires_at_least_one_evidence_table():
    cohort_df = pd.DataFrame({
        'subject_id': [1, 2],
        'spell_id': [101, 102],
        'cutoff_date': ['2023-01-01', '2023-01-02']
    })

    with pytest.raises(ValueError, match="At least one comorbidity evidence table is required."):
        build_comorbidity_table(
            cohort_df=cohort_df,
            diagnoses_df=None,
            prescriptions_df=None,
            problems_df=None,
        )

@pytest.mark.parametrize(
    "invalid_cohort_df",
    [
        pd.DataFrame(),  # Empty DataFrame
        pd.DataFrame({'subject_id': [1, 2]}),  # Missing required columns
        pd.DataFrame({'spell_id': [101, 102]}),  # Missing required columns
        pd.DataFrame({'cutoff_date': ['2023-01-01', '2023-01-02']}),
        None  # Missing required columns
    ]
)
def test_requires_cohort_and_complete_cols(invalid_cohort_df, raw_problems_df):
    with pytest.raises(ValueError):
        build_comorbidity_table(
            cohort_df=invalid_cohort_df,
            problems_df=raw_problems_df,
        )

def test_returns_one_row_per_subject_and_spell(cohort_df):

    diagnoses_df = pd.DataFrame({
        'subject': [1, 2],
        'spell_identifier': [101, 102],
        'diagnosis_code_icd': ['A', 'B'],
        'diagnosis_date': ['2022-12-31', '2023-01-01']
    })

    result_df = build_comorbidity_table(
        cohort_df=cohort_df,
        diagnoses_df=diagnoses_df,
        prescriptions_df=None,
        problems_df=None,
    )

    assert result_df.shape[0] == cohort_df.shape[0]


def test_default_pipeline_integrates_all_sources(
    cohort_df, raw_diagnoses_df, raw_prescriptions_df, raw_problems_df,
):
    result = build_comorbidity_table(
        cohort_df, raw_diagnoses_df, raw_prescriptions_df, raw_problems_df, cci_score=True,
    ).set_index("subject")
    assert result.loc["s1", "myocardial_infarction"] == 1
    assert result.loc["s1", "peripheral_vascular_disease"] == 1
    assert result.loc["s1", "chronic_pulmonary_disease"] == 1
    assert result.loc["s1", "cci_score"] == 3
    assert result.loc["s2", "cci_score"] == 0


def test_partial_overrides_across_all_tables(
    cohort_df, raw_diagnoses_df, raw_prescriptions_df, raw_problems_df,
):
    tables = {
        "cohort": cohort_df,
        "diagnoses": raw_diagnoses_df,
        "prescriptions": raw_prescriptions_df,
        "problems": raw_problems_df,
    }
    mapping = {
        "cohort": {"subject": "patient", "spell_identifier": "visit"},
        "diagnoses": {"subject": "person", "diagnosis_code_icd": "icd10", "spell_identifier": "encounter"},
        "prescriptions": {"subject": "patient_id", "medication_name_short": "drug"},
        "problems": {"problem_dt_tm": "recorded_at"},
    }
    renamed = {
        name: df.rename(columns={col: mapping[name].get(col.lower(), col) for col in df.columns})
        for name, df in tables.items()
    }
    originals = {name: df.copy(deep=True) for name, df in renamed.items()}
    original_mapping = deepcopy(mapping)
    expected = build_comorbidity_table(*tables.values(), cci_score=True)
    actual = build_comorbidity_table(*renamed.values(), column_map=mapping, cci_score=True)
    pd.testing.assert_frame_equal(actual, expected)
    assert mapping == original_mapping
    for name in renamed:
        pd.testing.assert_frame_equal(renamed[name], originals[name])


@pytest.mark.parametrize("code_col, code, condition", [
    ("diagnosis_code_icd", "I21.0", "myocardial_infarction"),
    ("diagnosis_code_snomed", "95443002", "peripheral_vascular_disease"),
])
def test_single_diagnosis_code_system_and_admission_fallback(cohort_df, code_col, code, condition):
    diagnoses = pd.DataFrame({"subject": ["s1"], "spell_identifier": ["A1"], code_col: [code]})
    result = build_comorbidity_table(cohort_df, diagnoses_df=diagnoses).set_index("subject")
    assert result.loc["s1", condition] == 1


def test_pipeline_has_only_one_column_configuration_api():
    assert list(inspect.signature(build_comorbidity_table).parameters) == [
        "cohort_df", "diagnoses_df", "prescriptions_df", "problems_df",
        "cci_score", "column_map", "cutoff",
    ]


def test_schema_errors_precede_cleaning(cohort_df, raw_problems_df, monkeypatch):
    def unexpected_cleaning(*args, **kwargs):
        pytest.fail("Cleaning must not start before schema validation finishes")

    monkeypatch.setattr("comorbidicare.pipeline.clean_problems", unexpected_cleaning)
    with pytest.raises(ValueError, match="problems.*problem_code.*column_map"):
        build_comorbidity_table(cohort_df, problems_df=raw_problems_df.drop(columns="PROBLEM_CODE"))


def test_dated_diagnoses_without_spell_column(cohort_df, raw_diagnoses_df):
    result = build_comorbidity_table(
        cohort_df, raw_diagnoses_df.drop(columns="SPELL_IDENTIFIER"),
    ).set_index("subject")
    assert result.loc["s1", "myocardial_infarction"] == 1


def test_missing_cohort_column_is_reported_early(cohort_df, raw_problems_df):
    with pytest.raises(ValueError, match="cohort.*subject.*column_map"):
        build_comorbidity_table(cohort_df.drop(columns="subject"), problems_df=raw_problems_df)


@pytest.mark.parametrize("cutoff, expected", [("admission", 0), ("discharge", 1)])
def test_cutoff_switch_with_renamed_dates(cohort_df, cutoff, expected):
    cohort = cohort_df.rename(columns={"admission_date": "start", "discharge_date": "end"})
    problems = pd.DataFrame({
        "subject": ["s1"], "problem_code": ["95443002"],
        "problem_dt_tm": ["2025-06-02"],
    })
    result = build_comorbidity_table(
        cohort, problems_df=problems, cutoff=cutoff, cci_score=True,
        column_map={"cohort": {"admission_date": "start", "discharge_date": "end"}},
    ).set_index("subject")
    assert result.loc["s1", "peripheral_vascular_disease"] == expected
    assert result.loc["s1", "cci_score"] == expected


def test_invalid_cutoff_rejected(cohort_df, raw_problems_df):
    with pytest.raises(ValueError, match="cutoff must be"):
        build_comorbidity_table(cohort_df, problems_df=raw_problems_df, cutoff="other")
