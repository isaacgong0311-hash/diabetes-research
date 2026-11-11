# A1C-recording comparison: stratified sensitivity analysis

Run date: 2026-11-01. Historical source: [UCI Diabetes 130-US Hospitals](https://doi.org/10.24432/C5230J), 1999–2008. See [findings.md](findings.md) for cohort construction and limitations.

## Question

Does the observed difference in recorded 30-day readmission between encounters with and without a recorded A1C result change when the two groups are compared using the same age-band and prior inpatient-use distribution? This is an observational association, not a test of the effect of ordering an A1C test.

The cohort includes 69,973 patients selected by smallest encounter ID, with death or hospice excluded afterwards. A1C “not recorded” is the source's `None` category and does not establish that a test never occurred. The data include multiple diabetes types, and the dataset does not capture every possible measure of disease severity or clinical context.

## Crude and standardized rates

| Outcome | A1C not recorded | A1C recorded | Difference: recorded minus not recorded |
|---|---:|---:|---:|
| Crude recorded readmission rate | 9.1% | 8.4% | -0.71 percentage points |
| Standardized to pooled age/prior-use distribution | 9.0% | 8.9% | -0.06 percentage points |

The standardized difference has a 95% patient-bootstrap percentile interval of **-0.62 to +0.48 percentage points** (500 successful resamples; seed 3701). The interval quantifies sampling variation under this resampling approach; it does not remove bias or support a causal conclusion.

## Stratum-specific rates

| Age band | Prior inpatient visits | A1C not recorded: n; rate | A1C recorded: n; rate |
|---|---|---:|---:|
| 0–39 | 0 | 2,797; 5.6% | 1,289; 4.5% |
| 0–39 | 1 or more | 340; 21.5% | 74; 16.2% |
| 40–59 | 0 | 13,226; 6.6% | 3,928; 6.6% |
| 40–59 | 1 or more | 1,708; 12.5% | 315; 13.7% |
| 60–79 | 0 | 24,416; 8.7% | 4,913; 9.2% |
| 60–79 | 1 or more | 3,629; 15.9% | 476; 14.5% |
| 80+ | 0 | 9,553; 9.7% | 1,660; 9.9% |
| 80+ | 1 or more | 1,459; 17.4% | 190; 11.1% |

The standardization uses eight strata: four age groups crossed with zero versus one or more prior inpatient visits. Each group's within-stratum readmission rate is weighted by that stratum's proportion in the full analysis cohort. Small or uneven cells make individual stratum rates less stable; the table makes the overlap visible.

## What the comparison does and does not tell us

Only two broad characteristics were accounted for. Residual confounding from illness severity, diabetes type, reasons for ordering tests, other care, hospital differences, access, missing results and discharge context may be substantial. Recorded readmission may also be incomplete. This analysis cannot tell us whether performing an A1C test changes readmission, nor can it guide individual care.

## Reproduce

Install NumPy and run `python standardization_experiment.py` in this folder. It writes `standardization_results.json` and this report. Archive SHA-256: `f82ac129da2ddd2299391ff6fbae3a6a58b3edcf59ac9d7bd480c00fe453112a`.
