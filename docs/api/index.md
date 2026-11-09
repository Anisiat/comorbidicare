# API reference

These pages render function signatures, parameters, return values, and source
code directly from the package's Python docstrings using mkdocstrings.

| Stage | Reference | Purpose |
| --- | --- | --- |
| All | [Input schema and pipeline](schema.md) | Run every stage in one call. |
| 1 | [Input schema and pipeline](schema.md#comorbidicare.schema.standardise_columns) | Rename input columns to canonical names. |
| 2 | [Cleaning](cleaning.md) | Clean raw diagnoses, problem-list, and prescription tables. |
| 3 | [Mapping](mapping.md) | Load lookup tables and convert codes into dated comorbidity evidence. |
| 4 | [Features](features.md) | Build spell-level indicators and optionally calculate CCI scores. |

Import functions from the modules shown on each page. The package root does not
currently re-export these functions.

To run all stages on raw iCARE tables, use `build_comorbidity_table`, which is
imported from the package itself (`from comorbidicare import
build_comorbidity_table`). See [Input schema and pipeline](schema.md) for the
columns it reads.

## Updating this reference

Edit the NumPy-style docstrings in `src/comorbidicare/` to change the generated
function documentation. Edit these Markdown pages to change introductions and
examples. The documentation workflow rebuilds the site when either changes.
