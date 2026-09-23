# Ideas for comorb_icare

Once the tests are green the package runs end to end. These are things I think would take it from "works" to "really good".

---

## A. Science options

### 1. Choose the Charlson weights: 1987 or Quan 2011   *(small)*

**What:** a `weights=` argument so users choose between the original 1987 weights and Quan et al.'s 2011 re-estimated ones.

**Why:** when I looked into how Charlson scores are calculated, I found that Quan et al. re-estimated the weights in 2011 on more recent data, and they're quite different. MI, PVD, stroke, peptic ulcer and uncomplicated diabetes all drop to 0, and dementia and mild liver disease go up to 2. From what I read, a lot of recent papers use the 2011 version, so people will probably want to compare.

```python
CCI_WEIGHTS_1987 = {... what you have now ...}

CCI_WEIGHTS_QUAN_2011 = {
    "myocardial_infarction": 0,
    "congestive_heart_failure": 2,
    "peripheral_vascular_disease": 0,
    "cerebrovascular_disease": 0,
    "dementia": 2,
    "chronic_pulmonary_disease": 1,
    "rheumatic_disease": 1,
    "peptic_ulcer_disease": 0,
    "mild_liver_disease": 2,
    "diabetes_without_complication": 0,
    "diabetes_with_complication": 1,
    "hemiplegia_or_paraplegia": 2,
    "renal_disease": 1,
    "malignancy": 2,
    "moderate_or_severe_liver_disease": 4,
    "metastatic_solid_tumor": 6,
    "aids_hiv": 4,
}

WEIGHT_SETS = {"charlson_1987": CCI_WEIGHTS_1987, "quan_2011": CCI_WEIGHTS_QUAN_2011}

def calculate_cci_score(features, weights="charlson_1987"):
    table = WEIGHT_SETS[weights]          # raise a clear error for unknown names
    apply hierarchy (as now)
    score = sum(flag * table[condition] for each condition)
```

**Test:** a patient with only an MI scores 1 under 1987 and 0 under 2011. Heart failure alone scores 1 under 1987 and 2 under 2011.

---

### 2. Lookback window   *(small)*

**What:** a `lookback_days=` argument, so only evidence from, say, the last 1 or 5 years before the admission counts.

**Why:** right now a diabetes code from 1998 flags a 2025 admission. From the papers I looked at, most use a 1 or 5 year window, and when I tried it on test data it changed prevalence a lot.

```python
def build_comorbidity_features(..., lookback_days=None):
    if lookback_days is not None and lookback_days < 0: raise ValueError
    keep evidence where:
        evidence_date < cutoff
        and (lookback_days is None or evidence_date >= cutoff - lookback_days)
```

**Test:** evidence from 10 years ago is dropped with `lookback_days=365`, and evidence from 5 months ago is kept. Evidence dated exactly `lookback_days`before the cutoff still counts (make the window start inclusive).

---

### 3. Default cutoff = admission date   *(tiny)*

**What:** change the pipeline's default `cutoff_col` from `discharge_date` to`admission_date`.

**Why:** With discharge, anything coded *during* the admission counts as pre-existing, which from what I found is a classic source of leakage if the features feed a model predicting something about that admission. Your `build_comorbidity_features` docstring already says admission, so they'd agree.

```python
def build_comorbidity_table(..., cutoff_col="admission_date", ...):
```

**Test:** a problem dated between admission and discharge does not flag that spell.

---

### 4. Make medication evidence opt-in   *(small)*

**What:** if someone passes `prescriptions_df`, require `medication_evidence=True`.

**Why:** your methodology page says medication evidence is supportive rather than diagnostic. When I looked up the drugs in the list, inhaled steroids are also used for asthma, which isn't a Charlson condition, so they could lower specificity. Seems worth making users switch it on knowingly.

```python
if prescriptions_df is not None and not medication_evidence:
    raise ValueError("Medication evidence is supportive only; pass medication_evidence=True")
```

