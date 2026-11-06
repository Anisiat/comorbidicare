<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Anisiat/comorbidicare/main/docs/assets/logo-dark.svg">
    <img src="https://raw.githubusercontent.com/Anisiat/comorbidicare/main/docs/assets/logo.svg" alt="comorbidicare" width="420">
  </picture>
</p>

# comorbidicare: a Python tool for deriving comorbidity information and CCI scores from iCARE data

[![PyPI](https://img.shields.io/pypi/v/comorbidicare)](https://pypi.org/project/comorbidicare/)
[![Python](https://img.shields.io/pypi/pyversions/comorbidicare)](https://pypi.org/project/comorbidicare/)
[![Tests](https://github.com/Anisiat/comorbidicare/actions/workflows/tests.yaml/badge.svg)](https://github.com/Anisiat/comorbidicare/actions/workflows/tests.yaml)
[![Docs](https://github.com/Anisiat/comorbidicare/actions/workflows/docs.yaml/badge.svg)](https://anisiat.github.io/comorbidicare/)
[![Licence: MIT](https://img.shields.io/github/license/Anisiat/comorbidicare)](https://github.com/Anisiat/comorbidicare/blob/main/LICENSE)

**Derive the 17 Charlson comorbidities and the Charlson Comorbidity Index (CCI)
for hospital admissions, from iCARE clinical data.**

[Documentation](https://anisiat.github.io/comorbidicare/) ·
[Source code](https://github.com/Anisiat/comorbidicare) ·
[Report a problem](https://github.com/Anisiat/comorbidicare/issues)

## Table of contents

- [What is it?](#what-is-it)
- [Main features](#main-features)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Input tables and column names](#input-tables-and-column-names)
- [Output](#output)
- [Evidence cutoff](#evidence-cutoff)
- [How codes are mapped and scored](#how-codes-are-mapped-and-scored)
- [Documentation](#documentation)
- [Getting help and contributing](#getting-help-and-contributing)
- [Licence](#licence)

## What is it?

**comorbidicare** is a Python package that cleans iCARE tables containing
comorbidity information, standardises their column names and formats, and maps
clinical codes to the 17 Charlson comorbidities. From these it builds one row
per hospital admission (*spell*), with a yes/no flag for each comorbidity and,
optionally, the Charlson Comorbidity Index (CCI) score. Only evidence recorded
before each admission's cutoff date is counted.

The package takes a **cohort table**, which lists the admissions you want to
score (one row per spell, with the subject, spell identifier, admission date
and discharge date), and one or more of these **iCARE evidence tables**:

| Table | Evidence used |
|---|---|
| Diagnoses | ICD-10 and SNOMED CT codes |
| Problems | SNOMED CT problem-list codes |
| Prescribing | Medication names, for selected conditions |

It works on pandas DataFrames and does not connect to a database. Extract the
iCARE tables first (for example from Snowflake), then pass them to the package.

## Main features

- Works with any combination of the three evidence tables
- Copes with missing fields, e.g. diagnoses without SNOMED codes or dates;
  undated diagnoses fall back to the spell's admission date when a
  `spell_identifier` is present
- Standard iCARE column names work as-is; other names can be mapped with
  `column_map`
- Choice of evidence cutoff: before discharge (default) or before admission
- Optional weighted CCI score (no age adjustment)
- Never changes your input DataFrames; it works on copies

## Installation

Requires Python 3.10 or later and pandas 2.3 or later (pandas 3 is supported).

```bash
pip install comorbidicare
```

## Quick start

Copy and run this example. It uses made-up data, with all three evidence tables.

```python
import pandas as pd
from comorbidicare import build_comorbidity_table

# One admission (spell) to score
cohort = pd.DataFrame({
    "subject": ["p1"],
    "spell_identifier": ["s1"],
    "admission_date": ["2024-03-01"],
    "discharge_date": ["2024-03-05"],
})

# Evidence recorded before that admission, one row per table
diagnoses = pd.DataFrame({
    "subject": ["p1"],
    "diagnosis_code_icd": ["I21.0"],          # ICD-10: myocardial infarction
    "diagnosis_date": ["2023-01-15"],
})
problems = pd.DataFrame({
    "subject": ["p1"],
    "problem_code": ["73211009"],             # SNOMED CT: diabetes mellitus
    "problem_dt_tm": ["2022-11-01"],
})
prescriptions = pd.DataFrame({
    "subject": ["p1"],
    "medication_name_short": ["Tiotropium"],  # COPD inhaler
    "order_dt_tm": ["2023-06-01"],
})

features = build_comorbidity_table(
    cohort_df=cohort,
    diagnoses_df=diagnoses,
    problems_df=problems,
    prescriptions_df=prescriptions,
    cci_score=True,
)
print(features.T)  # transposed so the 17 flags fit on screen
```

Output:

```text
                                   0
subject                           p1
spell_identifier                  s1
myocardial_infarction              1
congestive_heart_failure           0
peripheral_vascular_disease        0
cerebrovascular_disease            0
dementia                           0
chronic_pulmonary_disease          1
rheumatic_disease                  0
peptic_ulcer_disease               0
mild_liver_disease                 0
diabetes_without_complication      1
diabetes_with_complication         0
hemiplegia_or_paraplegia           0
renal_disease                      0
malignancy                         0
moderate_or_severe_liver_disease   0
metastatic_solid_tumor             0
aids_hiv                           0
cci_score                          3
```

The sample data is one patient (`p1`) with one admission (1–5 March 2024).
Each evidence table holds one record from before that admission: a heart
attack ICD-10 code in diagnoses, a diabetes SNOMED CT code in the problem
list, and a COPD inhaler in prescribing. Each maps to a different Charlson
condition, so `p1` gets three flags and a CCI score of 1 + 1 + 1 = 3.

`features` has one row per admission. Any one evidence table is enough; pass
only the ones you have.

## Input tables and column names

The evidence tables are the raw iCARE tables that hold comorbidity
information (diagnoses, problems and prescribing), passed as pandas DataFrames
without any prior cleaning. They can contain other columns as well; these are
kept during processing but not used.

| Table | Required columns | Optional columns |
|---|---|---|
| Cohort | `subject`, `spell_identifier`, `admission_date`, `discharge_date` | |
| Diagnoses | `subject`, and at least one of `diagnosis_code_icd` or `diagnosis_code_snomed` | `spell_identifier`, `diagnosis_date`, `diagnosis_desc_icd`, `diagnosis_desc_snomed` |
| Problems | `subject`, `problem_code`, `problem_dt_tm` | `problem_desc` |
| Prescribing | `subject`, `medication_name_short`, `order_dt_tm` | |

Column names are stripped and lowercased, so `SUBJECT` and `subject` are the
same. If your columns have other names, pass `column_map`, which maps
**canonical name → your column name**, separately for `cohort`, `diagnoses`,
`prescriptions` and `problems`:

```python
# Your tables use some different names:
#   my_cohort:    patient_id         (instead of subject)
#   my_diagnoses: patient_id, icd10  (instead of subject, diagnosis_code_icd)
features = build_comorbidity_table(
    cohort_df=my_cohort,
    diagnoses_df=my_diagnoses,
    column_map={
        "cohort":    {"subject": "patient_id"},
        "diagnoses": {"subject": "patient_id", "diagnosis_code_icd": "icd10"},
    },
)
```

The output uses the canonical names (`subject`, not `patient_id`).

Fields you do not list keep their default names, and no column names are
guessed. Renaming columns does not translate identifier values: subjects and
spells must be identified the same way in every table. See the
[input schema reference](https://anisiat.github.io/comorbidicare/api/schema/)
for full details and validation rules.

## Output

`build_comorbidity_table()` returns a DataFrame with **one row per subject and
spell**, using canonical column names:

| Column | Description |
|---|---|
| `subject`, `spell_identifier` | Identify the admission |
| 17 comorbidity columns | `1` if there is evidence before the cutoff, otherwise `0` |
| `cci_score` | Weighted CCI score; only present when `cci_score=True` |

The 17 comorbidity columns, with their CCI weights:

| Weight | Comorbidities |
|---:|---|
| 1 | `myocardial_infarction`, `congestive_heart_failure`, `peripheral_vascular_disease`, `cerebrovascular_disease`, `dementia`, `chronic_pulmonary_disease`, `rheumatic_disease`, `peptic_ulcer_disease`, `mild_liver_disease`, `diabetes_without_complication` |
| 2 | `diabetes_with_complication`, `hemiplegia_or_paraplegia`, `renal_disease`, `malignancy` |
| 3 | `moderate_or_severe_liver_disease` |
| 6 | `metastatic_solid_tumor`, `aids_hiv` |

When both a mild and a severe form are present (diabetes, liver disease,
malignancy), only the more severe one counts towards `cci_score`. Both flags
stay in the output.

## Evidence cutoff

Only evidence dated **strictly before** the cutoff counts; evidence exactly on
the cutoff date is excluded.

| `cutoff` | Evidence counted | Trade-off |
|---|---|---|
| `"discharge"` (default) | Before discharge, including codes recorded during the stay | Captures long-standing conditions first coded during the admission, but can also include conditions that began during the stay |
| `"admission"` | Before admission only | Avoids conditions that began during the stay (important for prediction models), but misses long-standing conditions first coded during the admission |

Choose based on your research question, and report which cutoff you used.

```python
features = build_comorbidity_table(cohort, diagnoses_df=diagnoses, cutoff="admission")
```

For example, with the quick-start admission (1–5 March 2024), a prescription
dated 3 March 2024 was recorded during the stay: it is counted with
`cutoff="discharge"` but not with `cutoff="admission"`.

## How codes are mapped and scored

- **ICD-10** codes are uppercased with dots removed, then matched by prefix
  (`I50.9` matches `I50`). All matching conditions are kept, not only the most
  specific. Mappings are based on
  [Quan et al. (2005)](https://doi.org/10.1097/01.mlr.0000182534.19832.83).
- **SNOMED CT** codes are matched exactly, using codelists based on
  [Fortin et al. (2022)](https://doi.org/10.1186/s12911-022-02006-1),
  with clinically inappropriate assignments removed.
- **Medication names** give supporting evidence only, for chronic pulmonary
  disease and diabetes without complication. They do not show severity or
  complications.
- **Scoring** uses the standard Charlson weights above, with no age adjustment.

The mapping files are in `src/comorbidicare/data/`. See the
[mapping methodology](https://anisiat.github.io/comorbidicare/01-CCI-mapping-methodology/)
for sources and reasoning. If you are a clinician and would like to help review
the medication mappings, please get in touch.

## Documentation

Full documentation is at <https://anisiat.github.io/comorbidicare/>, including
the [input schema](https://anisiat.github.io/comorbidicare/api/schema/) and the
[mapping methodology](https://anisiat.github.io/comorbidicare/01-CCI-mapping-methodology/).

## Getting help and contributing

Questions, bug reports and suggestions are welcome as
[GitHub issues](https://github.com/Anisiat/comorbidicare/issues). To work on
the code:

```bash
git clone https://github.com/Anisiat/comorbidicare.git
cd comorbidicare
python -m pip install -e ".[dev]"
python -m pytest
```

Please use only synthetic data in tests, docs and examples.

## Licence

[MIT](https://github.com/Anisiat/comorbidicare/blob/main/LICENSE)
