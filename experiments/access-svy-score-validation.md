# Supported-package check of complete-case score aggregation

Run date: 2026-11-01. This is a computational check, not validation of the underlying comparison or its interval coverage.

The [complete-case uncertainty probe](access-uncertainty-probe.md) computes influence scores for three standardizations and two paired differences. This script passes those **already computed scores** to `svy` 0.36.0 as weighted totals and asks the package to compute their standard errors, keeping the full survey design and centering full-sample singleton strata. Every 2023 record has a unique stratum/PSU pair, so the package uses each record as a PSU. The two paths agree within 1e-10 on the proportion scale.

| Score | Prototype SE, percentage points | svy SE, percentage points |
|---|---:|---:|
| age_only | 0.742530 | 0.742530 |
| age_income | 0.710603 | 0.710603 |
| age_income_insurance | 0.689666 | 0.689666 |
| income_minus_age | 0.248432 | 0.248432 |
| full_minus_age | 0.318598 | 0.318598 |

This tests aggregation of the supplied scores and covariance for the paired differences. It does **not** independently derive the nonlinear joint-stratum contrast, verify the score formula, validate normal-interval coverage with sparse cells, or resolve missingness and confounding. The corresponding age-only calculation in the broader 2023 domain was separately checked as a [nonlinear svy contrast](svy-contrast-validation.md).

Run `python access_uncertainty_probe.py` followed by `python access_svy_score_validation.py`. Install NumPy, pandas, Polars, and svy; details are in `access-svy-score-validation-results.json`.
