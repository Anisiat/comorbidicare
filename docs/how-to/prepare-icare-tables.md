# Prepare iCARE tables

This guide shows which iCARE tables and columns to extract from Snowflake ❄️, and how to pass them into `build_comorbidity_table()`.

## 1. Choose your evidence tables

You can use any combination of these three tables. Each adds evidence the others may miss.

| Table | iCARE name | Evidence it gives |
|---|---|---|
| Diagnoses | `icare_episodes_diagnosis_anon` | ICD-10 and SNOMED CT diagnosis codes from inpatient episodes |
| Problems | `icare_problems_anon` | SNOMED CT codes from the problem list |
| Prescribing | `icare_pharmacy_prescribing_anon` | Medication names (only includes two conditions) |

## 2. Extract the columns the package uses

You only need these columns. Leave out large description fields if your
extract is too big.

**Diagnoses**

- `subject`
- `diagnosis_code_icd` and/or `diagnosis_code_snomed` (at least one)
- `diagnosis_date`
- `spell_identifier` (recommended: see below)

**Problems**

- `subject`
- `problem_code`
- `problem_dt_tm`

**Prescribing**

- `subject`
- `medication_name_short`
- `order_dt_tm`

!!! tip "Keep `spell_identifier` in the diagnoses table"
    Many iCARE diagnoses have missing `diagnosis_date`. When `spell_identifier` is
    present, a missing date is filled with that spell's admission date from
    the cohort table. Without it, diagnoses with no date can't be used.

## 3. Build the cohort table

The cohort table is the anchor and lists the patient admissions you want to score or get comorbidity information for, one row per spell:

| Column | Meaning |
|---|---|
| `subject` | Patient identifier, the same values as in the evidence tables |
| `spell_identifier` | Spell (admission) identifier |
| `admission_date` | Date of admission |
| `discharge_date` | Date of discharge |

## 4. Load the tables into pandas and run the pipeline

The package works on pandas DataFrames and does not connect to Snowflake ❄️.
Export each table, read it into a DataFrame, then pass it to the pipeline function `build_comorbidity_table`.

```python
import pandas as pd
from comorbidicare import build_comorbidity_table

cohort = pd.read_csv("cohort.csv")
diagnoses = pd.read_csv("diagnoses.csv", dtype={"diagnosis_code_snomed": str})
problems = pd.read_csv("problems.csv", dtype={"problem_code": str})

features = build_comorbidity_table(
    cohort_df=cohort,
    diagnoses_df=diagnoses,
    problems_df=problems,
    cci_score=True,
)
```

!!! warning "Read SNOMED CT codes as text"
    SNOMED CT codes can be up to 18 digits long. If pandas reads them as
    numbers, the last digits can be lost and the codes no longer match. Use
    `dtype={...: str}` as above.

Column names are matched without regard to case or surrounding spaces, so
`SUBJECT` works as well as `subject`. 

!!! info "Different column names"
    If your columns have different names,
    see [Rename columns](rename-columns.md).

## Reference: all fields in the iCARE tables

These lists show every field in each table, including the ones the package
doesn't use.

??? note "Diagnoses: `icare_episodes_diagnosis_anon`"
    - `subject`: pseudonymised patient identifier
    - `spell_identifier`: unique inpatient spell identifier
    - `encntr_id`: pseudonymised inpatient encounter ID
    - `episode_identifier`: unique inpatient episode identifier
    - `diagnosis_code_icd`: inpatient ICD diagnosis code
    - `diagnosis_code_snomed`: inpatient SNOMED diagnosis code
    - `diagnosis_desc_icd`: ICD diagnosis description
    - `diagnosis_desc_snomed`: SNOMED diagnosis description
    - `diagnosis_date`: date of diagnosis
    - `diagnosis_seq_n`: diagnosis sequence; `1 = primary`
    - `order_no_of_episode`: sequential episode number within a spell
    - `update_dt_tm`: date/time of data refresh

??? note "Problems: `icare_problems_anon`"
    - `subject`: pseudonymised patient identifier
    - `encntr_id`: pseudonymised encounter ID
    - `problem_code`: SNOMED problem code
    - `problem_desc`: problem description
    - `problem_dt_tm`: date/time the problem was recorded
    - `update_dt_tm`: date/time of data refresh

??? note "Prescribing: `icare_pharmacy_prescribing_anon`"
    - `subject`: pseudonymised patient identifier
    - `encntr_id`: pseudonymised encounter ID
    - `order_id`: prescription/order identifier
    - `admission_medicine_y_n`: whether the patient was admitted on the drug
    - `gp_to_continue`: whether the GP should continue the drug after discharge
    - `medication_name_cleaned`: cleaned medication name
    - `medication_name_short`: shortened medication name
    - `ordered_dose_clean`: prescribed dose
    - `ordered_drug_form`: drug formulation
    - `ordered_frequency`: prescribed frequency
    - `ordered_route`: prescribed route
    - `ordered_unit`: prescribed unit
    - `order_dt_tm`: prescription date/time
    - `order_type`: order type
    - `prescription_type`: prescription type
    - `therapeutical_class`: drug class
    - `update_dt_tm`: date/time of data refresh -->


## Next steps

- [How to choose between admission and discharge cutoff](../explanation/pipeline-and-cutoff.md)
- [Run cleaning, mapping and CCI score steps individually](run-steps-separately.md)
- [Rename columns](rename-columns.md)