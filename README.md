# comorbidicare

`comorbidicare` is a Python package for deriving Charlson Comorbidity Index (CCI) features from routinely collected iCARE clinical data.

## Overview

The package uses information from up to three iCARE tables:

- diagnoses
- problems
- prescribing

It identifies the 17 Charlson comorbidities using:

- ICD-10 diagnosis codes
- SNOMED CT codes
- medication evidence for selected conditions

Evidence from these sources is standardised to a common set of CCI comorbidity labels, reconciled across sources, and can then be used to calculate the Charlson Comorbidity Index.

The package is intended to support both:

- lower-level use, where users clean, map, reconcile, or score data step-by-step
- higher-level use, where users provide one or more iCARE tables and receive derived comorbidities and CCI scores directly

Standard iCARE column names work by default. For renamed input columns, supply optional `column_map` overrides to `build_comorbidity_table()`.


## Input column names

```python
from comorbidicare.pipeline import build_comorbidity_table

# Raw tables with default iCARE column names; any one evidence source is enough.
features = build_comorbidity_table(
    cohort_df=cohort,
    diagnoses_df=diagnoses,
    prescriptions_df=prescriptions,
    problems_df=problems,
    cci_score=True,
)

# Only these columns have different names; all other defaults still apply.
features = build_comorbidity_table(
    cohort_df=cohort.rename(columns={"subject": "patient_id"}),
    diagnoses_df=diagnoses.rename(columns={"diagnosis_code_icd": "icd10"}),
    column_map={
        "cohort": {"subject": "patient_id"},
        "diagnoses": {"diagnosis_code_icd": "icd10"},
    },
)
```

Mappings use **canonical name → input column name**, separately for `cohort`,
`diagnoses`, `prescriptions`, and `problems`. Unspecified fields retain their
defaults. Column names are stripped and lowercased, preserving existing iCARE
normalisation; no column names are guessed. Inputs are copied, and outputs use
canonical names when using `column_map` alone.

See [the input schema reference](docs/api/schema.md) for supported columns,
validation rules, and migration from the removed `*_col` arguments.

**Breaking change:** column-name configuration now uses only `column_map`.
The pipeline no longer accepts `subject_col`, `spell_col`, `admission_date_col`,
or `cutoff_col`; outputs always use canonical names. Feature building also
requires canonical names for patient, spell, comorbidity and evidence date.
Its `cutoff_col` argument selects the cohort date used for filtering.

The pipeline defaults to `cutoff="discharge"`. Use `cutoff="admission"` to
include only evidence strictly before admission instead. The switch selects
canonical dates after `column_map` is applied; evidence exactly at the cutoff
is excluded. Both cohort date columns are still required.

## Intended use

The package is designed for iCARE-derived clinical data and provides reusable comorbidity features for downstream clinical research and analysis.

Users may provide one, two, or all three supported source tables depending on data availability.

The package does not connect directly to Snowflake. Users are expected to extract the relevant iCARE data and pass the resulting pandas DataFrames to the package.


## Outputs

The package is intended to return two main outputs.

### Evidence table

A long-format table containing the comorbidity evidence identified for each subject:

| subject | comorbidity | evidence_source | code | date |
|---|---|---|---|---|

This preserves the provenance of each inferred comorbidity.

### CCI feature table

A wide-format subject-level table containing:

- binary indicators for the 17 Charlson comorbidities
- the calculated CCI score
- optionally, only the overall score if individual comorbidity flags are not required

Example structure:

| subject | diabetes | heart_failure | ... | cci_score |
|---|---:|---:|---|---:|

## Example data completeness

The following missingness values were observed in one cleaned development sample and are included only as an illustration of data availability.

They should not be interpreted as fixed characteristics of the full iCARE dataset.

### Diagnoses

| Column | Missing (%) |
|---|---:|
| `subject` | 0.0 |
| `spell_identifier` | 0.0 |
| `diagnosis_date` | 95.0 |
| `diagnosis_code_icd` | 3.8 |
| `diagnosis_code_snomed` | 95.6 |

### Prescribing

| Column | Missing (%) |
|---|---:|
| `subject` | 0.0 |
| `medication_name_short` | 0.0 |
| `order_dt_tm` | 0.0 |

### Problems

| Column | Missing (%) |
|---|---:|
| `subject` | 0.0 |
| `problem_code` | 2.4 |
| `problem_desc` | 0.1 |
| `problem_dt_tm` | 0.0 |

These patterns motivate a package design that does not require all coding systems or date fields to be present.

In particular:

- ICD-10 diagnosis evidence should remain usable when SNOMED diagnosis codes are missing
- diagnosis dates should be treated as optional where appropriate
- problem-list and prescribing dates can provide additional temporal information
- different evidence sources should be retained separately before reconciliation

## Development roadmap

Remaining work includes:

- optional age-adjusted CCI scoring where age is provided
- reviewing overlapping ICD-10 prefixes in the mapping table to confirm whether retaining all matching comorbidities, rather than only the most specific match, is intentional
