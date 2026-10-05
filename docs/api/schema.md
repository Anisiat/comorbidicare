# Input schema and pipeline

`build_comorbidity_table()` accepts a cohort and one or more raw evidence tables.
It standardises column names before cleaning, mapping, and feature building.
Existing iCARE names need no configuration, including uppercase source columns.

```python
from comorbidicare.pipeline import build_comorbidity_table

features = build_comorbidity_table(
    cohort_df=cohort,
    diagnoses_df=diagnoses,
    prescriptions_df=prescriptions,
    problems_df=problems,
    cci_score=True,
)
```

## Partial overrides

Pass a nested `column_map` using **canonical name → input column name**:

```python
features = build_comorbidity_table(
    cohort_df=cohort.rename(columns={"subject": "patient_id"}),
    diagnoses_df=diagnoses.rename(columns={"diagnosis_code_icd": "icd10"}),
    column_map={
        "cohort": {"subject": "patient_id"},
        "diagnoses": {"diagnosis_code_icd": "icd10"},
    },
)
```

Each table's unspecified fields retain their default names. The adapter copies
inputs and strips/lowercases column names, as the cleaners already do. It does
not guess aliases. Identifiers must still refer to the same patients and spells
across tables; renaming columns does not translate identifier values.

## Canonical raw fields

| Table | Canonical field | Meaning | Status |
| --- | --- | --- | --- |
| cohort | `subject` | Patient identifier | Required |
| cohort | `spell_identifier` | Spell identifier within patient | Required |
| cohort | `admission_date` | Admission date; optional cutoff choice and diagnosis fallback | Required |
| cohort | `discharge_date` | Discharge date; default evidence cutoff | Required |
| diagnoses | `subject` | Patient identifier | Required |
| diagnoses | `spell_identifier` | Spell for admission-date lookup | Optional; enables fallback |
| diagnoses | `diagnosis_code_icd` | ICD-10 diagnosis code | At least one diagnosis code field required |
| diagnoses | `diagnosis_code_snomed` | SNOMED diagnosis code | At least one diagnosis code field required |
| diagnoses | `diagnosis_date` | Recorded diagnosis date | Optional; falls back to admission date |
| diagnoses | `diagnosis_desc_icd` | ICD diagnosis description | Optional |
| diagnoses | `diagnosis_desc_snomed` | SNOMED diagnosis description | Optional |
| diagnoses | `admission_date` | Existing admission date | Optional; replaced by cohort dates |
| prescriptions | `subject` | Patient identifier | Required |
| prescriptions | `medication_name_short` | Medication name for lookup | Required |
| prescriptions | `order_dt_tm` | Medication evidence date | Required |
| problems | `subject` | Patient identifier | Required |
| problems | `problem_code` | SNOMED problem code | Required |
| problems | `problem_dt_tm` | Problem evidence date | Required |
| problems | `problem_desc` | Problem description | Optional |

When diagnoses include spell identifiers, the pipeline supplies cohort admission
dates to diagnosis cleaning, replacing any admission dates already in diagnoses.
Missing diagnosis dates use the matched admission date. Without spell identifiers,
only recorded diagnosis dates are used.

All listed fields can be mapped. Other raw columns are retained but do not need
mapping because the package does not interpret them. Derived fields such as
`comorbidity_date` are created downstream and are not raw-input mapping keys.

Missing required fields produce an error naming the table and suggesting
`column_map`. Unknown tables or canonical fields, duplicate input assignments,
missing explicitly mapped inputs (even optional ones), and column collisions
also raise errors. Cleaner validation of values and dates remains in place.

## Breaking API change

Column-name configuration is now exclusively through `column_map` at the input
boundary. The pipeline no longer accepts `subject_col`, `spell_col`,
`admission_date_col`, or `cutoff_col`. There are no aliases or deprecation shims.
Output identifiers are always `subject` and `spell_identifier`.

`build_comorbidity_features` requires canonical patient, spell and evidence names.
Its `subject_col`, `spell_col`, `comorbidity_col`, and `comorbidity_date_col`
arguments have been removed. It retains `cutoff_col` to select the cohort date
used for temporal filtering.
Package-created fields such as `comorbidity`, `comorbidity_date`, and `cci_score`
are fixed. Direct callers must supply canonical tables.

The mapper retains `code_col` and `date_col` because they select different
canonical fields for different source types, rather than configuring the schema.

## Admission or discharge cutoff

The pipeline defaults to `cutoff="discharge"`. Set `cutoff="admission"` to use
admission dates instead. This selects between canonical dates after schema
adaptation; custom raw names still belong in `column_map`.

```python
features = build_comorbidity_table(
    cohort_df=cohort,
    diagnoses_df=diagnoses,
    cutoff="admission",
)
```

Both date columns remain part of the required cohort schema. Only the selected
cutoff must contain valid, non-missing cutoff values. Evidence must be strictly
before that date: same-time evidence is excluded, including diagnoses whose
inferred evidence date equals admission when using an admission cutoff.

For direct feature building, use
`build_comorbidity_features(cohort, evidence, cutoff_col="admission_date")`.
Its default is `cutoff_col="discharge_date"`; direct callers may also select
another cohort date column. Patient, spell, and derived evidence names stay fixed.

::: comorbidicare.schema.standardise_columns

::: comorbidicare.pipeline.build_comorbidity_table

## Dates and identifiers

Dates are parsed individually, allowing mixed date/time formats. Timezone-aware
values are converted to UTC; timezone-naive values are treated as UTC. Cleaned
dates are returned as timezone-naive UTC timestamps. Localise local-clock dates
to their correct timezone before passing them in if offsets matter.

Patient and spell identifiers are normalised to strings, including numeric IDs,
while textual leading zeros are preserved. Cohort identifiers must be present,
and each patient/spell must have one consistent selected cutoff date.

Integer-valued SNOMED codes such as `95443002.0` are normalised for exact matching.
Supply large identifiers and SNOMED codes as strings to avoid precision loss
already introduced by floating-point storage; cleaning cannot recover lost digits.
