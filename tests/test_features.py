import pandas as pd
import pytest

from comorbidicare.features import build_comorbidity_features
from comorbidicare.features import CCI_COMORBIDITIES, CCI_WEIGHTS


@pytest.fixture
def one_spell_cohort():
    return pd.DataFrame(
        {
            "subject": ["s1"],
            "spell_identifier": ["A1"],
            "discharge_date": ["2025-02-01"],
        }
    )


@pytest.fixture
def cohort():
    return pd.DataFrame(
        {
            "subject": ["s1", "s2"],
            "spell_identifier": ["A1", "B1"],
            "discharge_date": ["2022-01-01", "2027-01-01"],
        }
    )

@pytest.fixture
def diagnoses():
    return pd.DataFrame(
        {
            "subject": ["s1"],
            "comorbidity": ["renal_disease"],
            "comorbidity_date": ["2023-01-01"],
            'other_column': [1],
        })

@pytest.fixture
def problems():
    return pd.DataFrame(
        {
            "subject": ["s1"],
            "comorbidity": ["renal_disease"],
            "comorbidity_date": ["2026-02-01"]
        })

@pytest.fixture
def medications():
    return pd.DataFrame(
        {
            "subject": ["s1", "s2"],
            "comorbidity": ["renal_disease", "aids_hiv"],
            "comorbidity_date": ["2025-01-01", "2025-01-01"]
        }
    )


@pytest.mark.parametrize(
    "missing_column",
    [
        "subject",
        "spell_identifier",
        'discharge_date',
    ],
)
def test_raises_if_required_cohort_column_missing(missing_column, cohort_df):
    cohort = cohort_df.drop(columns=missing_column)

    evidence = pd.DataFrame(
        {
            "subject": [1],
            "comorbidity": ["renal_disease"],
            "comorbidity_date": ["2025-01-01"],
        }
    )

    with pytest.raises(ValueError, match="missing required columns"):
        build_comorbidity_features(
            cohort_df=cohort,
            evidence_tables=[evidence],
        )

def test_features_require_canonical_columns(cohort_df, diagnoses):
    renamed = cohort_df.rename(columns={"subject": "patient_id"})
    with pytest.raises(ValueError, match="missing required columns.*subject"):
        build_comorbidity_features(renamed, [diagnoses])


def test_features_signature_uses_fixed_schema():
    import inspect

    assert list(inspect.signature(build_comorbidity_features).parameters) == [
        "cohort_df", "evidence_tables", "cci_score", "cutoff_col",
    ]


def test_raises_if_no_evidence_tables(cohort_df):
    with pytest.raises(
        ValueError,
        match="At least one comorbidity evidence table is required",
    ):
        build_comorbidity_features(
            cohort_df=cohort_df,
            evidence_tables=[],

        )

def test_raises_if_evidence_table_missing_required_columns(cohort_df):
    evidence = pd.DataFrame(
        {
            "subject": [1],
            "comorbidity": ["renal_disease"],
        }
    )

    with pytest.raises(ValueError, match="missing required columns"):
        build_comorbidity_features(
            cohort_df=cohort_df,
            evidence_tables=[evidence],
        )

@pytest.mark.filterwarnings('ignore')
def test_invalid_cutoff_date_in_cohort(cohort_df):
    cohort = cohort_df.copy()
    cohort.loc[0, "discharge_date"] = "invalid_date"

    evidence = pd.DataFrame(
        {
            "subject": ["s1"],
            "comorbidity": ["renal_disease"],
            "comorbidity_date": ["2025-01-01"],
        }
    )

    with pytest.raises(
        ValueError,
        match="cohort_df contains missing or invalid values in 'discharge_date'",
    ):
        build_comorbidity_features(
            cohort_df=cohort,
            evidence_tables=[evidence],
        )

def test_no_comorbidities_after_cutoff(cohort, diagnoses, problems, medications):

    cohort = cohort.copy()
    diagnoses = diagnoses.copy()
    problems = problems.copy()
    medications = medications.copy()

    result = build_comorbidity_features(
        cohort_df=cohort,
        evidence_tables=[diagnoses, problems, medications],
    )

    assert len(result) == 2
    assert result.loc[1, "subject"] == "s2"
    assert result.loc[1, "spell_identifier"] == "B1"
    assert result.loc[1, 'aids_hiv'] == 1
    assert result.loc[0, list(CCI_WEIGHTS)].sum() == 0  # No comorbidities for subject s1 after cutoff


def test_comorbidity_features_output_structure(cohort, diagnoses, problems, medications):

    result = build_comorbidity_features(
        cohort_df=cohort,
        evidence_tables=[diagnoses, problems, medications],
    )

    expected_columns = ["subject", "spell_identifier"] + list(CCI_WEIGHTS)
    assert list(result.columns) == expected_columns



def test_comorbidity_empty_cohort_df_output_structure(diagnoses, problems, medications):

    cohort = pd.DataFrame(columns=["subject", "spell_identifier", "discharge_date"])

    result = build_comorbidity_features(
        cohort_df=cohort,
        evidence_tables=[diagnoses, problems, medications],
    )
    expected_columns = ["subject", "spell_identifier"] + list(CCI_WEIGHTS)
    assert list(result.columns) == expected_columns


