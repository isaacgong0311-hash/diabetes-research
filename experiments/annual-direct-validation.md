# Direct check of the annual uncertainty calculation

Run date: 2026-11-01. This checks arithmetic under shared assumptions; it does not validate the statistical interpretation or assumptions for real surveys.

The [annual contrast probe](annual-contrast-probe.md) combines `svy` cell-proportion covariance matrices with derivatives. This program instead computes the contrast directly from weighted age-by-group means and the baseline age distribution. It derives per-record influence contributions from those quantities and aggregates them by the full-sample strata and PSUs, including records outside the comparison domain with zero contribution. The 2023 contribution includes both the reference-age distribution and baseline group rates; annual sampling is assumed independent, and full-sample singleton strata are centered.

| Comparison | Change in contrast, percentage points | Direct standard error, percentage points | Direct minus svy-covariance SE, proportion scale |
|---|---:|---:|---:|
| 2024 | +1.3095 | 0.962746 | -3.23e-11 |
| 2025 | +1.1646 | 1.005196 | -3.48e-11 |

For each comparison, both the point estimate and the two year-specific variance contributions match the `svy` covariance approach within numerical tolerances. The checks use different computational pathways but the same linearization, data, singleton rule, and independence assumptions; this is not an independent study, a guarantee of coverage, or confirmation that annual samples have zero covariance.

Run `python annual_contrast_probe.py` followed by `python annual_direct_validation.py` after preparing the datasets. The results are also available in `annual-direct-validation-results.json`.
