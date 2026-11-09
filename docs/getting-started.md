# Get started

In this tutorial you will install `comorbidicare`, run it on a small made-up
dataset, and read the result. It takes about ten minutes.

You need Python 3.10 or newer and some familiarity with pandas DataFrames.

## 1. Install the package

=== "pip"

    ```bash
    pip install comorbidicare
    ```

=== "iCARE AVD (terminal)"

    ```bash
    pip install --trusted-host nexus.tde.imperial.nhs.uk --index-url http://nexus.tde.imperial.nhs.uk:8081/repository/pypi/simple/ comorbidicare
    ```

=== "iCARE AVD (notebook)"

    ```python
    %pip install \
        --trusted-host nexus.tde.imperial.nhs.uk \
        --index-url http://nexus.tde.imperial.nhs.uk:8081/repository/pypi/simple/ \
        comorbidicare
    ```

## 2. Make some example data

The package needs a **cohort** table: the patients and admissions (spells) you want to get comorbidities and CCI score for.
The example below has two patients, each with one admission:

```python
import pandas as pd

cohort = pd.DataFrame({
    "subject": ["p1", "p2"],
    "spell_identifier": ["s1", "s2"],
    "admission_date": ["2024-03-01", "2024-04-10"],
    "discharge_date": ["2024-03-05", "2024-04-12"],
})

print(f"Cohort:\n{cohort}")
```

```text
Cohort:
  subject spell_identifier admission_date discharge_date
0      p1               s1     2024-03-01     2024-03-05
1      p2               s2     2024-04-10     2024-04-12
```

It also needs **evidence**: records that might show a Charlson condition. We
make one small table of each type, all for patient `p1`:

```python
# Diagnoses: ICD-10 codes, one from last year and one from during the stay
diagnoses = pd.DataFrame({
    "subject": ["p1", "p1"],
    "diagnosis_code_icd": ["I21.0", "I50.9"],  # heart attack, heart failure
    "diagnosis_date": ["2023-01-15", "2024-03-03"],
})
print(f"Diagnoses:\n{diagnoses}\n")

# Problem list: a SNOMED CT code for diabetes
problems = pd.DataFrame({
    "subject": ["p1"],
    "problem_code": ["73211009"],
    "problem_dt_tm": ["2022-11-01"],
})
print(f"Problems:\n{problems}\n")

# Prescribing: an inhaler used for COPD
prescriptions = pd.DataFrame({
    "subject": ["p1"],
    "medication_name_short": ["Tiotropium"],
    "order_dt_tm": ["2023-06-01"],
})
print(f"Prescriptions:\n{prescriptions}")
```

```text
Diagnoses:
  subject diagnosis_code_icd diagnosis_date
0      p1              I21.0     2023-01-15
1      p1              I50.9     2024-03-03

Problems:
  subject problem_code problem_dt_tm
0      p1     73211009    2022-11-01

Prescriptions:
  subject medication_name_short order_dt_tm
0      p1            Tiotropium  2023-06-01
```

!!! info "The column names for each evidence table are the standard iCARE names, so the package finds them without any setup."

## 3. Build the comorbidity table

```python
from comorbidicare import build_comorbidity_table

features = build_comorbidity_table(
    cohort_df=cohort,
    diagnoses_df=diagnoses,
    problems_df=problems,
    prescriptions_df=prescriptions,
    cci_score=True,
)
print(features.T)  # transposed so all the columns fit on screen
```

```text
                                   0   1
subject                           p1  p2
spell_identifier                  s1  s2
myocardial_infarction              1   0
congestive_heart_failure           1   0
peripheral_vascular_disease        0   0
cerebrovascular_disease            0   0
dementia                           0   0
chronic_pulmonary_disease          1   0
rheumatic_disease                  0   0
peptic_ulcer_disease               0   0
mild_liver_disease                 0   0
diabetes_without_complication      1   0
diabetes_with_complication         0   0
hemiplegia_or_paraplegia           0   0
renal_disease                      0   0
malignancy                         0   0
moderate_or_severe_liver_disease   0   0
metastatic_solid_tumor             0   0
aids_hiv                           0   0
cci_score                          4   0
```

## 4. Read the result

`features` has **one row per admission**. (We printed it transposed, so here
each admission is a column.)

- **`p1`** has four conditions flagged, one from each piece of evidence: heart
  attack and heart failure from the diagnoses, diabetes from the problem list,
  and chronic pulmonary disease from the inhaler. Each is worth 1 point, so
  `cci_score` is 4.
- **`p2`** has no evidence at all, so every flag is `0` and the score is `0`.
  Admissions without evidence are still kept in the output.

!!! warning "Heart failure was recorded during the stay"

    `p1`'s heart failure code is dated 3 March, during their admission. It is
    flagged because the default cutoff is the discharge date. Section 5 shows
    how to exclude it with the admission cutoff.

## 5. Count only evidence from before the admission

By default, evidence counts if it is dated before **discharge**. The heart
failure code was recorded on 3 March, during `p1`'s stay, so it counted.

Run it again with `cutoff="admission"`:

```python
before_admission = build_comorbidity_table(
    cohort_df=cohort,
    diagnoses_df=diagnoses,
    problems_df=problems,
    prescriptions_df=prescriptions,
    cci_score=True,
    cutoff="admission",
)
print(before_admission[["subject", "congestive_heart_failure", "cci_score"]])
```

```text
  subject  congestive_heart_failure  cci_score
0      p1                         0          3
1      p2                         0          0
```

!!! info "Heart failure is no longer flagged and the score drops to 3, because that code was recorded after the admission started."

You have now built a comorbidity table from all three types of evidence, and
seen how the cutoff changes it. 😁

## Next steps

- [Extract the right iCARE tables](how-to/prepare-icare-tables)
- [How to choose between admission and discharge cutoff](explanation/pipeline-and-cutoff.md) 
- [Use a different table schema](how-to/rename-columns.md)
- [Run cleaning, mapping and CCI score steps individually](how-to/run-steps-separately.md)