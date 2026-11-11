# Exploratory experiment: diabetes hospital readmission

Run date: 2026-11-01. The results are deterministic for a fixed dataset. This is an observational, retrospective exploration—not an intervention or a clinical prediction tool.

## Question and dataset

How does recorded readmission within 30 days vary by previous inpatient use, length of stay, and whether an A1C result was recorded? The [UCI Diabetes 130-US Hospitals dataset](https://doi.org/10.24432/C5230J) contains inpatient encounters from 1999–2008 in which any type of diabetes was recorded. It is not restricted to type 2 diabetes. An encounter qualified for the source dataset if it lasted 1–14 days and involved lab tests and medication. Readmission reflects the dataset's recorded outcome, not necessarily all readmissions elsewhere.

The archive had 101,766 encounters and 71,518 distinct patient identifiers. For the main analysis, the encounter with the smallest encounter ID per patient was selected as a proxy for the earliest recorded encounter, then discharges coded as death or hospice (11, 13, 14, 19, 20, 21) were excluded. This left **69,973 encounters**, with 6,277 recorded early readmissions (9.0%). Encounter IDs are a proxy, not independently verified dates. Exclusion was applied after selecting the first encounter; later eligible encounters for excluded patients were not substituted.

## Experiment 1: previous inpatient visits

Grouping is the recorded number of inpatient visits in the year preceding the encounter.

| Group | Encounters | Readmitted within 30 days | Rate | 95% Wilson interval |
|---|---:|---:|---:|---:|
| 0 | 61,782 | 5,015 | 8.1% | 7.9%–8.3% |
| 1 | 5,794 | 747 | 12.9% | 12.1%–13.8% |
| 2 or more | 2,397 | 515 | 21.5% | 19.9%–23.2% |

The recorded rate for the 2-or-more group exceeded the 0 group by **13.4 percentage points**. This is an unadjusted difference, not evidence that reducing visits would itself reduce readmissions.

## Experiment 2: length of stay

| Group | Encounters | Readmitted within 30 days | Rate | 95% Wilson interval |
|---|---:|---:|---:|---:|
| 1–3 days | 35,135 | 2,640 | 7.5% | 7.2%–7.8% |
| 4–7 days | 25,072 | 2,485 | 9.9% | 9.5%–10.3% |
| 8–14 days | 9,766 | 1,152 | 11.8% | 11.2%–12.5% |

Length of stay may reflect illness severity, discharge planning, and other factors. These results cannot establish an effect of shortening or extending a hospital stay.

## Experiment 3: A1C result recorded

| Group | Encounters | Readmitted within 30 days | Rate | 95% Wilson interval |
|---|---:|---:|---:|---:|
| No A1C result recorded | 57,128 | 5,199 | 9.1% | 8.9%–9.3% |
| A1C result recorded | 12,845 | 1,078 | 8.4% | 7.9%–8.9% |

“No A1C result recorded” is the source's `None` category; it does not prove a test was never performed. The groups may differ in care, illness, and other characteristics. This comparison cannot establish whether ordering an A1C test affects readmission.

## Sensitivity check: all eligible encounters

This repeats experiment 1 without selecting one encounter per patient. It retains 99,343 encounters, so patients with more visits contribute more than once. The change in rates shows the impact of the unit of analysis; these rows are correlated and should not be treated as independent patients.

| Group | Encounters | Readmitted within 30 days | Rate | 95% Wilson interval |
|---|---:|---:|---:|---:|
| 0 | 66,245 | 5,690 | 8.6% | 8.4%–8.8% |
| 1 | 18,984 | 2,516 | 13.3% | 12.8%–13.7% |
| 2 or more | 14,114 | 3,108 | 22.0% | 21.3%–22.7% |

## Interpretation and limitations

- The percentages are descriptive and unadjusted. Confounding, selection bias, and changes in care since 2008 limit interpretation and generalization.
- The outcome combines `>30` and `NO` as “not recorded as readmitted within 30 days.” Follow-up and capture outside the contributing system may be incomplete.
- Group intervals are 95% Wilson intervals for individual proportions, not confidence intervals for differences. In the all-encounter sensitivity analysis, repeated patients make the displayed intervals too narrow if interpreted as independent observations.
- The three comparisons were exploratory; no causal claim or multiple-testing inference is made.
- The data include all diabetes types, and may not represent current care, all U.S. hospitals, or all people with diabetes.
- No external validation, adjustment, data linkage, or prospective evaluation was performed. Do not use these results for patient-level decisions.

## Reproduce

Run `python readmission_experiment.py` in this folder. The script downloads the UCI archive if absent, then saves `results.json` and this report. Source dataset: Clore, Cios, DeShazo, and Strack, *Diabetes 130-US Hospitals for Years 1999-2008* (2014), UCI Machine Learning Repository, DOI [10.24432/C5230J](https://doi.org/10.24432/C5230J); licensed CC BY 4.0. Archive SHA-256: `f82ac129da2ddd2299391ff6fbae3a6a58b3edcf59ac9d7bd480c00fe453112a`. The archive is retained for reproducibility.
