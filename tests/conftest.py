"""Shared synthetic fixtures shaped like raw iCARE extracts.

Column names deliberately match the iCARE tables documented in
``docs/02-icare-source-tables-extraction.md`` so these tests exercise the
"works with exact iCARE column names" promise made in the README.
"""

import pandas as pd
import pytest


# Codes below are taken from the bundled mapping CSVs so the tests exercise the
# real lookups rather than a toy mapping.
ICD_MI_CODE = "I21.0"  # myocardial_infarction (prefix I21)
SNOMED_PVD_CODE = "95443002"  # peripheral_vascular_disease
MEDICATION_COPD = "Aclidinium"  # chronic_pulmonary_disease (stored lowercase)


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
    """Raw iCARE diagnoses table using ``spell_identifier``."""
    return pd.DataFrame(
        {
            "subject": ["s1"],
            "spell_identifier": ["A0"],
            "diagnosis_code_icd": [ICD_MI_CODE],
            "diagnosis_code_snomed": [None],
            "diagnosis_date": ["2024-01-01"],
        }
    )


@pytest.fixture
def raw_problems_df():
    return pd.DataFrame(
        {
            "SUBJECT": ["s1"],
            "PROBLEM_CODE": [SNOMED_PVD_CODE],
            "PROBLEM_DESC": ["Peripheral vascular disease"],
            "PROBLEM_DT_TM": ["2024-03-01"],
        }
    )


@pytest.fixture
def raw_prescriptions_df():
    return pd.DataFrame(
        {
            "subject": ["s1"],
            "medication_name_short": [MEDICATION_COPD],
            "order_dt_tm": ["2024-05-01"],
        }
    )
