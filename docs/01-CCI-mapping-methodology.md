## CCI mapping methodology

### ICD-10

ICD-10 comorbidity mappings are based on:

**Quan et al. (2005)**  
*Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data.*
Medical Care 43(11):1130–1139.
[doi:10.1097/01.mlr.0000182534.19832.83](https://doi.org/10.1097/01.mlr.0000182534.19832.83)

### SNOMED CT

SNOMED CT mappings are based on:

**Fortin et al. (2022)**  
*Adaptation and validation of a coding algorithm for the Charlson Comorbidity
Index in administrative claims data using the SNOMED CT standardized vocabulary.*
BMC Medical Informatics and Decision Making 22:261.
[doi:10.1186/s12911-022-02006-1](https://doi.org/10.1186/s12911-022-02006-1)
([correction, 2023](https://doi.org/10.1186/s12911-023-02205-4): fixes the
moderate or severe liver disease code list)

Clinically invalid or inappropriate category assignments are excluded from the package mappings where necessary.

### Medication evidence

Medication mappings are manually curated and used only for selected Charlson conditions where relatively specific chronic medications provide useful supporting evidence.

Medication evidence is:

- supportive rather than definitive
- used only for selected comorbidities
- not used to distinguish disease severity or complications

The package retains the evidence source so users can distinguish ICD, SNOMED, and medication-derived evidence.

Clinical collaboration: If you are a clinician and would like to contribute to reviewing and optimising the medication mappings used for comorbidity inference, please get in touch.

## CCI scoring

The package will support calculation of the standard weighted Charlson Comorbidity Index based on the inferred comorbidity categories.

Age-adjusted CCI scoring may be supported separately where users provide an appropriate age variable, as age is not contained within the three core iCARE source tables.