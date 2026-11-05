# Release checklist: v0.1.0

Progress towards the first release. Tick items (`[x]`) as they are done and
commit this file with the work. Each step says *why* it matters.

---

## 1. Validation: do the tests pass?

**Why:** before releasing, confirm the code does what the tests say, in every
setup the package claims to support (`pyproject.toml` promises Python >= 3.10
and pandas >= 2.3).

- [x] Full test suite passes locally on pandas 2.3.3 (the SDE version)
- [x] Full test suite passes locally on pandas 3.1
- [x] CI runs a test matrix: Python 3.10/3.13 x pandas 2.3/3 (all green)

## 2. Test the built package: does what users install actually work?

**Why:** locally, the tests run against `src/` through an editable install.
Users instead install a *wheel*, a zip file built from the code. If something
is left out of the wheel (e.g. the mapping CSVs in `src/comorbidicare/data/`),
the tests still pass here but the package breaks for users. This step tests
the wheel itself.

- [x] `python -m build`: creates the wheel (`.whl`) and source archive
      (`.tar.gz`) in `dist/`
- [x] `twine check dist/*`: checks the metadata and that the README will
      display correctly on PyPI
- [x] Create a brand-new environment, install only the wheel, and run a small
      script (outside the repo folder) that runs the pipeline on synthetic data
      (all 3 tables, both cutoffs, liver hierarchy: all as expected)
- [ ] Repeat this check on the final build just before publishing
- [x] Add `MANIFEST.in` with `graft tests`: the sdist currently includes the
      `test_*.py` files but not `tests/conftest.py`, so its tests can't run

## 3. Quick-start docs: can a new user get started?

**Why:** the README and docs are the first thing users read. They must match
what the code actually does.

- [ ] `docs/00-getting-started.md` (currently empty): how to install, and one
      example that runs on made-up data
- [x] README "Outputs": now says one row per subject and spell; the evidence
      table is left out (`return_evidence=True` planned for 0.2.0)
- [x] README: install line added; all links absolute (they work on PyPI)
- [x] README rewritten: runnable quick start using all 3 tables with real
      output, input column table, `column_map` example, cutoff trade-offs,
      paper links (DOIs); breaking-change note, missingness numbers and
      roadmap removed
- [x] Logo added (`docs/assets/logo.svg`, `logo-dark.svg`, `logo-icon.svg`)
      and shown at the top of the README
- [x] Logo: text converted to outlines (Poppins, SIL Open Font License),
      so it looks the same on every computer
- [ ] Docs site: add the logo and favicon in `mkdocs.yaml` (`theme: logo`,
      `favicon`), and fix `site_url` (still the old `comorb_package` address)
- [ ] `docs/04-feature-pipeline.md` (currently empty): explain the pipeline
      steps and the cutoff trade-off with an example
- [ ] Methodology page: remove "age is not contained within the three core
      iCARE source tables" (not confirmed)
- [ ] Check on TestPyPI that the README displays correctly, including the
      table-of-contents links and the logo

## 4. Behaviour decisions: are the choices written down?

**Why:** these choices change people's results. Users need to know what the
package does so they can describe it in their methods.

- [x] Document ICD prefix matching in the README: codes match by prefix and
      *all* matching conditions are kept
- [ ] Add a test that the bundled ICD prefixes never overlap
- [x] Explain the cutoff clearly, with the trade-off for each option (README)
- [ ] Decide whether the default should stay `"discharge"`
- [x] SNOMED mapping checked against Fortin et al. Additional File 1
      (corrected version, May 2023): matches, including the liver codes.
      The 29 long codes that differ are rounded in the Word file; the repo has
      the full codes
- [ ] Write `src/comorbidicare/data/README.md`: sources and versions of each
      mapping file, and the 2 SNOMED codes removed with reasons (`372087000`
      from metastatic solid tumour, `713571008` from dementia)

## 5. Release: version, notes, distribution

**Why:** a release is a fixed, numbered snapshot people can install and cite.
Uploads to PyPI are permanent: a version number can never be reused.

- [ ] Fill in `pyproject.toml` metadata: authors, license, classifiers,
      project URLs
- [x] `build` and `twine` added to the `dev` extra
- [ ] Rebuild after the README changes (the README is copied into the package)
- [ ] On release day, add the PyPI and Python-version badges to the README
      (the Python badge needs the classifiers above)
- [ ] `__init__.py`: add `__version__` and top-level imports
      (`from comorbidicare import build_comorbidity_table`)
- [ ] Tidy the repo: untrack `.coverage`; remove the empty `cleaning.md`,
      `features.md` and `api/` at the top level
- [ ] Confirm the version number (`0.1.0` = first, early release)
- [ ] Write `CHANGELOG.md` (release notes)
- [ ] Ask the SDE team how packages reach the SDE: Nexus directly, or Nexus
      mirroring PyPI?
- [ ] If publishing on PyPI: practise on TestPyPI first, then publish via a
      GitHub Actions workflow with Trusted Publishing (no API tokens)
- [ ] Tag the release in git (`v0.1.0`) and create a GitHub Release
- [ ] Optional: `CITATION.cff` and Zenodo for a citable DOI
