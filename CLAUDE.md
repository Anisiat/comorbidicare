# comorbidicare

Python package that derives the 17 Charlson Comorbidity Index (CCI) conditions
and the CCI score from iCARE tables (diagnoses, problems, prescribing).
Source is in `src/comorbidicare/`, tests in `tests/`, docs in `docs/`.

## Commands

```bash
python -m pip install -e ".[dev]"   # editable install with test tools
python -m pytest                    # full test suite; must pass before committing
python -m pytest tests/test_pipeline.py                        # one test file
python -m pytest tests/test_pipeline.py::test_invalid_cutoff_rejected  # one test
python -m pytest --cov=comorbidicare --cov-report=term-missing # coverage report
python -m build && twine check dist/*   # build and check the release files
zensical build --clean --config-file mkdocs.yaml   # build docs into site/
```

Use `python -m pytest`, not bare `pytest`, so the tests run in the Python that
has the package installed.

## Environments and versions

- Support Python >= 3.10 and pandas >= 2.3, including pandas 3.
- The SDE (where the package is used on real data) has **pandas 2.3.3**. The
  local dev environment matches it; CI also tests pandas 3.
- CI (`.github/workflows/tests.yaml`) runs a matrix: Python 3.10/3.13 x
  pandas 2.3/3 (pandas 3 needs Python 3.11+, so 3.10 + pandas 3 is excluded).
- Write pandas code that works on both versions. Known trap: column-label
  dtypes differ (use `astype(str)`, not `astype("string")`).
- Don't pin exact versions in `pyproject.toml`; this is a library.

## How the pipeline works

Entry point: `build_comorbidity_table()` in `pipeline.py`. Steps, in order:

1. `schema.standardise_columns`: rename inputs to canonical names using
   `column_map` (canonical name -> input column name), then strip and lowercase.
2. `cleaning/clean_*`: clean each source table. Diagnoses with no date fall
   back to the spell's `admission_date` when `spell_identifier` is present.
3. `mapping/map_code_to_comorbidity`: map ICD-10, SNOMED and medication names
   to CCI conditions using the CSVs in `src/comorbidicare/data/`.
4. `features.build_comorbidity_features`: keep evidence dated strictly before
   the cutoff and return **one row per subject and spell** with binary flags,
   plus `cci_score` if `cci_score=True`.

## Rules to keep

- **Canonical names.** Everything after `standardise_columns` uses the names in
  `schema.DEFAULT_COLUMN_MAP`. Renamed inputs are handled only via
  `column_map`; never guess column names.
- **Cutoff.** `cutoff="discharge"` (default) or `"admission"`. Evidence exactly
  on the cutoff date is excluded. Use `"admission"` when features must only use
  evidence from before the admission, e.g. for prediction models (otherwise
  codes recorded during the stay leak in).
- **ICD matching.** Codes are uppercased with dots removed, then matched by
  prefix (`startswith`). All matching conditions are kept, not just the most
  specific. The bundled prefixes don't currently overlap.
- **Mapping CSVs change results.** Any edit to `src/comorbidicare/data/*.csv`
  changes people's scores: note the source and reason, add a CHANGELOG entry,
  and treat it as at least a minor version bump.
- **Medication evidence** is supportive, not diagnostic (see
  `docs/01-CCI-mapping-methodology.md`).
- **Inputs are never mutated**; functions work on copies.

## Tests

- Every bug fix gets a test in `tests/test_regressions.py` that reproduces it.
- Shared fixtures are in `tests/conftest.py`.
- Use only synthetic data in tests, docs and examples.

## Docs

- `docs/` is the source; `site/` is build output (ignored by git).
- The docs site deploys to GitHub Pages automatically on push to `main`
  (`.github/workflows/docs.yaml`).
- When behaviour or arguments change, update the README, the relevant page in
  `docs/` and the docstrings together.

## Style

- British spelling in code and docs (standardise, normalise).
- NumPy-style docstrings (`Parameters`, `Returns`).

## Working with Claude

- This repo is worked on from both the Claude app and terminal Claude. Only one
  session edits files at a time; commit before switching.
- Run `git pull` before starting, and check `git log` to see recent changes.
- Release progress: `RELEASE_CHECKLIST.md`. Tick items as they are done.
- Feature ideas: `comorbidicare_ideas.md`.

## How to work with me (learning)

This is my first Python package and I want to learn best practice for coding
and building packages, not just get things done.

- Teach the main concepts behind what we're doing, in plain language, before
  or while doing it.
- Correct my terminology when I use a term wrongly.
- Don't just do things for me: explain the step, and let me try the small
  parts myself where that makes sense.
- Check that I'm following, e.g. a short question at the end of an explanation.
