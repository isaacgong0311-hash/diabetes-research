# Nonlinear survey-package check of the missingness comparison

Run date: 2026-11-01. This is a numerical cross-check under specified assumptions, not validation of the missing-data mechanism or survey coverage.

The [shared-age comparison](missingness-standardized-probe.md) derives record-level influence scores. This check uses `svy` 0.36.0 to estimate 24 weighted age-by-completeness-by-diabetes-by-outcome cell proportions and their joint covariance. It constructs each gap and their difference directly as nonlinear expressions of those proportions, independently of the prototype's influence scores. The full survey design is retained, with one record per stratum/PSU pair and centered full-sample singleton strata.

| Comparison | Estimate, percentage points | Prototype SE, percentage points | svy SE, percentage points |
|---|---:|---:|---:|
| complete | +4.8866 | 0.745050 | 0.745050 |
| incomplete | +4.8908 | 1.496888 | 1.496888 |
| complete_minus_incomplete | -0.0042 | 1.672087 | 1.672087 |

Both computations agree to better than 1e-10 on the proportion scale. This supports the numerical calculation under the same input data and design choices. It does not prove that missingness is ignorable, that income or insurance has no effect, or that the normal intervals have nominal coverage. It does not replace a separately developed replication or address confounding and nonresponse.

Run `python missingness_standardized_probe.py` followed by `python missingness_svy_validation.py` with NumPy, pandas, Polars and svy installed. Machine-readable results are in `missingness-svy-validation-results.json`.
