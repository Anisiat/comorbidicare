# Mapping methodology

This page explains where the code lists come from, what was changed from the
published versions and why, and how the score is calculated. Use it when you
describe the method in a paper.

## Three kinds of evidence

A comorbidity can be recorded in several ways in iCARE: as an ICD-10
code on an inpatient episode, as a SNOMED CT code on a diagnosis or the
problem list, or indirectly through a medicine the patient takes. The package
uses all three, and flags a condition if **any** of them shows it before the
cutoff. Using several sources finds conditions that a single table would
miss, especially long-standing ones that aren't recoded at every admission.

## ICD-10

ICD-10 codes are mapped using the coding algorithm in:

**Quan et al. (2005).** *Coding algorithms for defining comorbidities in
ICD-9-CM and ICD-10 administrative data.* Medical Care 43(11):1130–1139.
[doi:10.1097/01.mlr.0000182534.19832.83](https://doi.org/10.1097/01.mlr.0000182534.19832.83)

The code list is stored as **prefixes**. A recorded code counts if it starts
with a prefix: `I50.9` matches `I50` (heart failure). Codes are compared in
upper case with the dots removed, so `i50.9`, `I50.9` and `I509` are the same.

If a code matches prefixes for more than one condition, all of them are kept.
In the bundled list no two conditions share a prefix, and a test checks this.

## SNOMED CT

SNOMED CT codes are mapped using Additional File 1 of:

**Fortin et al. (2022).** *Adaptation and validation of a coding algorithm for
the Charlson Comorbidity Index in administrative claims data using the SNOMED
CT standardized vocabulary.* BMC Medical Informatics and Decision Making
22:261. [doi:10.1186/s12911-022-02006-1](https://doi.org/10.1186/s12911-022-02006-1)

This includes the
[2023 correction](https://doi.org/10.1186/s12911-023-02205-4) to the moderate
or severe liver disease list. Codes must match exactly.

Two code–condition pairs from Fortin's list are left out on purpose. In both
cases Fortin lists the code under two conditions, and the second one doesn't
fit:

| Code | Meaning | Kept under | Left out of | Reason |
|---|---|---|---|---|
| `372087000` | Primary malignant neoplasm | `malignancy` | `metastatic_solid_tumor` | A primary cancer is not necessarily metastatic; keeping it would score 6 instead of 2 |
| `713571008` | Disorder of central nervous system co-occurrent with HIV infection | `aids_hiv` | `dementia` | A CNS disorder alongside HIV is not necessarily dementia |

## Medication evidence

The medication list was put together for this package; it is not from a
published codelist. Medicines are only included when they point fairly
specifically to one condition:

- **Chronic pulmonary disease:** long-acting inhalers, for example
  tiotropium, umeclidinium and budesonide-formoterol.
- **Diabetes without complication:** gliclazide and the gliptins (alogliptin,
  linagliptin, sitagliptin).

!!! note "Medication evidence is supportive only"
    A prescription suggests a condition but doesn't confirm it, and it says
    nothing about severity or complications. That is why medicines are
    only used for two conditions, and only for their mildest category.

If you [run the steps separately](../how-to/run-steps-separately.md), each
evidence row keeps its source table, so you can check which flags come only
from medication evidence.

!!! question "Are you a clinician? Help improve the medication list"
    Medication evidence currently covers only two conditions. If you think
    other medicines point specifically enough to a Charlson condition to be
    useful evidence, or that a medicine on the list shouldn't be there,
    please [open an issue](https://github.com/Anisiat/comorbidicare/issues)
    or get in touch. Suggestions with a short clinical reason are especially
    helpful.

## Scoring

The CCI score is the sum of the standard Charlson weights for each flagged
condition:

| Weight | Conditions |
|---:|---|
| 1 | `myocardial_infarction`, `congestive_heart_failure`, `peripheral_vascular_disease`, `cerebrovascular_disease`, `dementia`, `chronic_pulmonary_disease`, `rheumatic_disease`, `peptic_ulcer_disease`, `mild_liver_disease`, `diabetes_without_complication` |
| 2 | `diabetes_with_complication`, `hemiplegia_or_paraplegia`, `renal_disease`, `malignancy` |
| 3 | `moderate_or_severe_liver_disease` |
| 6 | `metastatic_solid_tumor`, `aids_hiv` |

Three conditions come in a milder and a more severe form. When both are
flagged, only the more severe one is scored, so the same disease is never
counted twice:

| If this is flagged… | …this is not scored |
|---|---|
| `diabetes_with_complication` | `diabetes_without_complication` |
| `moderate_or_severe_liver_disease` | `mild_liver_disease` |
| `metastatic_solid_tumor` | `malignancy` |

Both flags stay in the output, so you can still see that each was recorded.

The score is **not age-adjusted**. If you need the age-adjusted CCI, add the
age points yourself.

## Where the mapping files are

The three mapping tables are CSV files in
[`src/comorbidicare/data/`](https://github.com/Anisiat/comorbidicare/tree/main/src/comorbidicare/data).
Any change to them changes people's results, so each change is recorded in the
[changelog](https://github.com/Anisiat/comorbidicare/blob/main/CHANGELOG.md).
