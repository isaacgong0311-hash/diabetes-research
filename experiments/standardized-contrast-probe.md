# Experimental standardization-variance diagnostic

Run date: 2026-11-01. This file documents a **research prototype**, not a validated confidence interval or clinical result. The main [2023 survey report](brfss2023-findings.md) remains a point-estimate analysis.

## What was checked

The contrast is the difference in the two cost-barrier proportions standardized to the weighted age distribution of the pooled eligible sample. Unlike a fixed external standard, this reference distribution is estimated from the same sample. The prototype linearizes both the age-specific rates and the estimated reference weights, retains out-of-domain records with zero scores, and aggregates the scores using full-sample strata and PSUs.

For 402,094 eligible respondents, the contrast is +4.901 percentage points. The sum of individual influence scores is 2.78e-17. Numerical perturbations of 38 selected survey weights produced a maximum absolute derivative discrepancy of 9.26e-14 on the proportion scale. This is an implementation check, not an independent validation of the survey variance or interval coverage.

The prototype also computes candidate standard errors under two full-sample singleton-stratum policies. Those diagnostic quantities are retained in `standardized-contrast-probe-results.json`. The policies are modeling choices. A separate [estimator check](samplics-probe.md) compares aggregation of these influence scores against another package under one policy, but does not independently verify the score formula. A further [nonlinear-contrast check](svy-contrast-validation.md) uses a supported package to compute the whole contrast from cell proportions and their covariance, and examines domain-singleton policies. Further uncertainty assessment across annual survey comparisons remains necessary.

## Reproduce

Run `python standardized_contrast_probe.py` after preparing the 2023 extract. Requires pandas and NumPy. Do not use this prototype for policy conclusions or patient-level decisions.