**Also worth deciding:** when I ran it on public data, insulin and metformin were the two most common unmatched prescriptions, and they aren't in the list. Not sure if they should be. That feels like a clinical call.

---

### 5. Age-adjusted CCI   *(small)*

**What:** an `age_col=` argument that adds a `cci_score_age_adjusted` column.

**Why:** it's on your roadmap. The standard version (Charlson et al. 1994), which adds +1 point per decade from 50-59, capped at +4.

```python
def age_points(age):
    return clip((age - 40) // 10, 0, 4)      # 49 -> 0, 50 -> 1, 72 -> 3, 95 -> 4

if age_col:
    features["cci_score_age_adjusted"] = features["cci_score"] + age_points(cohort[age_col])
    # missing or invalid ages -> raise, don't silently score 0
```

**Test:** parametrise ages 39, 49, 50, 59, 60, 70, 80, 95 → 0, 0, 1, 1, 2, 3, 4, 4.

---

### 6. Flag spells with no prior record   *(small)*

**What:** a `has_prior_record` column (or a summary number) for spells with no evidence of *any* kind before the cutoff.

**Why:** something I noticed when testing it: a first admission always scores 0, however ill the patient is, because nothing is on record yet. With iCARE's missing diagnosis dates, that's every single-admission patient. On the MIMIC demo it was 71% of spells. Those zeros mean "no information", not "healthy", and I'd guess a model should know the difference.

```python
earliest = evidence.groupby("subject")["comorbidity_date"].min()
spells["has_prior_record"] = spells.subject.map(earliest) < spells[cutoff_col]
# count ALL evidence, including unmatched codes: they still show the patient had a record
```

**Test:** a patient's first spell is False, their second spell is True. A patient with no evidence at all is False.

---

## B. Showing your working (what makes people trust it)

### 7. Return the evidence table   *(tiny)*

**What:** `return_evidence=True` returns `(features, evidence)`.

**Why:** your README promises a long evidence table with provenance, but the pipeline builds it and throws it away. 

```python
evidence = pd.concat(mapped_tables)
return (features, evidence) if return_evidence else features
```

---

### 8. Evidence summary report   *(small)*

**What:** `summarise_evidence(evidence)` gives rows, matched and unmatched counts per source. `top_unmatched_codes(evidence, n=50)` gives the most common codes that didn't map.

**Why:** the unmatched list is the single best debugging tool. The float SNOMED bug shows up there instantly as "95443002.0" at the top. Log the summary from the pipeline at INFO level.

```python
summary = evidence.groupby("comorbidity_code_source").agg(
    rows=size, matched=comorbidity.notna().sum(), distinct_codes=code.nunique(), ...)

top_unmatched = (evidence[comorbidity.isna()]
                 .groupby([source, code]).size()
                 .sort_values(descending).head(n))
```

---

### 9. Validation helpers   *(small)*

**What:**

- `comorbidity_prevalence(features)`: the fraction of spells with each flag.
- `source_agreement(evidence, "diagnoses", "problems")`: for each condition,
  how many subjects are flagged by both sources, by one only, and the overlap.

**Why:** these seemed like the two obvious checks to run on real iCARE before trusting it. Prevalence should look roughly like published figures. ICD and SNOMED shouldn't wildly disagree for common conditions.

```python
for each condition:
    a = subjects flagged via diagnoses; b = subjects flagged via problems
    both = |a & b|; agreement = both / |a | b|
```

A small `scripts/validate_cohort.py` that runs all of this on parquet files and prints it is really handy.

---

## C. Easier to use

### 10. Import everything from the package root   *(tiny)*

```python
# comorb_icare/__init__.py
from .pipeline import build_comorbidity_table
from .cleaning import clean_diagnoses, clean_problems, clean_prescriptions
... etc, plus __version__ and __all__
```

Then users can write `from comorb_icare import build_comorbidity_table`.

---

### 11. `column_map` for non-iCARE data   *(small)*

