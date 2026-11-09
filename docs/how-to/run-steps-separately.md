# Run the steps separately

`build_comorbidity_table()` runs cleaning, mapping and feature building in one
call. Run the steps yourself when you want to:

- look at the evidence behind each flag (which code, from which table, on
  which date)
- use your own mapping table instead of a bundled one
- clean or map only some of your tables

Each step's functions are imported from their own module.

## 1. Clean each table

```python
import pandas as pd
from comorbidicare.cleaning.clean_diagnoses import clean_diagnoses
from comorbidicare.cleaning.clean_prescriptions import clean_prescriptions

cohort = pd.DataFrame({
    "subject": ["p1"],
    "spell_identifier": ["s1"],
    "admission_date": ["2024-03-01"],
    "discharge_date": ["2024-03-05"],
})
diagnoses = pd.DataFrame({
    "subject": ["p1"],
    "diagnosis_code_icd": ["I21.0"],
    "diagnosis_date": ["2023-01-15"],
})
prescriptions = pd.DataFrame({
    "subject": ["p1"],
    "medication_name_short": ["Saxagliptin"],
    "order_dt_tm": ["2023-06-01"],
})

clean_dx = clean_diagnoses(diagnoses)
clean_rx = clean_prescriptions(prescriptions)
```

The cleaners need canonical column names. If yours differ, rename them first
with `DataFrame.rename(columns=...)`.

### What cleaning changes

Cleaning tidies codes and converts dates from text into real dates. Here is a
small, messy diagnoses table before and after:

```python
raw_dx = pd.DataFrame({
    "subject": ["p1", "p1", "p2"],
    "spell_identifier": ["s1", "s1", "s2"],
    "diagnosis_code_icd": [" i21.0", "I50.9", "E11.9"],  # stray space, lower case, dot
    "diagnosis_date": ["2023-01-15", "not a date", None],
})
print(raw_dx.dtypes["diagnosis_date"])

cleaned = clean_diagnoses(raw_dx)
print(cleaned.dtypes["diagnosis_date"])
print(cleaned[["diagnosis_code_icd", "diagnosis_date", "comorbidity_date"]])
```

```text
object
datetime64[ns]
  diagnosis_code_icd diagnosis_date comorbidity_date
0               I210     2023-01-15       2023-01-15
1               I509            NaT              NaT
2               E119            NaT              NaT
```

- **Codes** are stripped of spaces, upper-cased and have their dots removed
  (`" i21.0"` becomes `"I210"`).
- **Dates** change from text (`object`) to a real date type (`datetime64`), so
  they can be compared with the cutoff. A date that is missing or can't be read
  (`"not a date"`) becomes `NaT`, pandas' "not a time" marker. The row is
  kept, but without a date it can't count as evidence.
- **`comorbidity_date`** is a new column holding the best date for each row.

!!! note
    pandas 2.3 shows the date type as `datetime64[ns]`. pandas 3 may show a
    different time unit, such as `datetime64[us]`. Both are real dates.

### Fill missing diagnosis dates from the admission date

Two of the three rows above have no usable date. If a diagnosis belongs to a
spell, the spell's admission date is a reasonable stand-in. Pass the cohort's
spell dates to `clean_diagnoses`:

```python
spells = pd.DataFrame({
    "subject": ["p1", "p2"],
    "spell_identifier": ["s1", "s2"],
    "admission_date": ["2024-03-01", "2024-04-10"],
})

filled = clean_diagnoses(raw_dx, spell_admission_dates_df=spells)
print(filled[["diagnosis_code_icd", "diagnosis_date", "comorbidity_date", "comorbidity_date_source"]])
```

```text
  diagnosis_code_icd diagnosis_date comorbidity_date comorbidity_date_source
0               I210     2023-01-15       2023-01-15          diagnosis_date
1               I509            NaT       2024-03-01    spell_admission_date
2               E119            NaT       2024-04-10    spell_admission_date
```

