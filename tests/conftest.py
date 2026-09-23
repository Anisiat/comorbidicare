"""Shared synthetic fixtures shaped like raw iCARE extracts.

Raw source fixtures include all fields documented in
``docs/02-icare-source-tables-extraction.md`` so these tests exercise the
"works with exact iCARE column names" promise made in the README. Raw
column names are uppercase to match iCARE extracts.
"""

import pandas as pd
import pytest


# Codes below are taken from the bundled mapping CSVs so the tests exercise the
# real lookups rather than a toy mapping.
ICD_MI_CODE = "I21.0"  # myocardial_infarction (prefix I21)
SNOMED_PVD_CODE = "95443002"  # peripheral_vascular_disease
MEDICATION_COPD = "Aclidinium"  # chronic_pulmonary_disease (stored lowercase)


@pytest.fixture(params = [None, "", " ", "N/A", "na", "null", "none"])
def missing_value(request):
    """Parametrized fixture for missing values."""
    return request.param

@pytest.fixture
def cohort_df():
    """Two subjects, one spell each. Subject s2 has no evidence anywhere."""
    return pd.DataFrame(
        {
            "subject": ["s1", "s2"],
            "spell_identifier": ["A1", "B1"],
            "admission_date": ["2025-06-01", "2025-06-01"],
            "discharge_date": ["2025-06-05", "2025-06-05"],
        }
    )


@pytest.fixture
def raw_diagnoses_df():
    """Raw iCARE diagnoses table using ``SPELL_IDENTIFIER``."""
    return pd.DataFrame(
        {
            "SUBJECT": ["s1"],
            "SPELL_IDENTIFIER": ["A0"],
            "ENCNTR_ID": ["E0"],
            "EPISODE_IDENTIFIER": ["EP0"],
            "DIAGNOSIS_CODE_ICD": [ICD_MI_CODE],
            "DIAGNOSIS_CODE_SNOMED": [None],
            "DIAGNOSIS_DESC_ICD": ["Acute myocardial infarction"],
            "DIAGNOSIS_DESC_SNOMED": [None],
            "DIAGNOSIS_DATE": ["2024-01-01"],
            "DIAGNOSIS_SEQ_N": [1],
            "ORDER_NO_OF_EPISODE": [1],
            "UPDATE_DT_TM": ["2024-01-02"],
        }
    )


@pytest.fixture
def raw_problems_df():
    return pd.DataFrame(
        {
            "SUBJECT": ["s1"],
            "ENCNTR_ID": ["E1"],
            "PROBLEM_CODE": [SNOMED_PVD_CODE],
            "PROBLEM_DESC": ["Peripheral vascular disease"],
            "PROBLEM_DT_TM": ["2024-03-01"],
            "UPDATE_DT_TM": ["2024-03-02"],
        }
    )


@pytest.fixture
def raw_prescriptions_df():
    """Three distinct prescription orders for subject s1."""
    return pd.DataFrame(
        {
            "SUBJECT": ["s1", "s1", "s1"],
            "ENCNTR_ID": ["E2", "E3", "E4"],
            "ORDER_ID": ["O1", "O2", "O3"],
            "ADMISSION_MEDICINE_Y_N": ["Y", "Y", "Y"],
            "GP_TO_CONTINUE": ["Y", "Y", "Y"],
            "MEDICATION_NAME_CLEANED": [MEDICATION_COPD, MEDICATION_COPD, MEDICATION_COPD],
            "MEDICATION_NAME_SHORT": [MEDICATION_COPD, MEDICATION_COPD, MEDICATION_COPD],
            "ORDERED_DOSE_CLEAN": [None, None, None],
            "ORDERED_DRUG_FORM": [None, None, None],
            "ORDERED_FREQUENCY": [None, None, None],
            "ORDERED_ROUTE": [None, None, None],
            "ORDERED_UNIT": [None, None, None],
            "ORDER_DT_TM": ["2024-05-01", "2024-05-03", "2024-05-05"],
            "ORDER_TYPE": [None, None, None],
            "PRESCRIPTION_TYPE": [None, None, None],
            "THERAPEUTICAL_CLASS": [None, None, None],
            "UPDATE_DT_TM": ["2024-05-02", "2024-05-04", "2024-05-06"],
        }
    )
