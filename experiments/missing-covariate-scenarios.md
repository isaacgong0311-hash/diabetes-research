# Fixed-assignment stress test for missing covariates

Run date: 2026-11-01. This is a set of deliberately strong hypothetical assignments, not a missing-data model, causal analysis, or set of mathematical bounds.

## Setup

Of 402,094 respondents with definite diabetes and cost responses and known age in 48 states plus DC, 85,827 lack income and/or insurance. We retain observed values and fill only the missing fields. Within each diabetes-response group, a scenario assigns **every** missing income to one chosen income band and **every** missing insurance response to one chosen coverage category. Existing observed values are never replaced. The row chooses the assignment for respondents reporting no diabetes; the column chooses it for respondents reporting diabetes. Each cell recomputes both group rates standardized to that scenario's pooled age-income-insurance distribution.

Income bands are below $25,000, $25,000–<$50,000, and $50,000 or above; insured means any reported coverage. Each table entry is the diabetes-minus-no-diabetes difference in percentage points.

| No-diabetes assignment ↓ / Diabetes assignment → | <25k insured | <25k uninsured | 25–<50k insured | 25–<50k uninsured | 50k+ insured | 50k+ uninsured |
|---|---:|---:|---:|---:|---:|---:|
| <25k insured | +4.00 | +2.95 | +4.86 | +3.80 | +6.03 | +4.86 |
| <25k uninsured | +5.78 | +4.27 | +6.69 | +5.18 | +8.01 | +6.38 |
| 25–<50k insured | +3.84 | +2.94 | +3.72 | +2.69 | +5.22 | +4.17 |
| 25–<50k uninsured | +5.51 | +4.17 | +5.42 | +3.94 | +7.06 | +5.55 |
| 50k+ insured | +1.93 | +1.10 | +2.15 | +1.27 | +3.69 | +2.61 |
| 50k+ uninsured | +3.16 | +2.02 | +3.39 | +2.20 | +5.38 | +3.89 |

Across these 36 specific, deterministic scenarios, the difference ranges from +1.10 to +8.01 percentage points. This is **not** the range of all possible missing-value patterns: people within each response group can have different missing values, and assignments could depend on outcomes or other characteristics. It is also not an interval for sampling uncertainty. The standard population changes with each scenario, so the scenarios pose different descriptive questions. The smallest unweighted group/cell across the scenarios is 23.

## Holding the reference population fixed

To separate changes in the estimated group rates from changes in the standard population, this table repeats the same assignments but always standardizes to the pooled age-income-insurance distribution of the original complete cases. Across these 36 settings, the fixed-reference difference ranges from +1.38 to +5.98 percentage points. This comparison still depends on the artificial assignments and is not a bound or uncertainty interval.

| No-diabetes assignment ↓ / Diabetes assignment → | <25k insured | <25k uninsured | 25–<50k insured | 25–<50k uninsured | 50k+ insured | 50k+ uninsured |
|---|---:|---:|---:|---:|---:|---:|
| <25k insured | +3.64 | +2.81 | +3.83 | +2.92 | +5.22 | +4.19 |
| <25k uninsured | +4.39 | +3.56 | +4.58 | +3.67 | +5.98 | +4.94 |
| 25–<50k insured | +3.38 | +2.55 | +3.57 | +2.66 | +4.97 | +3.93 |
| 25–<50k uninsured | +4.12 | +3.29 | +4.31 | +3.40 | +5.71 | +4.67 |
| 50k+ insured | +2.21 | +1.38 | +2.40 | +1.49 | +3.80 | +2.77 |
| 50k+ uninsured | +2.91 | +2.08 | +3.10 | +2.19 | +4.50 | +3.47 |

The values provide a stress test of assumptions, not evidence that any assignment is plausible. They do not account for the uncertainty of missing values, residual confounding, nonresponse, omitted states, or changing the missing-age population. They cannot establish why the diabetes and no-diabetes groups differ. The separately [cross-checked complete-case analysis](access-svy-nonlinear-validation.md) uses a narrower population; its results are not directly comparable as causal estimates.

The figures display both the [varying-reference matrix](figure_missing_covariate_scenarios.png) and the [fixed-reference matrix](figure_missing_covariate_fixed.png); SVG versions are also available.

## Reproduce

Run `python missingness_standardized_probe.py` and then `python missing_covariate_scenarios.py`, with pandas and NumPy. Run `python plot_missing_covariate_scenarios.py` with matplotlib installed to regenerate the figure. All 36 rates, assignments, and cell-size diagnostics are in `missing-covariate-scenarios-results.json`.
