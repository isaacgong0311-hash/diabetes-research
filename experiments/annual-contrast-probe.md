# Exploratory annual contrast uncertainty probe

Run date: 2026-11-01. This is an experimental computational analysis, not a validated trend test or causal comparison.

## Target and method

For 2023, 2024, and 2025, the target is the cost-barrier rate among respondents reporting diabetes minus that among respondents reporting no diabetes, standardized to the *same estimated 2023 pooled age distribution*. The comparison is the later-year contrast minus the 2023 contrast, in the common footprint of 44 states and DC. It excludes California, Kentucky, Mississippi, Nevada, Pennsylvania, and Tennessee; it is not a U.S.-wide estimate.

The supported `svy` package version 0.36.0 estimates each year's 12 weighted age-by-group-by-outcome cell proportions and their design covariance, preserving the full design outside the domain and centering full-sample singleton strata. The script verifies one record per stratum/PSU pair in each year before omitting explicit PSU identifiers. It numerically differentiates the difference-in-contrasts with respect to the cell proportions and checks the derivatives against a separate analytic expression. The 2023 reference distribution and 2023 group rates are perturbed together to preserve their covariance. The calculation assumes independent annual samples and zero cross-year covariance; repeated respondents or other cross-year dependence could violate that assumption. It uses normal approximate intervals and does not address the joint uncertainty in both comparisons or multiple testing.

## Preliminary numerical checks

The annual contrasts reproduce the previously calculated three-year point estimates. Under the stated assumptions:

| Comparison | Change in contrast, percentage points | SE, percentage points | Approximate 95% interval, percentage points |
|---|---:|---:|---:|
| 2024 versus 2023 | +1.31 | 0.96 | -0.58 to +3.20 |
| 2025 versus 2023 | +1.16 | 1.01 | -0.81 to +3.13 |

These numbers are exploratory. A separate [direct record-level calculation](annual-direct-validation.md) checks the two variance contributions against the covariance-matrix route under the same assumptions; neither calculation establishes interval coverage or cross-year independence. They do not establish a trend or causal change. The comparison can reflect changes in composition, nonresponse, survey coverage, and measurement. Diabetes is self-reported and does not distinguish type 2. The third-party conversions were checked by hashes and selected official benchmarks, not record by record against CDC source files.

## Reproduce

Run `python brfss_3year_check.py` and then `python annual_contrast_probe.py` with NumPy, pandas, DuckDB, Polars and svy installed. Raw estimates, variance contributions, and assumptions are in `annual-contrast-probe-results.json`.
