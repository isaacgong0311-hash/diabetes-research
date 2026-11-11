# Nonlinear survey-package check of complete-case standardization

Run date: 2026-11-01. This checks the computation under shared survey-design assumptions; it does not establish causal effects or interval coverage.

The [complete-case uncertainty probe](access-uncertainty-probe.md) uses record-level influence scores. This check independently expresses the three standardizations and their two paired differences as nonlinear functions of 72 weighted age-by-income-by-insurance-by-diabetes-by-outcome cell proportions. `svy` 0.36.0 estimates the full cell covariance and applies its contrast machinery. It keeps the full survey design and centers full-sample singleton strata; the 2023 data have one record per stratum/PSU pair.

| Comparison | Estimate, percentage points | Prototype SE, percentage points | svy SE, percentage points |
|---|---:|---:|---:|
| age_only | +4.9268 | 0.742530 | 0.742530 |
| age_income | +2.7032 | 0.710603 | 0.710603 |
| age_income_insurance | +3.4669 | 0.689666 | 0.689666 |
| income_minus_age | -2.2236 | 0.248432 | 0.248432 |
| full_minus_age | -1.4599 | 0.318598 | 0.318598 |

Both calculations agree within 1e-10 on the proportion scale. This provides an end-to-end check of the numeric standardization and variance calculations, including covariance for paired changes, under the same data and design assumptions. It does not validate the sparse-cell normal approximation, prove the missing data are ignorable, or make these comparisons causal. The [bootstrap diagnostic](access-bootstrap-probe.md) illustrates sparse-event instability without establishing coverage.

Run `python access_uncertainty_probe.py` followed by `python access_svy_nonlinear_validation.py`. NumPy, pandas, Polars and svy are required. Results are saved in `access-svy-nonlinear-validation-results.json`.
