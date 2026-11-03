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
- [ ] Create a brand-new environment, install only the wheel, and run a small
      script (outside the repo folder) that runs the pipeline on synthetic data

## 3. Quick-start docs: can a new user get started?

**Why:** the README and docs are the first thing users read. They must match
what the code actually does.

- [ ] `docs/00-getting-started.md` (currently empty): how to install, and one
      example that runs on made-up data
- [ ] README "Outputs": the pipeline returns **one row per subject and spell**,
      not one row per subject, and does not return a separate evidence table.
      Either fix the text, or add `return_evidence=True` (ideas file, no. 7)
- [ ] README: add an install line, and fix the relative link to
      `docs/api/schema.md` (relative links break on PyPI)

## 4. Behaviour decisions: are the choices written down?

**Why:** these choices change people's results. Users need to know what the
package does so they can describe it in their methods.

- [ ] Document ICD prefix matching: codes match by prefix and *all* matching
      conditions are kept. Add a test that the bundled prefixes never overlap
- [ ] Explain the cutoff clearly: `cutoff="admission"` uses only evidence from
      before the admission (use this for prediction models);
      `"discharge"` (the default) also counts codes recorded during the stay
- [ ] Decide whether the default should stay `"discharge"`

## 5. Release: version, notes, distribution

**Why:** a release is a fixed, numbered snapshot people can install and cite.
Uploads to PyPI are permanent: a version number can never be reused.

- [ ] Fill in `pyproject.toml` metadata: authors, license, classifiers,
      project URLs
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
