# Input schema and pipeline

`build_comorbidity_table()` takes a cohort and one or more raw evidence tables,
and runs every step of the pipeline. This page lists the columns it reads.

```python
from comorbidicare import build_comorbidity_table
```

## Canonical fields

These are the column names the package expects, called **canonical names**.
Column names are matched after removing surrounding spaces and converting to
lower case. To use different names, see [Rename columns](../how-to/rename-columns.md).

Each table below is named by its `column_map` key.

<div class="schema-table schema-cohort" markdown>

### `cohort`

| Canonical field | Meaning | Status |
| --- | --- | --- |
| `subject` | Patient identifier | Required |
| `spell_identifier` | Spell identifier within patient | Required |
| `admission_date` | Admission date; admission cutoff and diagnosis date fallback | Required |
| `discharge_date` | Discharge date; default cutoff | Required |

</div>

<div class="schema-table schema-diagnoses" markdown>

### `diagnoses`

| Canonical field | Meaning | Status |
| --- | --- | --- |
| `subject` | Patient identifier | Required |
| `spell_identifier` | Spell, for the admission-date fallback | Optional; enables fallback |
| `diagnosis_code_icd` | ICD-10 diagnosis code | At least one diagnosis code field required |
| `diagnosis_code_snomed` | SNOMED CT diagnosis code | At least one diagnosis code field required |
| `diagnosis_date` | Recorded diagnosis date | Optional; falls back to admission date |
| `diagnosis_desc_icd` | ICD-10 description | Optional |
| `diagnosis_desc_snomed` | SNOMED CT description | Optional |

</div>

<div class="schema-table schema-problems" markdown>

### `problems`

| Canonical field | Meaning | Status |
| --- | --- | --- |
| `subject` | Patient identifier | Required |
| `problem_code` | SNOMED CT problem code | Required |
| `problem_dt_tm` | Problem evidence date | Required |
| `problem_desc` | Problem description | Optional |

</div>

<div class="schema-table schema-prescriptions" markdown>

### `prescriptions`

| Canonical field | Meaning | Status |
| --- | --- | --- |
| `subject` | Patient identifier | Required |
| `medication_name_short` | Medication name for lookup | Required |
| `order_dt_tm` | Medication evidence date | Required |

</div>

Other columns in your tables are kept but not used.

Only the date column chosen by `cutoff` must have a valid date on every row.
Each patient and spell must have one cutoff date. For how the cutoff, date
fallback and date parsing work, see
[Pipeline and cutoff](../explanation/pipeline-and-cutoff.md).

## Errors

The pipeline raises a `ValueError` when:

- no evidence table is given, or the cohort is empty
- a required field is missing (the message names the table and suggests `column_map`)
- `column_map` names an unknown table or field, maps two fields to the same
  column, or names a column that isn't in the table
- `cutoff` is not `"admission"` or `"discharge"`

## Functions

::: comorbidicare.pipeline.build_comorbidity_table
    options:
      heading_level: 3

::: comorbidicare.schema.standardise_columns
    options:
      heading_level: 3
