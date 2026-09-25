"""Tests for spell-level feature building and CCI scoring."""

import pandas as pd
import pytest

from comorbidicare.features import CCI_COMORBIDITIES, build_comorbidity_features


def _evidence(subject, comorbidity, date):
    return pd.DataFrame(
        {
            "subject": [subject],
            "comorbidity": [comorbidity],
            "comorbidity_date": [date],
        }
    )


@pytest.fixture
def one_spell_cohort():
    return pd.DataFrame(
        {"subject": ["s1"], "spell_identifier": ["A1"], "admission_date": ["2025-02-01"]}
    )


def test_docs_example_gives_one_flag_and_score_of_one(one_spell_cohort):
    """Mirrors the worked example on the Features docs page."""
    evidence = _evidence("s1", "myocardial_infarction", "2025-01-01")

    features = build_comorbidity_features(
        one_spell_cohort,
        evidence_tables=[evidence],
        cutoff_col="admission_date",
        cci_score=True,
    )

    assert features.loc[0, "myocardial_infarction"] == 1
    assert features.loc[0, "cci_score"] == 1
    assert features[list(CCI_COMORBIDITIES)].sum().sum() == 1


def test_evidence_on_cutoff_date_is_excluded(one_spell_cohort):
    """Cutoff is strict: evidence dated exactly at the cutoff does not count."""
    evidence = _evidence("s1", "myocardial_infarction", "2025-02-01")

    features = build_comorbidity_features(
        one_spell_cohort, evidence_tables=[evidence], cutoff_col="admission_date"
    )

    assert features.loc[0, "myocardial_infarction"] == 0


def test_spells_without_evidence_get_zero_rows():
    cohort = pd.DataFrame(
        {"subject": ["s1", "s2"], "spell_identifier": ["A1", "B1"], "admission_date": ["2025-02-01"] * 2}
    )
    evidence = _evidence("s1", "dementia", "2024-01-01")

    features = build_comorbidity_features(
        cohort, evidence_tables=[evidence], cutoff_col="admission_date"
    )

    assert len(features) == 2
    s2 = features.set_index("subject").loc["s2"]
    assert s2[list(CCI_COMORBIDITIES)].sum() == 0


def test_cci_score_uses_most_severe_of_hierarchical_pair(one_spell_cohort):
    """Diabetes with complication (2) supersedes without (1): score 2, not 3.

    Both flags remain 1 so users can still see the underlying evidence.
    """
    evidence = pd.concat(
        [
            _evidence("s1", "diabetes_without_complication", "2024-01-01"),
            _evidence("s1", "diabetes_with_complication", "2024-01-01"),
        ]
    )

    features = build_comorbidity_features(
        one_spell_cohort, evidence_tables=[evidence], cutoff_col="admission_date", cci_score=True
    )

    assert features.loc[0, "diabetes_without_complication"] == 1
    assert features.loc[0, "diabetes_with_complication"] == 1
    assert features.loc[0, "cci_score"] == 2


def test_metastatic_tumour_outweighs_malignancy(one_spell_cohort):
    evidence = pd.concat(
        [
            _evidence("s1", "malignancy", "2024-01-01"),
            _evidence("s1", "metastatic_solid_tumor", "2024-01-01"),
        ]
    )

    features = build_comorbidity_features(
        one_spell_cohort, evidence_tables=[evidence], cutoff_col="admission_date", cci_score=True
    )

    assert features.loc[0, "cci_score"] == 6


def test_unrecognised_comorbidity_raises(one_spell_cohort):
    evidence = _evidence("s1", "gout", "2024-01-01")

    with pytest.raises(ValueError, match="unrecognised comorbidities"):
        build_comorbidity_features(
            one_spell_cohort, evidence_tables=[evidence], cutoff_col="admission_date"
        )


def test_missing_cutoff_date_raises():
    cohort = pd.DataFrame(
        {"subject": ["s1"], "spell_identifier": ["A1"], "admission_date": [None]}
    )
    evidence = _evidence("s1", "dementia", "2024-01-01")

    with pytest.raises(ValueError, match="missing or invalid"):
        build_comorbidity_features(
            cohort, evidence_tables=[evidence], cutoff_col="admission_date"
        )
