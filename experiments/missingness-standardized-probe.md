# Missingness sensitivity with a shared age distribution

Run date: 2026-11-01. This is an exploratory observational comparison, not a missing-data correction or causal analysis.

Among 402,094 2023 respondents with known age and definite diabetes and cost responses in 48 states plus DC, 316,267 had known income and insurance and 85,827 lacked at least one. Respondents with unknown age are excluded from this particular comparison. The [missingness audit](access-missingness-audit.md) includes them in its overall counts.

For each completeness group, the gap is the cost-barrier rate for respondents reporting diabetes minus that for respondents reporting no diabetes. Both gaps are standardized to the **same pooled age distribution of all known-age respondents**, including complete and incomplete cases. Thus these complete-case figures differ from [earlier estimates](brfss-access-standardization.md) that use the complete-case age distribution as their reference. The contrast between gaps reflects differences in observed outcomes, not the effect of missingness and not the outcome that would have occurred had missing covariates been observed.

| Comparison | Gap or difference, percentage points | SE, points | Approximate 95% interval, points |
|---|---:|---:|---:|
| Complete income and insurance | +4.89 | 0.75 | +3.43 to +6.35 |
| Missing income and/or insurance | +4.89 | 1.50 | +1.96 to +7.82 |
| Complete gap minus incomplete gap | -0.00 | 1.67 | -3.28 to +3.27 |

The prototype uses the full strata and PSUs, accounts for uncertainty in the shared estimated age reference and covariance between the two gaps, and centers full-sample singleton strata. A [survey-package cross-check](missingness-svy-validation.md) reproduces the whole nonlinear calculation under the same design choices; coverage of the normal-approximation intervals is not established. The common reference shares are 46.1%, 30.3%, and 23.6% for ages 18–44, 45–64, and 65+. Numerical checks of 24 selected derivatives had maximum error 3.5e-14 on the proportion scale.

Differences may reflect other respondent characteristics, nonresponse, self-report, selection, sampling error, or residual age differences within bands. This does not identify the missing income or insurance values, establish whether data are missing at random, or extend the complete-case income-and-insurance-standardized results to all respondents. Diabetes type is not identified and the missing Kentucky and Pennsylvania data prevent all-state coverage.

## Reproduce

Run `python missingness_standardized_probe.py` after the 2023 extract is prepared; NumPy and pandas are required. Numerical results are in `missingness-standardized-probe-results.json`.
