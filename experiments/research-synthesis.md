# Diabetes research: synthesis and evidence boundaries

Updated: 2026-11-01. This working synthesis brings together analyses from two different public-data sources. It is exploratory research, not clinical guidance.

## What was studied

1. **Hospital records:** the UCI Diabetes 130-US Hospitals dataset, covering 1999–2008 inpatient encounters involving any diabetes type. The main analysis selects one encounter per patient, then excludes death/hospice, leaving 69,973 records. Outcome: recorded readmission in less than 30 days.
2. **Population survey:** CDC BRFSS telephone survey data, accessed through checksum-verified third-party conversions. The 2023 public data cover 48 states and DC after territories are excluded. Outcome of interest: self-reported inability to afford a needed doctor visit in the past year. Diabetes status is self-reported and does not identify type 2 specifically.

These studies ask different questions. The survey does not independently validate the hospital model, and the hospital cohort does not estimate the experiences of all people with diabetes.

## Findings worth investigating

### 1. Prior inpatient use and recorded readmission

The hospital cohort's recorded <30-day readmission rates were 8.1% after zero prior inpatient visits, 12.9% after one, and 21.5% after two or more. These are unadjusted associations. They may reflect illness severity, access, care patterns, or other factors; they do not prove that prior visits cause readmission.

The simple expanded model had test AUC 0.594 on one patient split. Across five overlapping random splits, its AUC ranged from 0.594 to 0.622. This is modest discrimination, not external validation. Dataset vintage, outcome capture, and absence of verifiable dates and hospital identifiers limit transportability.

Details: [initial hospital analysis](findings.md), [held-out model](extended-findings.md), [robustness checks](robustness-findings.md), and [hospital figure](figure_hospital_readmission.png).

### 2. Recorded A1C and hospital readmission

The crude recorded-minus-not-recorded A1C comparison was -0.71 percentage points; standardizing for broad age and prior-inpatient-use strata changed the difference to -0.06 percentage points. The patient-bootstrap interval was -0.62 to +0.48 points. A missing recorded result is not proof that testing did not occur. Remaining confounding prevents a conclusion about effects of ordering A1C tests.

Details: [A1C standardization analysis](standardization-findings.md).

### 3. Age can obscure cost-barrier comparisons

In the 2023 survey sample, weighted crude doctor-visit cost-barrier rates were 11.2% among respondents reporting diabetes and 11.4% among those reporting no diabetes. Standardized to the pooled age distribution, the rates were 15.9% and 11.0%. This illustrates why sample composition matters; it does not establish why the groups differ. The estimate is for respondents in 48 states and DC, not the entire United States.

On a narrower common complete-case sample, changing the standardization produced the following descriptive rates:

| Common standard | Diabetes | No diabetes reported | Smallest unweighted group/cell |
|---|---:|---:|---:|
| Age | 16.0% | 11.1% | 3,361 |
| Age + income | 14.1% | 11.4% | 736 |
| Age + income + insurance | 14.8% | 11.3% | 23 |

These rows are not competing causal estimates. The standard population differs across specifications, the most detailed specification contains small cells, and 93,039 comparison respondents were omitted from this complete-case analysis due to missing age, income, or insurance data. An [exploratory uncertainty analysis](access-uncertainty-probe.md) retains the full survey design, and a [nonlinear survey-package check](access-svy-nonlinear-validation.md) reproduces the calculations under the same assumptions. Interval coverage is not established. The smallest joint group/cell contains 23 respondents, and a joint group/cell had zero events in 25 of 500 [bootstrap replicates](access-bootstrap-probe.md).

In the broader eligible sample, 25.1% of weighted respondents reporting diabetes and 25.1% reporting no diabetes were excluded for at least one unknown covariate. In an exploratory [shared-age comparison](missingness-standardized-probe.md), the complete-minus-incomplete difference in the diabetes cost-barrier gap was -0.00 percentage points, with an approximate 95% interval of -3.28 to +3.27 points. This does not prove missingness is ignorable or recover the unknown income and insurance values.