`comorbidity_date` uses the diagnosis date when there is one and the admission
date when there isn't. `comorbidity_date_source` records which was used, so you
can always tell a real date from a filled-in one. The diagnoses table must
include `spell_identifier`.

!!! warning "Filled dates are approximate"
    A diagnosis given the admission date is treated as recorded on that day. With
    `cutoff="admission"`, evidence dated exactly on the cutoff is excluded, so
    these rows won't count. With the default discharge cutoff, they will.

## 2. Map codes to Charlson conditions

Mapping is a lookup: it turns each code (or medicine name) into the Charlson
condition it stands for, using the bundled code lists.

`map_codes_to_comorbidities` works for every source, so you tell it which
column to read (`code_col`), which matching rule and code list to use
(`code_type`) and which column holds the date (`date_col`). These three are
required. `source` (a label for the output) and `mapping_df` (your own code
list, see step 3) are optional. See the
[reference](../api/mapping.md#comorbidicare.mapping.map_code_to_comorbidity.map_codes_to_comorbidities)
for full details.

Map each code column separately. The arguments for each source are:

| Source | `code_col` | `code_type` | `date_col` |
|---|---|---|---|
| Diagnoses, ICD-10 | `diagnosis_code_icd` | `"icd"` | `comorbidity_date` |
| Diagnoses, SNOMED CT | `diagnosis_code_snomed` | `"snomed"` | `comorbidity_date` |
| Problems | `problem_code` | `"snomed"` | `problem_dt_tm` |
| Prescriptions | `medication_name_short` | `"medication"` | `order_dt_tm` |

```python
from comorbidicare.mapping.map_code_to_comorbidity import map_codes_to_comorbidities

dx_evidence = map_codes_to_comorbidities(
    clean_dx,
    code_col="diagnosis_code_icd",
    code_type="icd",
    date_col="comorbidity_date",
    source="diagnoses",
)
```

`build_comorbidity_table()` makes these same calls for you, once for each code
column in the tables you pass in.

### What mapping produces

Here is a small diagnoses table with three ICD-10 codes, and what mapping
returns for it:

```python
example_dx = pd.DataFrame({
    "subject": ["p1", "p1", "p2"],
    "diagnosis_code_icd": ["I21.0", "J44.9", "R51"],  # heart attack, COPD, headache
    "diagnosis_date": ["2023-01-15", "2023-05-02", "2023-03-01"],
})

example_evidence = map_codes_to_comorbidities(
    clean_diagnoses(example_dx),
    code_col="diagnosis_code_icd",
    code_type="icd",
    date_col="comorbidity_date",
    source="diagnoses",
)
print(example_evidence.to_string())
```

```text
  subject comorbidity_code_value comorbidity_code_source                comorbidity comorbidity_date
0      p1                   I210               diagnoses      myocardial_infarction       2023-01-15
1      p1                   J449               diagnoses  chronic_pulmonary_disease       2023-05-02
2      p2                    R51               diagnoses                       <NA>       2023-03-01
```

The result is an **evidence table**, with one row per piece of evidence:

| Column | Contains |
|---|---|
| `subject` | The patient |
| `comorbidity_code_value` | The code that was looked up, as cleaned |
| `comorbidity_code_source` | Where it came from: the `source` label, or the `code_type` if you didn't give one |
| `comorbidity` | The Charlson condition, or `<NA>` if the code isn't on the list |
| `comorbidity_date` | The evidence date, taken from `date_col` |

- **Every input row is kept.** `R51` (headache) isn't a Charlson condition, so
  its `comorbidity` is `<NA>`. It is ignored when the features are built.
- **A code that matches two conditions gets two rows**, one for each.
- **Every evidence table has these same five columns**, whatever the source.
  That's what lets step 4 combine diagnoses, problems and prescriptions.

## 3. Optional: use your own mapping table

Pass `mapping_df` to use a different mapping. The easiest way is to start from
a bundled one with `load_mapping`. This example adds saxagliptin, a diabetes
medicine that isn't in the bundled list:

```python
from comorbidicare.mapping import load_mapping

medication_mapping = pd.concat([
    load_mapping("medication"),
    pd.DataFrame({
        "comorbidity": ["diabetes_without_complication"],
        "medication_name": ["saxagliptin"],
    }),
], ignore_index=True)

rx_evidence = map_codes_to_comorbidities(
    clean_rx,
    code_col="medication_name_short",
    code_type="medication",
    date_col="order_dt_tm",
    source="prescriptions",
    mapping_df=medication_mapping,
)
```

A mapping table needs a `comorbidity` column and one code column: `icd_code`,
`snomed_code` or `medication_name`. Condition names must be one of the 17
condition names listed under [Scoring](../explanation/methodology.md#scoring).

!!! warning "A custom mapping changes your results"
    Your scores will no longer match other users of the package. Record
    what you changed and why, and report it in your methods.

## 4. Build the features

Feature building turns the evidence tables into the final table: **one row per
spell** in the cohort, with a `0`/`1` column for each of the 17 conditions and,
if you ask for it, `cci_score`. This is the same table `build_comorbidity_table()`
returns, because the pipeline ends with this same step.

Pass all your evidence tables together, as a list:

```python
from comorbidicare.features import build_comorbidity_features

features = build_comorbidity_features(
    cohort,
    evidence_tables=[dx_evidence, rx_evidence],
    cci_score=True,
)
print(features[["subject", "myocardial_infarction", "diabetes_without_complication", "cci_score"]])
```

```text
  subject  myocardial_infarction  diabetes_without_complication  cci_score
0      p1                      1                              1          2
```

To use the admission date as the cutoff, add `cutoff_col="admission_date"`.

### What feature building does

Take the evidence table from [What mapping produces](#what-mapping-produces):
a heart attack code (January 2023) and a COPD code (May 2023) for `p1`, and a
headache code with no Charlson condition for `p2`. Now give `p1` two
admissions, one before the COPD code and one after:

```python
example_cohort = pd.DataFrame({
    "subject": ["p1", "p1", "p2"],
    "spell_identifier": ["s1", "s2", "s3"],
    "admission_date": ["2023-03-01", "2024-03-01", "2024-04-10"],
    "discharge_date": ["2023-03-04", "2024-03-05", "2024-04-12"],
})

example_features = build_comorbidity_features(
    example_cohort,
    evidence_tables=[example_evidence],
    cci_score=True,
)
print(example_features[["subject", "spell_identifier", "myocardial_infarction",
                        "chronic_pulmonary_disease", "cci_score"]].to_string())
```

```text
  subject spell_identifier  myocardial_infarction  chronic_pulmonary_disease  cci_score
0      p1               s1                      1                          0          1
1      p1               s2                      1                          1          2
2      p2               s3                      0                          0          0
```

Going from the long evidence table to this wide table, feature building:

1. **Combines** all the evidence tables into one.
2. **Drops evidence with no condition.** The headache row (`<NA>`) is ignored.
3. **Keeps only evidence dated before each spell's cutoff.** This is done
   separately for every spell, so the same patient can have different flags
   on different admissions. The COPD code (May 2023) comes after `s1`
   (March 2023), so it only counts for `s2`.
4. **Turns conditions into columns:** `1` if there is any evidence for that
   condition, otherwise `0`. Several pieces of evidence for one condition
   still give `1`.
5. **Keeps every spell in the cohort.** `p2` has no usable evidence, so `s3`
   gets all `0`s rather than being left out. Evidence for patients who aren't
   in the cohort is ignored.
6. **Adds `cci_score`** if `cci_score=True`. See
   [Scoring](../explanation/methodology.md#scoring).

The evidence tables are where you can see *which* code caused a flag. The
feature table only says *whether* a condition is present.