**What:** let users rename their columns on the way in.

**Why:** it's the only thing stopping it running on other NHS trusts' data or MIMIC. It's also how you'd test on public data.

```python
build_comorbidity_table(..., column_map={"subject_id": "subject", "hadm_id": "spell_id",
                                         "icd_code": "diagnosis_code_icd"})
# inside: rename every supplied table with column_map before anything else
```

---

## D. Faster (matters once cohorts get big)

### 12. Don't join every code to every spell   *(medium)*

**What:** currently evidence is merged to the cohort on subject alone, so a patient with 20 spells and 400 codes makes 8,000 rows before the date filter.

**Better:** for each spell and condition you only need to know whether *any* evidence predates the cutoff, so reduce first.

```python
# simplest version (no lookback): earliest date per subject+condition, then join
earliest = evidence.groupby(["subject", "comorbidity"]).comorbidity_date.min()
join to spells; flag = earliest < cutoff

# with a lookback window you need the LATEST date before the cutoff instead:
pd.merge_asof(spells_x_conditions.sort_values(cutoff), evidence.sort_values(date),
              left_on=cutoff, right_on=date, by=["subject", "comorbidity"],
              direction="backward", allow_exact_matches=False)
```

With this, 50,000 spells and ~1M source rows run in about 2-3 seconds.

### 13. Faster ICD matching   *(small)*

**What:** at the moment each code is checked against all 271 prefixes. Your prefixes are only 2, 3 or 4 characters long, so use a dictionary.

```python
lookup = {prefix: [conditions]}; lengths = {2, 3, 4}
match(code) = [cond for L in lengths for cond in lookup.get(code[:L], [])]
# and only match each DISTINCT code once, then map back onto the rows
```

---

## E. Tidier code

### 14. One place for shared rules   *(small)*

A few things are written out several times across modules. If one copy changes and the others don't, codes silently stop matching:

- a single `parse_datetime()` used everywhere (UTC, naive, errors → NaT)
- a single `require_columns(df, required, label)` for "missing column" errors
- a single `normalise_columns(df)`: strip, lower-case, rename `spell_identifier` → `spell_id`
- a single ICD normaliser (upper case, no dots) used by both the cleaner and the lookup
- one `EVIDENCE_COLUMNS` tuple for the evidence table schema

### 15. Split scoring into its own module   *(small)*

Move the weights, the hierarchy and the age adjustment into `scoring.py` with a public `calculate_cci_score(flags)`. Then someone can score flags they built elsewhere, and the methodology page maps onto one file. Idea 1 goes here too.

---

## F. Docs and repo polish

- **Getting started page** (currently empty): install, then one runnable example.
- **Worked example page:** walk one patient through several admissions, showing codes → flags → score accumulating, including the first-admission zero and diabetes-with-complications replacing plain diabetes.
- **Validation page:** the checks from ideas 8-9 and how to read them.
- **A notebook** in `examples/` that runs on generated data, so anyone can try it.
- **`data/README.md`:** which Quan / Fortin version and date each CSV came from, and any rows removed by hand. This is key for reproducibility.
- **LICENSE** (MIT is the usual choice), **CITATION.cff**, **CHANGELOG.md** (give mapping changes their own section, since they change scores).
- **ruff** in CI, and test on 3.10 and 3.12. Add a `dev` extra with pytest, pytest-cov, ruff and the docs tools.
- Drop the committed `.coverage` file and add it to `.gitignore`.

---

## Useful to know

- I checked your ICD-10 mapping against **comorbidipy** (another open-source Quan implementation) on 123 real admissions from the MIMIC-IV demo. Every flag on every admission matched. The mapping is right.
- The **MIMIC-IV demo** (physionet.org, open, 100 patients) and **Synthea** (synthetic, has SNOMED) are good for testing on realistic data without needing iCARE.
- Your bundled ICD prefixes never overlap, so "keep all matches" is safe. Worth a test that checks this stays true.
