import pandas as pd
from comorbidicare.pipeline import build_comorbidity_table

def create_test_data():
    # Create synthetic cohort data
    cohort = pd.DataFrame({
        "subject": [101, 102],
        "spell_identifier": [1001, 1002],
        "admission_date": ["2026-01-01", "2026-01-01"],
        "discharge_date": ["2026-01-10", "2026-01-10"],
    })

    diagnoses = pd.DataFrame({
        "subject_id": [101, 102],
        "code": ["K27.0", "I50.9"], # ICD-10: type 2 diabetes, heart failure
        "date": ["2026-01-01", "2026-01-02"],
    })

    problems = pd.DataFrame({
        "patient": [101, 102],
        "problem": ["44054006", "84114007"],  # SNOMED: type 2 diabetes, heart failure
        "start_date": ["2026-01-01", "2026-01-02"],
    })  

    prescriptions = pd.DataFrame({
        "patient_id": [101, 102],
        "medication": ["tiotropium", "Furosemide"], # Medication names for type 2 diabetes and heart failure
        "start_date": ["2026-01-01", "2026-01-02"],
    })

    column_mapping = {
        "diagnoses": {
            "subject": "subject_id",
            "diagnosis_code_icd": "code",
            "diagnosis_date": "date",
        },
        "prescriptions": {
            "subject": "patient_id",
            "medication_name_short": "medication",
            "order_dt_tm": "start_date",
        },
        "problems": {
            "subject": "patient",
            "problem_code": "problem",
            "problem_dt_tm": "start_date",
        }
    }

    return cohort, diagnoses, prescriptions, problems, column_mapping


def run_smoke_test():
    cohort, diagnoses, prescriptions, problems, column_mapping = create_test_data()

    features = build_comorbidity_table(
        cohort_df=cohort,
        diagnoses_df=diagnoses,
        prescriptions_df=prescriptions,
        problems_df=problems,
        column_map=column_mapping,
        cci_score = True
    )
    # Basic checks
    assert isinstance(features, pd.DataFrame)
    assert len(features) == 2
    assert not features.empty

    print(features)
    print("✅ comorbidicare smoke test passed!")
    return features

def main():
    run_smoke_test()

if __name__ == "__main__":

    # comorbidity_table = main()
    comorbidity_table = run_smoke_test()
    print(comorbidity_table.loc[:, comorbidity_table.eq(1).any(axis=0)])

  