# comorbidicare { .home-title }

<p align="center" markdown>
  ![comorbidicare](assets/logo.svg#only-light){ width="420" }
  ![comorbidicare](assets/logo-dark.svg#only-dark){ width="420" }
</p>

`comorbidicare` derives the 17 Charlson comorbidities and calculates the Charlson Comorbidity Index (CCI) for hospital admissions, from iCARE clinical data.

It takes in a cohort of admissions (spells) and one or more iCARE evidence
tables as pandas DataFrames. It returns **one row per admission** with a `0`/`1`
flag for each of the 17 Charlson conditions and, if you ask for it, the CCI score.

## Installing comorbidicare 

=== "pip"

    ```bash
    pip install comorbidicare
    ```

=== "iCARE AVD (terminal)"

    ```bash
    pip install --trusted-host nexus.tde.imperial.nhs.uk --index-url http://nexus.tde.imperial.nhs.uk:8081/repository/pypi/simple/ comorbidicare
    ```

=== "iCARE AVD (notebook)"

    ```python
    %pip install \
        --trusted-host nexus.tde.imperial.nhs.uk \
        --index-url http://nexus.tde.imperial.nhs.uk:8081/repository/pypi/simple/ \
        comorbidicare
    ```

## What it does

- **Uses up to three iCARE tables that hold comorbidity information:** diagnoses (ICD-10 and SNOMED CT codes),
  problems (SNOMED CT codes) and prescribing (medication names). Any one is
  enough.
- **Links evidence to admissions**: input a cohort table that contain patient and spell id along with a admission and discharge dates. Only evidence before the cutoff date will be included.
- **Maps codes to Charlson conditions** using published codelists
  ([Quan et al. 2005](https://doi.org/10.1097/01.mlr.0000182534.19832.83) for
  ICD-10, [Fortin et al. 2022](https://doi.org/10.1186/s12911-022-02006-1) for
  SNOMED CT) and a short curated medication list.
- **Only counts evidence from before a cutoff:** the admission or discharge
  date of each spell.
- **Scores** with the standard Charlson weights (no age adjustment).

It works on pandas DataFrames. It does not connect to Snowflake: extract the raw tables first, then pass them in.

## Where to go next

| If you want to… | Go to |
|---|---|
| Try it on example data | [Get started](getting-started.md) |
| Extract the right iCARE tables | [Prepare iCARE tables](how-to/prepare-icare-tables.md) |
| Use tables with different column names | [Rename columns](how-to/rename-columns.md) |
| Run cleaning, mapping and scoring yourself | [Run the steps separately](how-to/run-steps-separately.md) |
| Understand where the codes come from | [Mapping methodology](explanation/methodology.md) |
| Choose between an admission and a discharge cutoff | [Pipeline and cutoff](explanation/pipeline-and-cutoff.md) |
| Look up a function or argument | [Reference](api/index.md) |

## Getting help

Report a problem or ask a question on
[GitHub Issues](https://github.com/Anisiat/comorbidicare/issues). See the
[changelog](https://github.com/Anisiat/comorbidicare/blob/main/CHANGELOG.md)
for what changed in each version.
