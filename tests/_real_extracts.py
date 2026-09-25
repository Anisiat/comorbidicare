"""Tests for the mess real extracts contain.

Each test below describes a shape of data seen when this package was run on
public hospital datasets (MIMIC-IV demo, Synthea). Clean synthetic fixtures
never trigger these, which is why they are grouped here.
"""

import pandas as pd

from comorbidicare.cleaning.clean_problems import clean_problems
from comorbidicare.features import build_comorbidity_features
from comorbidicare.mapping.map_code_to_comorbidity import map_codes_to_comorbidities


def test_float_typed_snomed_codes_still_match():
    """Snowflake returns a numeric column containing NULLs as float64.

    So a SNOMED concept arrives as 95443002.0. It must still match the
    mapping's 95443002, otherwise every problem-list flag is silently zero.
    """
    problems = pd.DataFrame(
        {
            "subject": ["s1", "s2"],
            "problem_code": [95443002.0, None],
            "problem_dt_tm": ["2024-01-01", "2024-01-01"],
        }
    )

    cleaned = clean_problems(problems)
    mapped = map_codes_to_comorbidities(
        cleaned, code_col="problem_code", code_type="snomed", date_col="problem_dt_tm"
    )

    assert cleaned["problem_code"].tolist() == ["95443002"]
    assert mapped["comorbidity"].dropna().tolist() == ["peripheral_vascular_disease"]


def test_timezone_aware_evidence_dates_are_accepted():
    """ISO timestamps with a Z suffix (UTC) are common in extracts.

    Comparing them with a plain admission date must work, not crash.
    """
    cohort = pd.DataFrame(
        {"subject": ["s1"], "spell_identifier": ["A1"], "admission_date": ["2025-02-01"]}
    )
    evidence = pd.DataFrame(
        {
            "subject": ["s1"],
            "comorbidity": ["dementia"],
            "comorbidity_date": ["2024-01-01T00:26:23Z"],
        }
    )

    features = build_comorbidity_features(
        cohort, evidence_tables=[evidence], cutoff_col="admission_date"
    )

    assert features.loc[0, "dementia"] == 1


def test_medication_names_match_inside_real_prescribing_strings():
    """Real prescribing text wraps the drug name in salt, strength and form.

    "Tiotropium bromide 18 microgram inhalation powder" is tiotropium and
    should count as chronic pulmonary disease evidence. A partial word such
    as "notgliclazidex" must not match.
    """
    prescriptions = pd.DataFrame(
        {
            "subject": ["s1", "s2"],
            "medication_name_short": [
                "Tiotropium bromide 18 microgram inhalation powder",
                "notgliclazidex 5mg",
            ],
            "d": ["2024-01-01", "2024-01-01"],
        }
    )

    mapped = map_codes_to_comorbidities(
        prescriptions, code_col="medication_name_short", code_type="medication", date_col="d"
    )

    by_subject = mapped.set_index("subject")["comorbidity"]
    assert by_subject["s1"] == "chronic_pulmonary_disease"
    assert pd.isna(by_subject["s2"])


def test_rows_with_no_code_are_dropped_from_the_evidence():
    """A missing code carries no evidence.

    In real extracts the SNOMED diagnosis column is ~95% empty. Keeping a row
    per empty value doubles the evidence table and inflates unmatched counts.
    """
    df = pd.DataFrame(
        {"subject": ["s1", "s2"], "code": ["I21.0", None], "d": ["2024-01-01"] * 2}
    )

    mapped = map_codes_to_comorbidities(df, code_col="code", code_type="icd", date_col="d")

    assert mapped["subject"].tolist() == ["s1"]
