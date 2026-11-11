# Complete-case standardization: exploratory uncertainty and sparse cells

Run date: 2026-11-01. This is a methods diagnostic, not clinical or causal evidence. The [original comparison](brfss-access-standardization.md) describes the 48-state-plus-DC domain, source, definitions, and complete-case exclusions.

## Full-design calculation

The common complete-case sample contains 316,267 respondents. For each specification, the standard population is its corresponding pooled, weighted age or joint-factor distribution in those respondents. The program computes the full influence score for the standardized diabetes-minus-no-diabetes rate, including estimation of the standard-population weights, and aggregates it using full-sample strata and PSUs; records outside the domain contribute zero. Full-sample singleton strata use centering. These are normal-approximation intervals under a with-replacement linearization, presented for research diagnostics only.

| Standardization | Contrast, percentage points | SE, percentage points | Approximate 95% interval, percentage points |
|---|---:|---:|---:|
| Age | +4.93 | 0.74 | +3.47 to +6.38 |
| Age + income | +2.70 | 0.71 | +1.31 to +4.10 |
| Age + income + insurance | +3.47 | 0.69 | +2.12 to +4.82 |

The estimates match the earlier point estimates. A [nonlinear survey-package cross-check](access-svy-nonlinear-validation.md) independently reproduces the three complete-case calculations and paired differences under the same data and design assumptions. That checks their computation, not whether the sparse-cell intervals achieve their stated coverage. Center-versus-skip singleton results are retained in the JSON. Point estimates and intervals can be affected by missingness, nonresponse, self-report, residual confounding, and design assumptions.

## How specifications differ

The same sample contributes to every row. The following differences in contrasts therefore use the covariance between their influence scores; they are not calculated as if the rows were independent. Each standardization targets a different weighted population, so these are descriptive changes in a statistical estimand, not effects of changing income or insurance.

| Comparison | Change, percentage points | SE, percentage points | Approximate 95% interval, percentage points |
|---|---:|---:|---:|
| Age + income minus age only | -2.22 | 0.25 | -2.71 to -1.74 |
| Age + income + insurance minus age only | -1.46 | 0.32 | -2.08 to -0.84 |

## Sparse cells and verification

The 18 age-income-insurance strata create 36 group/cell combinations. The smallest has 23 respondents; the smallest event count is 3, and the smallest weight-only effective sample size is 7.5. These minima may occur in different cells. Weight-only effective size is `(sum of weights)^2 / sum of squared weights`; it is a descriptive weight-concentration diagnostic, not a survey-design degrees of freedom or a guarantee of precision. Small groups and few events can make normal approximations unstable. Cell-by-cell diagnostics are in the JSON.

The program checked 14 selected weight derivatives, with maximum absolute error 5.2e-14; this is an implementation check, not an external validation or coverage study. In this analysis 93,039 otherwise eligible respondents had unknown age, income, or insurance and were excluded. Results apply to complete cases and should not be generalized to those with missing values without further investigation.

## Reproduce

Run `python brfss_access_standardization.py`, then `python access_uncertainty_probe.py`, with NumPy and pandas installed. Results and cell diagnostics are saved in `access-uncertainty-probe-results.json`.
