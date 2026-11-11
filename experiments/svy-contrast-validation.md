# Independent survey-contrast cross-check

Run date: 2026-11-01. This is a computational methods check, not causal or clinical evidence.

## Method

The 2023 BRFSS extract includes 433,323 records from all reporting areas. Each record has a unique stratum/PSU pair, so this check treats each record as a PSU while retaining the full-sample strata and weights. It defines the 48-state-plus-DC comparison domain and encodes each eligible record into one of 12 cells: three age groups × two diabetes-response groups × two cost-response groups. Records outside the domain retain their design structure.

Using [svy](https://svylab.com/docs/svy/) version 0.36.0, the program estimates the 12 weighted cell proportions and their joint covariance. It then evaluates the pooled-age-standardized difference as a nonlinear expression of those proportions, allowing the package to compute a delta-method standard error without using the prototype's individual influence scores. Both calculations use centered handling of full-sample singleton strata.

## Results and singleton sensitivity

| Calculation | Difference, proportion scale | Standard error | Approximate 95% interval |
|---|---:|---:|---:|
| Python prototype; standard domain rule | 0.04900768 | 0.00667759 | Not promoted |
| svy; standard domain rule | 0.04900768 | 0.00667759 | 0.03592 to 0.06210 |
| svy; apply centered rule to domain singletons | 0.04900768 | 0.00667762 | 0.03592 to 0.06210 |

The point estimate is expressed as a proportion; multiply by 100 for percentage points. The prototype and svy standard-domain calculation differ by 1.09e-15 in the point estimate and 1.51e-16 in the standard error. Agreement checks two computational paths for the same data and chosen design, not all underlying assumptions. The `svy` and `samplics` packages have a shared developer, so they should not be counted as fully independent replications from different research teams.

The standard domain rule treats PSUs outside the domain as zero contributions. The alternative also applies the centered singleton rule to strata with only one domain PSU. Both are stated policy choices; their similarity or difference here does not prove one universally correct. The intervals are package-generated design-based approximations, not causal intervals. Self-report, selection, missingness, confounding, and absent Kentucky and Pennsylvania remain. The separate [synthetic simulation](contrast-simulation.md) found less-than-nominal coverage in one small-sample setting; it does not represent this survey but argues against assuming universal coverage.

## Scope and next steps

This validates the **calculation against a second implementation**, not the scientific validity of comparing these groups or applying results to other years, to type 2 diabetes specifically, or to all U.S. states. The source is a checksum-verified third-party conversion, with codebook checks rather than row-by-row validation. Further review should independently replicate with another survey implementation and test sensitivity to missing income, sparse joint strata, weighting, and annual sampling. The original survey reports continue to present the primary comparisons as descriptive until such review.

## Reproduce

Install `svy`, pandas, NumPy, and Polars, prepare the 2023 extract, and run `python svy_contrast_validation.py`. The 12 cell keys, package version, two policies, and full numerical results are recorded in `svy-contrast-validation-results.json`.
