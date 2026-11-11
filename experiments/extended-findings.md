# Extended readmission experiments

Run date: 2026-11-01. These experiments use the historical [UCI diabetes hospital dataset](https://doi.org/10.24432/C5230J). They are exploratory, not suitable for medical decision-making.

## Cohort and setup

We reused the cohort defined in [findings.md](findings.md): one encounter per patient using the smallest encounter ID as a proxy for the earliest recorded encounter, followed by exclusions for death or hospice. It contains 69,973 patients. Diabetes type is not restricted to type 2. We randomly split patients, stratified by the recorded <30-day readmission outcome, into 55,977 training and 13,996 test patients (seed 1729); 1,256 test patients had an event. No patient appears in both sets.

The expanded logistic model uses age-band midpoint, log-transformed prior inpatient, emergency and outpatient visits, length of stay, number of lab procedures, number of medications, and number of diagnoses. These are encounter-level data available by discharge, not necessarily at admission. It excludes sex and race, but the other features can still reflect unequal access or care. All scaling uses training data only. The model uses fixed settings with no test-set tuning. The prior-only model uses just prior inpatient visits; the constant model assigns the training event rate to everyone.

## Experiment 4: does the prior-use pattern appear across age bands?

Rates are unadjusted; one row per patient across the full cohort. Age is recorded in 10-year bands and grouped here into four broader bands.

| Age band | No prior inpatient visits: n; rate | One or more: n; rate |
|---|---:|---:|
| 0–39 | 4,086; 5.3% | 414; 20.5% |
| 40–59 | 17,154; 6.6% | 2,023; 12.7% |
| 60–79 | 29,329; 8.8% | 4,105; 15.7% |
| 80+ | 11,213; 9.7% | 1,649; 16.7% |

This is a check for a pattern within age groups, not a fully adjusted analysis. Differences in illness, insurance, facility, and other factors may remain within each age band.

## Experiment 5: patient-held-out prediction

| Model | ROC AUC | Average precision | Brier score |
|---|---:|---:|---:|
| Constant training prevalence | 0.500 | 0.090 | 0.0817 |
| Prior inpatient visits only | 0.545 | 0.112 | 0.0809 |
| Expanded model | 0.594 | 0.132 | 0.0807 |

ROC AUC describes ranking ability (0.5 is chance); average precision summarizes precision across recall levels, with prevalence as the constant baseline; Brier score measures average squared probability error (lower is better). These are test-set estimates, not estimates for a new hospital or a future year. The expanded model's ROC AUC has a paired test-set bootstrap 95% interval of **0.579–0.609**. Its AUC difference versus prior visits alone is **0.050** (200-resample paired percentile interval 0.037–0.063). This bootstrap holds the fitted models fixed and excludes training and dataset-selection uncertainty.

## Experiment 6: what a risk threshold would flag

The following thresholds are illustrations, not recommended cutoffs. Positive predictive value is the fraction of flagged patients who experienced the recorded outcome; sensitivity is the fraction of all test events flagged.

| Threshold | Flagged | True positives | False positives | Sensitivity | Positive predictive value |
|---|---:|---:|---:|---:|---:|
| 10.0% | 3,484 | 431 | 3,053 | 34.3% | 12.4% |
| 20.0% | 271 | 68 | 203 | 5.4% | 25.1% |

False negatives and true negatives are in the JSON file. The choice of any threshold would depend on the intervention, resources, harms, and prospective evaluation, none of which was assessed here.

## Experiment 7: calibration and subgroup performance

The test cohort was divided into ten equal-sized groups by predicted risk. Close agreement is desirable, but this table does not validate calibration at other hospitals, times, or within every subgroup.

| Risk tenth, lowest to highest | n | Mean predicted risk | Observed event rate |
|---|---:|---:|---:|
| 1 | 1,400 | 5.3% | 4.3% |
| 2 | 1,400 | 6.3% | 6.3% |
| 3 | 1,400 | 6.9% | 6.7% |
| 4 | 1,400 | 7.4% | 8.1% |
| 5 | 1,400 | 7.9% | 8.7% |
| 6 | 1,400 | 8.5% | 10.4% |
| 7 | 1,399 | 9.1% | 8.8% |
| 8 | 1,399 | 10.0% | 11.2% |
| 9 | 1,399 | 11.6% | 10.6% |
| 10 | 1,399 | 17.2% | 14.7% |

| Overall test events | Overall test patients | Observed rate |
|---:|---:|---:|
| 1,256 | 13,996 | 9.0% |

Age-specific test results:

| Age band | Test patients | Events | ROC AUC | Brier score |
|---|---:|---:|---:|---:|
| 0–39 | 897 | 65 | 0.707 | 0.0646 |
| 40–59 | 3,791 | 292 | 0.598 | 0.0706 |
| 60–79 | 6,713 | 634 | 0.584 | 0.0847 |
| 80+ | 2,595 | 265 | 0.562 | 0.0909 |

The age bands have different sample sizes and event counts; subgroup estimates are uncertain, and differences in AUC alone do not establish fairness. We did not perform a comprehensive fairness audit.

## Limitations and next steps

- A random patient split does not assess temporal or geographic transport. Hospital identifiers and actual encounter dates are not available for a reliable hospital-held-out or chronological validation in this file.
- The data cover 1999–2008 and all recorded diabetes types; clinical practice and coding have changed. The source dataset already selects encounters with lab tests, medications, and stays of 1–14 days.
- Recorded readmissions may not include all care outside the contributing system. Patients discharged to death or hospice were excluded after first-encounter selection; unknown disposition codes remain.
- Calibration, subgroup analysis, and thresholds were explored on this same test set. No external validation, model selection study, intervention evaluation, formal causal adjustment, or prospective trial was conducted.
- The model's associations are not causal effects. With an imbalanced outcome, a high accuracy score alone would be misleading, so we report ranking, probability error, and threshold tradeoffs.
- Reasonable follow-up: access a current, appropriately governed dataset with dates and site identifiers; define intended use and outcome capture; validate prospectively, including subgroup calibration and intervention harms.

## Reproduce

Install NumPy in your chosen Python environment (`python -m pip install numpy`), then run `python model_experiment.py` in this folder. The original archive is downloaded by `readmission_experiment.py` if needed. Results are saved as `model_results.json`. Python, NumPy, seed, and archive hash affect reproducibility; archive SHA-256: `f82ac129da2ddd2299391ff6fbae3a6a58b3edcf59ac9d7bd480c00fe453112a`. The fitted model is intentionally not saved as a clinical artifact.
