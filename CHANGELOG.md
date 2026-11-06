# Changelog

All notable changes to comorbidicare are listed here, newest first.
Versions follow [semantic versioning](https://semver.org/).

## 0.1.0 (2026-11-06)

First release.

- Derive the 17 Charlson comorbidities for each admission from iCARE
  diagnoses (ICD-10, SNOMED CT), problems (SNOMED CT) and prescribing tables.
- Optional weighted CCI score (no age adjustment).
- Evidence cutoff before discharge (default) or before admission.
- `column_map` for input tables with non-standard column names.
