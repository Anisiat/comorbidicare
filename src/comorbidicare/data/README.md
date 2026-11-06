# Mapping files

These CSV files decide which codes and medicines count towards each of the 17
Charlson conditions. **Any change to them changes people's results**: record
it in `CHANGELOG.md` with the source and reason, and release it as at least a
minor version.

| File | Rows | Columns | Source |
|---|---:|---|---|
| `charlson_icd10_mapping.csv` | 271 | `comorbidity`, `icd_code`, `weight` | Quan et al. (2005) |
| `charlson_snomed_mapping.csv` | 1,569 | `comorbidity`, `snomed_code` | Fortin et al. (2022), corrected 2023 |
| `charlson_medication_mapping.csv` | 20 | `comorbidity`, `medication_name` | Curated for this package |

Condition names are the package's canonical names (for example
`myocardial_infarction`); see `features.CCI_COMORBIDITIES`.

## ICD-10

Based on the ICD-10 coding algorithm in:

Quan H, et al. Coding algorithms for defining comorbidities in ICD-9-CM and
ICD-10 administrative data. *Medical Care* 2005;43(11):1130–1139.
<https://doi.org/10.1097/01.mlr.0000182534.19832.83>

`icd_code` holds code **prefixes** without dots (`I252` stands for I25.2).
A patient's code matches every prefix it starts with. No prefix overlaps a
prefix of a different condition; `tests/test_mapping.py` checks this.

## SNOMED CT

Based on Additional File 1 of:

Fortin SP, et al. Adaptation and validation of a coding algorithm for the
Charlson Comorbidity Index in administrative claims data using the SNOMED CT
standardized vocabulary. *BMC Medical Informatics and Decision Making*
2022;22:261. <https://doi.org/10.1186/s12911-022-02006-1>

including the 2023 correction to the moderate or severe liver disease list:
<https://doi.org/10.1186/s12911-023-02205-4>

Codes are matched exactly and stored as text: some are too long to survive
being read as numbers.

The file matches Fortin's corrected list (1,571 code–condition pairs) except
for two pairs removed on purpose. In both, Fortin lists the code under two
conditions and the second one does not fit:

| Code | Meaning | Kept under | Removed from | Reason |
|---|---|---|---|---|
| `372087000` | Primary malignant neoplasm | `malignancy` | `metastatic_solid_tumor` | A primary cancer is not by definition metastatic; keeping it would score 6 instead of 2 |
| `713571008` | Disorder of central nervous system co-occurrent with HIV infection | `aids_hiv` | `dementia` | A CNS disorder alongside HIV is not necessarily dementia |

`194781004` (hypertensive heart and renal disease with both heart failure and
renal failure) is kept under both `congestive_heart_failure` and
`renal_disease`, as in Fortin, because the code describes both conditions.

## Medications

Curated for this package; not from a published codelist. Medicines are only
mapped where they give fairly specific supporting evidence:

- `chronic_pulmonary_disease`: long-acting inhalers (for example tiotropium,
  umeclidinium, budesonide-formoterol)
- `diabetes_without_complication`: gliclazide and the gliptins (alogliptin,
  linagliptin, sitagliptin)

Names match `medication_name_short` in iCARE prescribing, case-insensitively.
Medication evidence is supportive only and never indicates severity or
complications. See `docs/01-CCI-mapping-methodology.md`.
