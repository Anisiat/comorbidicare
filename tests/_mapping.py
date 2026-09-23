"""Tests for the bundled lookups and code-to-comorbidity mapping."""

import pandas as pd
import pytest

from comorb_icare.features import CCI_COMORBIDITIES
from comorb_icare.mapping import load_mapping
from comorb_icare.mapping.map_code_to_comorbidity import map_codes_to_comorbidities


@pytest.mark.parametrize(
    ("mapping_type", "code_column"),
    [
        ("icd", "icd_code"),
        ("snomed", "snomed_code"),
        ("medication", "medication_name"),
    ],
)
def test_bundled_mappings_load_with_expected_columns(mapping_type, code_column):
    mapping = load_mapping(mapping_type)

    assert {"comorbidity", code_column} <= set(mapping.columns)
    assert len(mapping) > 0
    assert mapping[code_column].dtype == "string"


@pytest.mark.parametrize("mapping_type", ["icd", "snomed", "medication"])
def test_bundled_mappings_only_use_known_comorbidities(mapping_type):
    """Every label in the CSVs must be one the scorer knows how to weight."""
    mapping = load_mapping(mapping_type)

    unknown = set(mapping["comorbidity"].dropna()) - set(CCI_COMORBIDITIES)
    assert unknown == set()


def test_load_mapping_rejects_unknown_type():
    with pytest.raises(ValueError, match="mapping_type must be one of"):
        load_mapping("readv2")


def test_icd_codes_match_by_prefix_ignoring_dots():
    df = pd.DataFrame(
        {"subject": ["s1"], "diagnosis_code_icd": ["I21.0"], "d": ["2024-01-01"]}
    )

    mapped = map_codes_to_comorbidities(
        df, code_col="diagnosis_code_icd", code_type="icd", date_col="d"
    )

    assert mapped["comorbidity"].tolist() == ["myocardial_infarction"]
    assert mapped["comorbidity_code_source"].tolist() == ["icd"]
    assert mapped["comorbidity_date"].tolist() == [pd.Timestamp("2024-01-01")]


def test_snomed_codes_match_exactly():
    df = pd.DataFrame(
        {"subject": ["s1", "s1"], "problem_code": ["95443002", "9544300"], "d": ["2024-01-01"] * 2}
    )

    mapped = map_codes_to_comorbidities(
        df, code_col="problem_code", code_type="snomed", date_col="d", source="problems"
    )

    assert mapped["comorbidity"].tolist() == ["peripheral_vascular_disease", pd.NA]
    assert mapped["comorbidity_code_source"].unique().tolist() == ["problems"]


def test_medication_names_match_case_insensitively():
    df = pd.DataFrame(
        {"subject": ["s1"], "medication_name_short": ["  ACLIDINIUM "], "d": ["2024-01-01"]}
    )

    mapped = map_codes_to_comorbidities(
        df, code_col="medication_name_short", code_type="medication", date_col="d"
    )

    assert mapped["comorbidity"].tolist() == ["chronic_pulmonary_disease"]


def test_multiple_matches_expand_into_separate_rows():
    df = pd.DataFrame({"subject": ["s1"], "code": ["E11"], "d": ["2024-01-01"]})
    mapping = pd.DataFrame(
        {"icd_code": ["E1", "E11"], "comorbidity": ["cond_a", "cond_b"]}
    )

    mapped = map_codes_to_comorbidities(
        df, code_col="code", code_type="icd", date_col="d", mapping_df=mapping
    )

    assert mapped["comorbidity"].tolist() == ["cond_a", "cond_b"]
    assert mapped["subject"].tolist() == ["s1", "s1"]


def test_custom_mapping_missing_columns_raises():
    df = pd.DataFrame({"subject": ["s1"], "code": ["E11"], "d": ["2024-01-01"]})
    bad_mapping = pd.DataFrame({"code": ["E11"], "comorbidity": ["x"]})

    with pytest.raises(ValueError, match="missing required columns"):
        map_codes_to_comorbidities(
            df, code_col="code", code_type="icd", date_col="d", mapping_df=bad_mapping
        )


def test_unknown_code_type_raises():
    df = pd.DataFrame({"subject": ["s1"], "code": ["x"], "d": ["2024-01-01"]})

    with pytest.raises(ValueError, match="code_type must be one of"):
        map_codes_to_comorbidities(df, code_col="code", code_type="readv2", date_col="d")