For the separate 2023 pooled-age-standardized comparison above, a supported survey package independently computed the full nonlinear contrast and a design-based approximate 95% interval of 3.59 to 6.21 percentage points. It agrees numerically with the prototype under the stated survey-design and singleton assumptions. This checks the calculation, not causal interpretation or actual coverage for BRFSS. See the [survey-contrast cross-check](svy-contrast-validation.md).

Details: [2023 survey analysis](brfss2023-findings.md), [cost-barrier figure](figure_brfss_cost_barriers.png), and [complete-case sensitivity](brfss-access-standardization.md).

### 4. A common-footprint check across three years

To compare 2023–2025 consistently, all years exclude California, Kentucky, Mississippi, Nevada, Pennsylvania, and Tennessee because they are absent from at least one release. The analysis therefore covers 44 states and DC, not the whole country. Rates are standardized to the same 2023 pooled age distribution:

| Year | Respondents | Diabetes | No diabetes reported |
|---|---:|---:|---:|
| 2023 | 379,334 | 15.8% | 11.0% |
| 2024 | 402,275 | 18.0% | 11.8% |
| 2025 | 314,576 | 18.2% | 12.2% |

The samples are cross-sectional and differ each year. There are no validated design-based intervals here, so these numbers do not establish a time trend or statistically significant change.

An [exploratory annual uncertainty probe](annual-contrast-probe.md) accounts for the shared estimated 2023 age reference and, assuming independent annual samples, estimates a 2024-versus-2023 change in the group contrast of +1.31 percentage points (approximate 95% interval -0.58 to +3.20) and a 2025-versus-2023 change of +1.16 points (interval -0.81 to +3.13). Both intervals include zero. These are provisional calculations, not independently validated tests or evidence of a trend. A [synthetic check](annual-simulation.md) covered its known target in 94.1% of 1,000 simulated samples, which does not validate the BRFSS assumptions.

Details: [three-year check](brfss-3year-check.md) and [two-year check](brfss-year-comparison.md).

### 5. Access context

Among 2023 respondents aged 18–64 reporting diabetes and giving definite responses, 13.1% with any reported insurance and 56.3% without reported insurance reported a doctor-visit cost barrier. The groups may differ in many ways; these values do not estimate the effect of obtaining insurance. Unknown insurance and income responses were excluded from their respective analyses.

Details: [access context](brfss2023-access-context.md).

## What is not established

- A treatment effect, causal explanation, or patient-specific risk score.
- A validated prediction system, benefit from a clinical intervention, or evidence of current hospital performance.
- Type 2-specific estimates or nationally representative results for all states in the 2023–2025 survey comparison.
- A validated statistical test or trend across survey years: the annual uncertainty probe relies on an independence assumption and has not been independently validated end to end.
- Validated coverage for the experimental standardized-contrast uncertainty method. In one synthetic design, nominal 95% intervals covered the known answer in 92.9%, 95.0%, and 93.8% of 1,000 samples at increasing sample sizes. These simulations are not BRFSS validation; see [simulation details](contrast-simulation.md).
- Reliable 95% coverage under every sampling design. In a separate synthetic clustered population, the cluster-aware normal interval covered its known target in 91.9% of 1,500 samples; see the [cluster experiment](cluster-simulation.md). This hypothetical design is not BRFSS.
- Complete provenance verification against every original CDC record; the copies were checksum-verified and checked against selected official codebook benchmarks.

## Highest-value next steps

1. Replicate the complete-case and annual uncertainty calculations with a separately developed survey implementation. Investigate sparse-cell interval coverage and cross-year dependence.
2. Obtain the official source files when accessible and cross-check all variables, state participation, and annual coding. Document nonresponse and conduct sensitivity analyses for missing income and insurance.
3. Define a narrow research question and a causal diagram before adding covariates or interpreting the access differences. Decide whether a policy, clinical, or descriptive question is intended.
4. If developing a readmission model, use a current dataset with hospital and encounter dates, a prespecified intended use, external or temporal validation, subgroup calibration, and prospective evaluation before any deployment.

## Reproduce

See the [experiment index](README.md) for dependencies, exact commands, data provenance, checksums, and links to machine-readable results. Run the scripts sequentially on a memory-constrained machine. `make_research_summary.py` regenerates this document from saved results.