def test_cci_score_calculation(cohort, diagnoses, problems, medications):

    result = build_comorbidity_features(
        cohort_df=cohort,
        evidence_tables=[diagnoses, problems, medications],
        cci_score = True
    )

    # Calculate expected CCI score for subject s2
    expected_cci_score_s2 = 6

    assert result.loc[result["subject"] == "s2", "cci_score"].values[0] == expected_cci_score_s2

def test_no_cci_score_when_flag_false(cohort, diagnoses, problems, medications):

    result = build_comorbidity_features(
        cohort_df=cohort,
        evidence_tables=[diagnoses, problems, medications],
        cci_score = False
    )

    assert "cci_score" not in result.columns

def test_cci_score_hierarchy():

    # Add a comorbidity that should override another for subject s1
    diagnoses = pd.DataFrame(
        {
            "subject": ["s1", 's1'],
            "comorbidity": ["diabetes_with_complication", "diabetes_without_complication"],
            "comorbidity_date": ["2025-01-01", "2025-01-01"],
        }
    )

    cohort = pd.DataFrame(
        {
            "subject": ["s1"],
            "spell_identifier": ["A1"],
            "discharge_date": ["2025-06-01"],
        }
    )

    result = build_comorbidity_features(
        cohort_df=cohort,
        evidence_tables=[diagnoses],
        cci_score=True
    )

    expected_cci_score = 2

    assert result.loc[0, "cci_score"] == expected_cci_score


def test_unknown_comorbidity_in_evidence_raises_warning(cohort_df):

    evidence = pd.DataFrame(
        {
            "subject": ["s1"],
            "comorbidity": ["unknown_comorbidity"],
            "comorbidity_date": ["2025-01-01"],
        }
    )

    with pytest.raises(ValueError, match="unknown"):
        build_comorbidity_features(
            cohort_df=cohort_df,
            evidence_tables=[evidence],
        )

def test_multiple_spells_per_subject_use_own_cutoff_dates():

    cohort = pd.DataFrame(
        {
            "subject": ["s1", "s1"],
            "spell_identifier": ["A1", "A2"],
            "discharge_date": ["2025-01-01", "2025-06-01"],
        }
    )

    evidence = pd.DataFrame(
        {
            "subject": ["s1"],
            "comorbidity": ["renal_disease"],
            "comorbidity_date": ["2025-03-01"],
        }
    )

    result = build_comorbidity_features(
        cohort_df=cohort,
        evidence_tables=[evidence],
    )

    assert result.loc[result["spell_identifier"] == "A1", "renal_disease"].values[0] == 0
    assert result.loc[result["spell_identifier"] == "A2", "renal_disease"].values[0] == 1



def test_spells_without_evidence_get_zero_rows():
    cohort = pd.DataFrame(
        {"subject": ["s1", "s2"], "spell_identifier": ["A1", "B1"], "discharge_date": ["2025-02-01"] * 2}
    )
    evidence = pd.DataFrame(
        {"subject": ["s1"], "comorbidity": ["myocardial_infarction"], "comorbidity_date": ["2025-01-01"]}
    )

    features = build_comorbidity_features(
        cohort, evidence_tables=[evidence]
    )

    assert len(features) == 2
    s2 = features.set_index("subject").loc["s2"]
    assert s2[list(CCI_COMORBIDITIES)].sum() == 0


def test_metastatic_tumour_outweighs_malignancy(one_spell_cohort):
    evidence = pd.DataFrame(
        {
            "subject": ["s1", "s1"],
            "comorbidity": ["malignancy", "metastatic_solid_tumor"],
            "comorbidity_date": ["2024-01-01", "2024-01-01"],
        }
    )
    features = build_comorbidity_features(
        one_spell_cohort, evidence_tables=[evidence], cci_score=True
    )

    assert features.loc[0, "cci_score"] == 6


@pytest.mark.parametrize("cutoff_col", ["admission_date", "discharge_date", "index_date"])
def test_selected_cutoff_excludes_equal_and_later_evidence(cutoff_col):
    cohort = pd.DataFrame({"subject": ["s1"], "spell_identifier": ["A1"], cutoff_col: ["2025-01-02"]})
    evidence = pd.DataFrame({
        "subject": ["s1"] * 3,
        "comorbidity": ["dementia", "renal_disease", "aids_hiv"],
        "comorbidity_date": ["2025-01-01", "2025-01-02", "2025-01-03"],
    })
    result = build_comorbidity_features(cohort, [evidence], cutoff_col=cutoff_col)
    assert result.loc[0, "dementia"] == 1
    assert result.loc[0, "renal_disease"] == 0
    assert result.loc[0, "aids_hiv"] == 0


def test_missing_selected_cutoff(cohort_df, diagnoses):
    with pytest.raises(ValueError, match="missing required columns.*index_date"):
        build_comorbidity_features(cohort_df, [diagnoses], cutoff_col="index_date")


def test_invalid_selected_cutoff(cohort_df, diagnoses):
    cohort = cohort_df.assign(admission_date=None)
    with pytest.raises(ValueError, match="missing or invalid values in 'admission_date'"):
        build_comorbidity_features(cohort, [diagnoses], cutoff_col="admission_date")
