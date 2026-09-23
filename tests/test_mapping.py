"""Tests for the bundled lookups and code-to-comorbidity mapping."""

import pandas as pd
import pytest

from comorb_icare.features import CCI_COMORBIDITIES
from comorb_icare.mapping._loaders import load_mapping
from comorb_icare.mapping.map_code_to_comorbidity import map_codes_to_comorbidities
from comorb_icare.mapping.map_code_to_comorbidity import _get_icd_prefixes, _match_icd_code

@pytest.mark.parametrize(
    ("mapping_type", "code_column"),
    [
        ("icd", "icd_code"),
        ("snomed", "snomed_code"),
        ("medication", "medication_name"),
    ],
)
def test_bundled_mappings_load_and_have_expected_schema(mapping_type, code_column):
    mapping = load_mapping(mapping_type)

    assert isinstance(mapping, pd.DataFrame)
    assert {"comorbidity", code_column} <= set(mapping.columns)
    assert not mapping.empty
    assert mapping[code_column].dtype == "string"

def test_invalid_code_type_raises():
    df = pd.DataFrame({"subject": [1], "code": ["A"], "date": ["2020-01-01"]})
    with pytest.raises(ValueError, match="code_type must be one of"):
        map_codes_to_comorbidities(df, "code", "invalid_code_type", date_col="date")



@pytest.mark.parametrize('missing_column', ['subject', 'code', 'date'])
def test_missing_required_columns_raise(missing_column):
    df = pd.DataFrame({"subject": [1], "code": ["A"], "date": ["2020-01-01"]})
    df = df.drop(columns=[missing_column])
    with pytest.raises(ValueError, match=f"df must contain '{missing_column}' column."):
        map_codes_to_comorbidities(df, "code", "icd", date_col="date")


def test_mapping_code_is_retained_and_source_is_set():
    raw = pd.DataFrame({"subject": ["P"], "code": ["I21"], "date": ["2020-01-01"]})
    result = map_codes_to_comorbidities(raw, "code", "icd", date_col="date", source="test_source")
    assert result.loc[0, "comorbidity_code_value"] == "I21"
    assert result.loc[0, "comorbidity_code_source"] == "test_source"
    assert result.loc[0, "comorbidity_date"] == pd.Timestamp("2020-01-01")

def test_mapping_with_user_df():
    mapping_df = pd.DataFrame({
        "icd_code": ["I21", "I22"],
        "comorbidity": ["myocardial_infarction", "myocardial_infarction"]
    })
    raw = pd.DataFrame({"subject": ["P"], "code": ["I21"], "date": ["2020-01-01"]})
    result = map_codes_to_comorbidities(raw, "code", "icd", date_col="date", mapping_df=mapping_df)
    assert result.loc[0, "comorbidity"] == "myocardial_infarction"

def test_user_mapping_required_columns_validation():
    mapping_df = pd.DataFrame({
        "icd_code": ["I21", "I22"],
        # Missing 'comorbidity' column
    })
    raw = pd.DataFrame({"subject": ["P"], "code": ["I21"], "date": ["2020-01-01"]})
    with pytest.raises(ValueError, match="Provided mapping DataFrame is missing required columns"):
        map_codes_to_comorbidities(raw, "code", "icd", date_col="date", mapping_df=mapping_df)

def test_get_icd_prefixes_and_match_icd_code():
    mapping_df = pd.DataFrame({
        "icd_code": ["I21", "I22"],
        "comorbidity": [
            "myocardial_infarction",
            "myocardial_infarction",
        ],
    })

    prefixes = _get_icd_prefixes(mapping_df)

    assert prefixes == [
        ("I21", "myocardial_infarction"),
        ("I22", "myocardial_infarction"),
    ]

    assert _match_icd_code("I21.9", prefixes) == [
        "myocardial_infarction"
    ]

    assert _match_icd_code("I22.0", prefixes) == [
        "myocardial_infarction"
    ]

    assert _match_icd_code("I23", prefixes) == []


