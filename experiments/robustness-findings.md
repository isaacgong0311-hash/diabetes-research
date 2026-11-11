# Robustness checks: diabetes readmission experiments

Run date: 2026-11-01. Data source: [UCI Diabetes 130-US Hospitals, 1999–2008](https://doi.org/10.24432/C5230J). These are retrospective exploratory checks, not clinical validation. See [findings.md](findings.md) and [extended-findings.md](extended-findings.md) for definitions and limitations.

## Experiment 8: effect of cohort selection

The main analysis selects the smallest encounter ID for each patient, then excludes death/hospice. The alternative excludes those encounters first and selects the smallest remaining ID for each patient, potentially including a later encounter. The third approach includes every eligible encounter, so the same patient can contribute more than once.

| Selection method | Units | Overall rate | No prior visits: n; rate | One or more: n; rate |
|---|---:|---:|---:|---:|
| First encounter, then exclude | 69,973 | 9.0% | 61,782; 8.1% | 8,191; 15.4% |
| Exclude, then first eligible encounter | 69,990 | 9.0% | 61,795; 8.1% | 8,195; 15.4% |
| All eligible encounters | 99,343 | 11.4% | 66,245; 8.6% | 33,098; 17.0% |

All rates are raw descriptions. The first two analyses contain one encounter per patient; the all-encounter analysis is encounter-weighted, so it is not a rate for unique patients. Encounter ID is a proxy for ordering, and we cannot verify dates from this file. These comparisons reflect both inclusion and weighting changes, not a randomized experiment.

## Experiment 9: repeated patient-level splits

Five fixed random seeds produce five stratified 80/20 patient splits. Each model is re-trained from scratch on its training split; preprocessing is fitted only there. The test groups overlap across runs, so this is a stability check on the same historical dataset, not five independent replications or external validation. The first seed reproduces the original held-out experiment.

| Split seed | Test patients | Test events | Prior-only AUC | Expanded AUC | Expanded average precision | Expanded Brier |
|---|---:|---:|---:|---:|---:|---:|
| 1729 | 13,996 | 1,256 | 0.545 | 0.594 | 0.132 | 0.0807 |
| 11 | 13,996 | 1,256 | 0.546 | 0.599 | 0.129 | 0.0809 |
| 42 | 13,996 | 1,256 | 0.554 | 0.622 | 0.146 | 0.0802 |
| 99 | 13,996 | 1,256 | 0.563 | 0.621 | 0.141 | 0.0804 |
| 2026 | 13,996 | 1,256 | 0.543 | 0.602 | 0.131 | 0.0808 |

The expanded model uses age-band midpoint, prior inpatient/emergency/outpatient visits, length of stay, laboratory test count, medication count, and diagnoses count. Its test AUC ranges from **0.594 to 0.622** over these seeds. Comparing that range with the original single split helps show sampling sensitivity but is not a confidence interval.

## Experiment 10: shuffled-label negative control

For seed 1729, we randomly permuted the training outcomes while keeping the test outcomes intact. The expanded model trained on scrambled labels obtained test AUC **0.527**, average precision **0.109**, and Brier score **0.0816**. It should generally perform near chance on average; any single random shuffle can deviate from 0.5. This control checks that the pipeline does not automatically produce a useful ranking from scrambled training labels; it does not prove absence of all leakage or confounding.

## Reproduce and interpret

Run `python robustness_experiment.py` with NumPy installed and the other experiment scripts in the same directory. Machine-readable outputs are in `robustness_results.json`; the original archive has SHA-256 `f82ac129da2ddd2299391ff6fbae3a6a58b3edcf59ac9d7bd480c00fe453112a`. All three analyses use the same data source; repeated random splits are not an independent dataset. No study here demonstrates causality, transport to a new hospital, clinical benefit, or suitability for an individual patient.
