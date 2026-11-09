# Rename columns

Use this when your tables use different column names from the standard iCARE
names, for example `patient_id` instead of `subject`.

## 1. Find the package's name for each column

The package's own names are called **canonical names** and are the default iCARE column names. They are listed in the
[input schema](../api/schema.md#canonical-fields). Make a note of each
column in your tables whose name is different.

You don't need to do anything for:

- columns that already use the canonical name
- differences in case or surrounding spaces (`SUBJECT`, ` subject ` and
  `subject` are treated as the same)

## 2. Build and pass a `column_map`

`column_map` is a dictionary with one entry per table. Inside each table,
write **canonical name → your column name**:

```python
import pandas as pd
from comorbidicare import build_comorbidity_table

my_cohort = pd.DataFrame({
    "patient_id": ["p1"],
    "spell_identifier": ["s1"],
    "admission_date": ["2024-03-01"],
    "discharge_date": ["2024-03-05"],
})
my_diagnoses = pd.DataFrame({
    "patient_id": ["p1"],
    "icd10": ["I21.0"],
    "diagnosis_date": ["2023-01-15"],
})

features = build_comorbidity_table(
    cohort_df=my_cohort,
    diagnoses_df=my_diagnoses,
    column_map={
        "cohort": {"subject": "patient_id"},
        "diagnoses": {"subject": "patient_id", "diagnosis_code_icd": "icd10"},
    },
    cci_score=True,
)
print(features[["subject", "spell_identifier", "myocardial_infarction", "cci_score"]])
```

```text
  subject spell_identifier  myocardial_infarction  cci_score
0      p1               s1                      1          1
```

!!! info "Only list the columns that differ"

    The table names are `"cohort"`, `"diagnoses"`, `"problems"` and
    `"prescriptions"`. Every column you don't list keeps its standard name.

The output always uses the canonical names, so the result has a `subject`
column, not `patient_id`. Your input DataFrames are not changed.

## If you get an error

If a required column is missing, the error names the table and suggests
`column_map`:

```text
ValueError: cohort is missing required columns: ['subject']. Supply canonical
names or column_map['cohort'] with canonical_name: input_column_name entries.
```

You also get an error if `column_map`:

- uses a table or canonical name the package doesn't know (often a typo)
- points two canonical names at the same column
- names a column that isn't in your table

!!! note "Renaming columns does not translate values"
    `column_map` only changes which column is read. The identifiers in
    `subject` and `spell_identifier` must still refer to the same patients and
    spells across all your tables.

## Next steps

- [How to choose between admission and discharge cutoff](../explanation/pipeline-and-cutoff.md)
- [Run cleaning, mapping and CCI score steps individually](run-steps-separately.md)