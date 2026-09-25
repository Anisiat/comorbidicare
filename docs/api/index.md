# API reference

These pages render function signatures, parameters, return values, and source
code directly from the package's Python docstrings using mkdocstrings.

| Stage | Reference | Purpose |
| --- | --- | --- |
| 1 | [Cleaning](cleaning.md) | Standardise raw diagnoses, problem-list, and prescription tables. |
| 2 | [Mapping](mapping.md) | Load lookup tables and convert codes into dated comorbidity evidence. |
| 3 | [Features](features.md) | Build spell-level indicators and optionally calculate CCI scores. |

Import functions from the modules shown on each page. The package root does not
currently re-export these functions.

!!! warning "High-level pipeline is not yet usable"

    `comorbidicare.pipeline.build_comorbidity_table` currently references an undefined
    `subject_col` and does not supply the required mapping arguments.
    Use the cleaning, mapping, and feature functions documented
    here until those implementation issues are resolved.

## Updating this reference

Edit the NumPy-style docstrings in `src/comorbidicare/` to change the generated
function documentation. Edit these Markdown pages to change introductions and
examples. The documentation workflow rebuilds the site when either changes.
