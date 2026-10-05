import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from comorbidicare.schema import DEFAULT_COLUMN_MAP, standardise_columns


def test_defaults_copy_without_mutating(cohort_df):
    original = cohort_df.copy(deep=True)
    result = standardise_columns(cohort_df, "cohort")
    assert_frame_equal(result, original)
    result.loc[0, "subject"] = "changed"
    assert_frame_equal(cohort_df, original)


@pytest.mark.parametrize("overrides", [
    {"subject": "patient_id"},
    {"subject": "patient_id", "spell_identifier": "visit", "discharge_date": "cutoff"},
])
def test_partial_overrides_preserve_defaults(cohort_df, overrides):
    raw = cohort_df.rename(columns=overrides)
    original = raw.copy(deep=True)
    mapping = {"cohort": overrides.copy()}
    result = standardise_columns(raw, "cohort", mapping)
    assert_frame_equal(result, cohort_df)
    assert_frame_equal(raw, original)
    assert mapping == {"cohort": overrides}
    assert DEFAULT_COLUMN_MAP["cohort"]["subject"] == "subject"


def test_unknown_table(cohort_df):
    with pytest.raises(ValueError, match="Unknown table"):
        standardise_columns(cohort_df, "patients")


@pytest.mark.parametrize("mapping, message", [
    ({"patients": {}}, "Unknown table"),
    ({"cohort": {"patient": "id"}}, "Unknown canonical column"),
    ({"cohort": {"subject": "id", "spell_identifier": " ID "}}, "same input column"),
    ({"cohort": {"subject": "spell_identifier"}}, "same input column"),
    ({"cohort": {"subject": "missing"}}, "mapped to 'subject' is missing"),
    ({"cohort": {"subject": None}}, "non-empty string"),
    ({"cohort": []}, "must be a dictionary"),
    ([], "must be a dictionary"),
])
def test_invalid_mappings(cohort_df, mapping, message):
    with pytest.raises(ValueError, match=message):
        standardise_columns(cohort_df, "cohort", mapping)


def test_existing_canonical_column_collision(cohort_df):
    raw = cohort_df.assign(patient_id="other")
    with pytest.raises(ValueError, match="duplicate canonical"):
        standardise_columns(raw, "cohort", {"cohort": {"subject": "patient_id"}})


def test_duplicate_normalised_columns(cohort_df):
    raw = cohort_df.assign(SUBJECT="other")
    with pytest.raises(ValueError, match="Duplicate columns"):
        standardise_columns(raw, "cohort")


@pytest.mark.parametrize("table, columns, missing", [
    ("cohort", {"spell_identifier": [], "admission_date": [], "discharge_date": []}, "subject"),
    ("diagnoses", {"diagnosis_code_icd": []}, "subject"),
    ("prescriptions", {"subject": [], "order_dt_tm": []}, "medication_name_short"),
    ("problems", {"subject": [], "problem_code": []}, "problem_dt_tm"),
])
def test_missing_required_columns_explain_mapping(table, columns, missing):
    with pytest.raises(ValueError, match=rf"{table}.*{missing}.*column_map"):
        standardise_columns(pd.DataFrame(columns), table)


@pytest.mark.parametrize("code", ["diagnosis_code_icd", "diagnosis_code_snomed"])
def test_diagnoses_only_need_one_coding_system(code):
    raw = pd.DataFrame({"subject": ["s1"], code: ["123"]})
    assert_frame_equal(standardise_columns(raw, "diagnoses"), raw)


def test_diagnoses_require_a_coding_system():
    with pytest.raises(ValueError, match="at least one.*column_map"):
        standardise_columns(pd.DataFrame({"subject": []}), "diagnoses")


def test_existing_case_and_whitespace_normalisation(raw_problems_df):
    raw = raw_problems_df.rename(columns={"SUBJECT": " Patient ID "})
    result = standardise_columns(raw, "problems", {"problems": {"subject": "Patient ID"}})
    assert result["subject"].tolist() == ["s1"]
    assert "problem_code" in result
    assert "encntr_id" in result  # unrelated extra columns survive
