# Donor-method masking check on observed respondents

Run date: 2026-11-01. This is an artificial holdout check, not validation of a missing-data model for respondents who did not answer.

## Design

Starting with 316,267 respondents whose age, income, insurance, diabetes response, and cost response are known, we randomly selected 63,063 (20% target) as holdouts, seed 67032. Holdouts are excluded as donors. In turn, we hide income only, insurance only, or both fields on the same holdouts. For each pattern, we generate 50 weighted donor draws using the [same matching rules](hotdeck-sensitivity.md), and compare imputed categories to their known values. For the two-field pattern, accuracy requires both answers to match. Percentages are survey-weighted descriptive accuracy on held-out observed respondents; they are not design-based uncertainty estimates.

As a simple predictive benchmark, the majority column always selects the donor pool's highest-weight category. A donor draw is intended to represent variation rather than optimize individual accuracy, so the two serve different purposes. We also recompute the overall age-income-insurance-standardized group gap after masking and drawing; the reference distribution is held fixed at the original complete-case distribution. The fully observed reference gap is +3.467 percentage points. Its use here is for evaluation against known answers and would not be available for truly missing covariates.

| Hidden fields | Mean donor-draw accuracy | Weighted majority accuracy | Mean reconstructed gap minus known gap, points | SD across draws, points |
|---|---:|---:|---:|---:|
| Income only | 48.6% | 62.3% | +0.144 | 0.143 |
| Insurance only | 87.3% | 92.2% | +0.211 | 0.098 |
| Income and insurance together | 43.3% | 59.2% | +0.403 | 0.190 |

The smallest donor pool in this exercise had 35 members. The contrast errors and accuracy scores are affected by the particular random holdout split and donor draws. Small mean contrast error can coexist with many wrong individual assignments; neither result implies that donor draws recover the true missing answers.

The holdouts were randomly masked among **observed complete cases**, unlike the original unknown responses. If real nonresponse depends on income, insurance, or unmeasured characteristics, this check can substantially overstate real-world validity. It does not estimate complex-survey sampling uncertainty, correct nonresponse, prove a missing-at-random assumption, or establish causality. Outcome and diabetes status were included in donor matching and remain observed in the targeted domain.

## Reproduce

Run `python hotdeck_masking_validation.py` after generating `brfss-access-standardization-results.json`; NumPy and pandas are required. Results are saved in `hotdeck-masking-validation-results.json`. No record-level imputations are exported.
