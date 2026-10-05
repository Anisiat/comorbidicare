"""Regression coverage for input and temporal edge cases found in the final review."""

import pandas as pd
import pytest

from comorbidicare.cleaning.clean_diagnoses import clean_diagnoses
from comorbidicare.cleaning.clean_problems import clean_problems
from comorbidicare.features import build_comorbidity_features
from comorbidicare.mapping.map_code_to_comorbidity import map_codes_to_comorbidities
from comorbidicare.pipeline import build_comorbidity_table


@pytest.mark.parametrize("identifier", [1, 1.0, " 1 "])
def test_numeric_cohort_ids_match_cleaned_evidence(identifier):
    cohort = pd.DataFrame({
        "subject": [identifier], "spell_identifier": [101],
        "admission_date": ["2025-01-01"], "discharge_date": ["2025-01-05"],
    })
    problems = pd.DataFrame({"subject": [1], "problem_code": [95443002.0], "problem_dt_tm": ["2024-01-01"]})
    original = cohort.copy(deep=True)
    result = build_comorbidity_table(cohort, problems_df=problems, cci_score=True)
    assert result.loc[0, "peripheral_vascular_disease"] == 1
    assert result.loc[0, "cci_score"] == 1
    assert result.loc[0, "subject"] == "1"
    pd.testing.assert_frame_equal(cohort, original)


@pytest.mark.parametrize("source", ["diagnoses", "problems", "direct"])
def test_float_snomed_codes(source):
    raw = pd.DataFrame({"subject": ["s1"], "code": [95443002.0], "date": ["2024-01-01"]})
    if source == "diagnoses":
        raw = clean_diagnoses(raw.rename(columns={"code": "diagnosis_code_snomed", "date": "diagnosis_date"}))
        raw = raw.rename(columns={"diagnosis_code_snomed": "code", "diagnosis_date": "date"})
    elif source == "problems":
        raw = clean_problems(raw.rename(columns={"code": "problem_code", "date": "problem_dt_tm"}))
        raw = raw.rename(columns={"problem_code": "code", "problem_dt_tm": "date"})
    mapped = map_codes_to_comorbidities(raw, "code", "snomed", "date")
    assert mapped.loc[0, "comorbidity"] == "peripheral_vascular_disease"


def test_mixed_date_formats_and_timezones_survive_pipeline(cohort_df):
    # First row is at the cutoff after converting its offset to UTC; second is earlier.
    problems = pd.DataFrame({
        "subject": ["s1", "s2"], "problem_code": ["95443002"] * 2,
        "problem_dt_tm": ["2025-06-05T01:00:00+01:00", "2024-01-01"],
    })
    result = build_comorbidity_table(cohort_df, problems_df=problems).set_index("subject")
    assert result.loc["s1", "peripheral_vascular_disease"] == 0
    assert result.loc["s2", "peripheral_vascular_disease"] == 1


def test_timezone_aware_evidence_with_naive_cutoff(cohort_df):
    evidence = pd.DataFrame({"subject": ["s1"], "comorbidity": ["dementia"], "comorbidity_date": ["2024-01-01T00:26:23Z"]})
    result = build_comorbidity_features(cohort_df, [evidence])
    assert result.loc[0, "dementia"] == 1


def test_diagnosis_fallback_handles_mixed_timezone_dates(cohort_df):
    diagnoses = pd.DataFrame({
        "subject": ["s1", "s2"], "spell_identifier": ["A1", "B1"],
        "diagnosis_code_icd": ["I21", "I21"],
        "diagnosis_date": ["2024-01-01T01:00:00+01:00", None],
    })
    result = build_comorbidity_table(cohort_df, diagnoses_df=diagnoses)
    assert result["myocardial_infarction"].tolist() == [1, 1]


@pytest.mark.parametrize("field", ["subject", "spell_identifier"])
def test_missing_cohort_identifiers_raise(cohort_df, field):
    evidence = pd.DataFrame({"subject": ["s1"], "comorbidity": ["dementia"], "comorbidity_date": ["2024-01-01"]})
    cohort = cohort_df.copy()
    cohort.loc[0, field] = " "
    with pytest.raises(ValueError, match=f"missing {field}"):
        build_comorbidity_features(cohort, [evidence])


def test_conflicting_spell_cutoffs_raise(cohort_df):
    cohort = pd.concat([cohort_df, cohort_df.assign(discharge_date="2026-01-01")])
    evidence = pd.DataFrame({"subject": ["s1"], "comorbidity": ["dementia"], "comorbidity_date": ["2025-07-01"]})
    with pytest.raises(ValueError, match="conflicting cutoff dates"):
        build_comorbidity_features(cohort, [evidence])


def test_repeated_spells_and_sources_still_produce_binary_flags(cohort_df):
    cohort = pd.concat([cohort_df, cohort_df])
    evidence = pd.DataFrame({"subject": ["s1"], "comorbidity": ["dementia"], "comorbidity_date": ["2024-01-01"]})
    result = build_comorbidity_features(cohort, [evidence, evidence], cci_score=True)
    assert len(result) == 2
    assert result["dementia"].tolist() == [1, 0]
    assert result["cci_score"].tolist() == [1, 0]


def test_blank_icd_mapping_prefix_cannot_match_every_code():
    raw = pd.DataFrame({"subject": ["s1"], "code": ["Z99"], "date": ["2024-01-01"]})
    mapping = pd.DataFrame({"icd_code": ["", " . "], "comorbidity": ["dementia", "renal_disease"]})
    result = map_codes_to_comorbidities(raw, "code", "icd", "date", mapping_df=mapping)
    assert result["comorbidity"].isna().all()


@pytest.mark.parametrize("cutoff_col", ["subject", "spell_identifier", "comorbidity", "comorbidity_date"])
def test_cutoff_cannot_collide_with_join_or_evidence_fields(cohort_df, cutoff_col):
    evidence = pd.DataFrame({"subject": ["s1"], "comorbidity": ["dementia"], "comorbidity_date": ["2024-01-01"]})
    with pytest.raises(ValueError, match="separate cohort date column"):
        build_comorbidity_features(cohort_df, [evidence], cutoff_col=cutoff_col)
