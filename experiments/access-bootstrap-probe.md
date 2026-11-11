# Stratified PSU bootstrap diagnostic for complete-case contrasts

Run date: 2026-11-01. This is exploratory resampling of the observed survey, not a validation of coverage or a causal analysis.

## Method

Using the full 2023 sample design, including records outside the complete-case comparison domain, this program independently resamples PSUs within each design stratum. Each stratum with n > 1 sampled PSUs contributes n−1 draws with replacement and a weight multiplier n/(n−1). The 101 full-sample singleton PSUs stay fixed, so this bootstrap gives them zero variance contribution; the comparison is the **skip-singleton** linearized SE. All records have a unique stratum/PSU pair in this extract. The bootstrap recomputes the estimated pooled reference distribution and the within-cell rates in every replicate. It holds the released analysis weights fixed apart from the resampling multipliers; it does not rerun survey weight calibration or model nonresponse.

Seed 60241; 500 attempted replicates, 500 valid, and 0 missing a group in at least one standardization cell. 25 attempted replicates had at least one of the 36 joint group/cells with zero observed events. A zero event cell can still yield a finite estimate, but it is a warning about stability.

| Standardization | Point contrast, percentage points | Linearized SE (skip singleton), points | Bootstrap SD, points | Bootstrap percentile interval, points |
|---|---:|---:|---:|---:|
| age_only | +4.93 | 0.74 | 0.76 | +3.51 to +6.50 |
| age_income | +2.70 | 0.71 | 0.74 | +1.38 to +4.15 |
| age_income_insurance | +3.47 | 0.69 | 0.72 | +2.23 to +4.92 |

These are descriptive diagnostics. With only 500 replicates, tail quantiles have substantial Monte Carlo uncertainty. This resampling scheme is a simplified with-replacement approximation and has not been independently validated as CDC replicate weights for this survey. It cannot repair missing income or insurance, guarantee coverage for sparse cells, account for residual confounding, or determine the cause of a difference. The normal intervals in the [linearization probe](access-uncertainty-probe.md) use centered singleton handling, unlike the skip rule here.

## Reproduce

Run `python access_uncertainty_probe.py` followed by `python access_bootstrap_probe.py` with NumPy and pandas. All results are in `access-bootstrap-probe-results.json`.