def test_exact_codes_are_matched_for_snomed():
    mapping_df = pd.DataFrame({
        "snomed_code": ["123456789012345678", "987654321098765432"],
        "comorbidity": ["renal_disease", "dementia"]
    })

    df = pd.DataFrame({
        "subject": ["P1", "P2", "P3"],
        "date": ["2020-01-01", "2020-01-01", "2020-01-01"],
        "code": ["123456789012345678", " 987654321098765432 ", "000000000000000000"]
    })

    result = map_codes_to_comorbidities(df, "code", "snomed", date_col="date", mapping_df=mapping_df)

    assert result.loc[0, "comorbidity"] == "renal_disease"
    assert result.loc[1, "comorbidity"] == "dementia"
    assert pd.isna(result.loc[2, "comorbidity"])

def test_exact_codes_are_matched_for_medication():
    mapping_df = pd.DataFrame({
        "medication_name": ["ACLIDINIUM", "metformin"],
        "comorbidity": ["chronic_pulmonary_disease", "diabetes"]
    })

    df = pd.DataFrame({
        "subject": ["P1", "P2", "P3"],
        "date": ["2020-01-01", "2020-01-01", "2020-01-01"],
        "code": ["aclidinium", "  METFORMIN ", "UNKNOWN"]
    })

    result = map_codes_to_comorbidities(df, "code", "medication", date_col="date", mapping_df=mapping_df)

    assert result.loc[0, "comorbidity"] == "chronic_pulmonary_disease"
    assert result.loc[1, "comorbidity"] == "diabetes"
    assert pd.isna(result.loc[2, "comorbidity"])


@pytest.mark.parametrize(
    "code_type, code, expected_comorbidity",
    [
        ("icd", "I21.9", "myocardial_infarction"),
        ("snomed", "194781004", "congestive_heart_failure"),
        ("medication", "aclidinium", "chronic_pulmonary_disease"),
    ],
)
def test_mapping_with_various_code_types(code_type, code, expected_comorbidity):
    df = pd.DataFrame({
        "subject": ["P1"],
        "date": ["2020-01-01"],
        "code": [code]
    })

    result = map_codes_to_comorbidities(df, "code", code_type, date_col="date")

    assert result.loc[0, "comorbidity"] == expected_comorbidity

def test_code_matches_multiple_comorbidities():
    mapping_df = pd.DataFrame({
        "snomed_code": ["194781004", "194781004"],
        "comorbidity": ["congestive_heart_failure", "renal_disease"]
    })

    df = pd.DataFrame({
        "subject": ["P1"],
        "date": ["2020-01-01"],
        "code": ["194781004"]
    })

    result = map_codes_to_comorbidities(df, "code", "snomed", date_col="date", mapping_df=mapping_df)

    assert result.shape[0] == 2
    assert set(result["comorbidity"]) == {"congestive_heart_failure", "renal_disease"}


@pytest.mark.parametrize("mapping_type", ["icd", "snomed", "medication"])
def test_bundled_mappings_only_use_known_comorbidities(mapping_type):
    """Every label in the CSVs must be one the scorer knows how to weight."""
    mapping = load_mapping(mapping_type)

    unknown = set(mapping["comorbidity"].dropna()) - set(CCI_COMORBIDITIES)

    assert unknown == set()

@pytest.mark.parametrize("mapping_type", ["icd", "snomed"])
def test_mappings_have_all_cci_comorbidities(mapping_type):
    """Every CCI comorbidity must be represented in the bundled mappings."""
    mapping = load_mapping(mapping_type)

    missing = set(CCI_COMORBIDITIES) - set(mapping["comorbidity"].dropna())

    assert missing == set()


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

def test_snomed_codes_match_exactly():
    df = pd.DataFrame(
        {"subject": ["s1", "s1"], "problem_code": ["95443002", "9544300"], "d": ["2024-01-01"] * 2}
    )

    mapped = map_codes_to_comorbidities(
        df, code_col="problem_code", code_type="snomed", date_col="d", source="problems"
    )

    assert mapped["comorbidity"].tolist() == ["peripheral_vascular_disease", pd.NA]
    assert mapped["comorbidity_code_source"].unique().tolist() == ["problems"]




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
