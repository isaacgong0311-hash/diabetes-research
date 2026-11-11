# Missing-covariate audit for the 2023 access comparison

Run date: 2026-11-01. This is a descriptive sensitivity check; it does not determine the missing-data mechanism or estimate effects of income, insurance, or diabetes.

The [complete-case analysis](brfss-access-standardization.md) begins with 409,306 adults with definite diabetes and cost-barrier responses, positive survey weights, and the 48-state-plus-DC footprint. It retains 316,267 with known age, household income, and insurance. Counts below are unweighted; percentages and cost-barrier rates use survey weights. Unknown diabetes or cost responses were already excluded before this audit.

| Response group | Base n | Excluded n | Excluded, weighted | Complete-case cost rate | Excluded cost rate |
|---|---:|---:|---:|---:|---:|
| Reports diabetes | 58,047 | 13,239 | 25.1% | 11.4% | 10.3% |
| Reports no diabetes | 351,259 | 79,800 | 25.1% | 11.6% | 11.1% |

| Reason for exclusion | Reports diabetes: n (weighted %) | Reports no diabetes: n (weighted %) |
|---|---:|---:|
| Unknown age | 886 (2.0%) | 6,326 (1.8%) |
| Unknown income | 11,605 (21.5%) | 69,663 (21.5%) |
| Unknown insurance | 2,313 (4.9%) | 15,259 (5.6%) |

The exclusion reasons overlap, so counts and percentages across reasons do not sum to total exclusions. Income is defined as known only for `_INCOMG1` codes 1–7; insurance requires `_HLTHPL1` codes 1 or 2. A respondent can have more than one unknown field.

## Within broad age bands

These rows include respondents with known age only; those missing age appear in the preceding tables but cannot be assigned an age band here. No further adjustment has been made.

| Group | Age | Complete n | Excluded n | Excluded, weighted | Complete cost rate | Excluded cost rate |
|---|---|---:|---:|---:|---:|---:|
| diabetes | 18–44 | 3,361 | 754 | 21.7% | 22.2% | 22.0% |
| diabetes | 45–64 | 16,228 | 3,435 | 19.4% | 15.0% | 15.4% |
| diabetes | 65+ | 25,219 | 8,164 | 27.7% | 4.7% | 4.9% |
| no diabetes | 18–44 | 92,635 | 24,465 | 24.5% | 15.9% | 15.2% |
| no diabetes | 45–64 | 88,408 | 18,176 | 19.4% | 9.9% | 10.9% |
| no diabetes | 65+ | 90,416 | 30,833 | 28.0% | 3.1% | 3.2% |

Differences between complete and excluded respondents may reflect age composition, other measured or unmeasured characteristics, selection, or random error. Comparing observed cost rates cannot prove that values are missing at random or not at random, cannot reveal the missing covariates, and does not correct selection bias. No confidence intervals or significance tests are provided. The self-reported cost question concerns any needed doctor visit, and diabetes type is not identified.

## Reproduce

Run `python brfss_access_standardization.py` then `python access_missingness_audit.py`. It uses the previously checksum-verified 2023 extract and writes `access-missingness-audit-results.json`. Run `python verify_access_missingness.py` with DuckDB installed for a separate SQL check of the group counts, missing income, weights, and excluded-group cost rates.
