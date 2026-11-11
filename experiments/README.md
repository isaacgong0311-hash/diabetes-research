# Diabetes research experiments

These experiments investigate recorded hospital readmission patterns in the UCI Diabetes 130-US Hospitals dataset. They are historical, exploratory, and not a clinical prediction tool. The data contain encounters involving any diabetes type, not only type 2.

Start with the [research synthesis](research-synthesis.md) for the combined findings and evidence boundaries.

For the follow-up missing-data experiments, read the [missingness research synthesis](missingness-synthesis.md).

The [selected randomized-trial evidence register](randomized-trial-evidence.md) adds study populations, comparators, outcomes, harms, and limits; it is not a systematic review.

The broader adult type 2 diabetes review now includes pivotal evidence modules on [prevention and remission](../pivotal-evidence-prevention-remission.md), [GLP-1/GIP-based therapies and metabolic surgery](../pivotal-evidence-incretins-surgery.md), [cardiovascular and kidney outcomes](../pivotal-evidence-cardiorenal.md), and [CGM with Stelo interpretation](../pivotal-evidence-cgm.md), separate from these exploratory dataset analyses.

## Read the findings

1. [Initial descriptive experiments](findings.md): prior visits, length of stay, and recorded A1C results.
2. [Extended experiments](extended-findings.md): age-stratified rates, a patient-held-out model, threshold tradeoffs, and calibration.
3. [Robustness checks](robustness-findings.md): cohort-selection choices, five patient splits, and a shuffled-label negative control.
4. [A1C-recording sensitivity analysis](standardization-findings.md): comparison standardized for age and prior inpatient visits.
5. [2023 BRFSS population survey](brfss2023-findings.md): weighted diabetes and access-to-care estimates with age-standardization sensitivity checks.
6. [Access context in working-age adults](brfss2023-access-context.md): descriptive comparisons by insurance and income.
7. [2023–2024 common-footprint check](brfss-year-comparison.md): 47 states and DC, excluding KY, PA, and TN from both years.
8. [2023–2025 common-footprint check](brfss-3year-check.md): 44 states and DC; excludes CA, KY, MS, NV, PA, and TN from all years.
9. [Access standardization sensitivity](brfss-access-standardization.md): how descriptive estimates change under age, income, and insurance standardization, using a common complete-case sample.
10. [Survey-design audit](brfss-design-audit.md): strata and primary sampling unit checks that explain what remains before reporting uncertainty.
11. [Survey variance probe](survey-variance-probe.md) and [independent estimator check](samplics-probe.md): exploratory checks of a simple domain ratio, not validation of the standardized contrasts.
12. [Standardized-contrast prototype](standardized-contrast-probe.md) and [supported-package cross-check](svy-contrast-validation.md): independent calculation of the same nonlinear contrast and sensitivity to singleton handling.
13. [Synthetic coverage simulation](contrast-simulation.md): 3,000 simulated samples testing the prototype under one controlled design at three sample sizes.
14. [Synthetic cluster simulation](cluster-simulation.md): 1,500 samples comparing two variance calculations under a hypothetical clustered design.
15. [Annual contrast probe](annual-contrast-probe.md), [direct calculation check](annual-direct-validation.md), and [shared-reference simulation](annual-simulation.md): exploratory year-to-year uncertainty calculations and a synthetic coverage check, subject to an assumption of independent annual samples.
16. [Complete-case uncertainty and sparse cells](access-uncertainty-probe.md), [nonlinear survey-package check](access-svy-nonlinear-validation.md), and [PSU bootstrap](access-bootstrap-probe.md): diagnostic intervals and stability checks for standardizing by age, income, and insurance.
17. [Missing-covariate audit](access-missingness-audit.md), [shared-age comparison](missingness-standardized-probe.md), and [survey-package check](missingness-svy-validation.md): observed cost-barrier rates among complete and excluded respondents and a calculation check.
18. [Missing-covariate assignment scenarios](missing-covariate-scenarios.md): 36 deterministic stress tests that illustrate dependence on hypothetical missing answers; these are not statistical bounds.
19. [Weighted donor-draw sensitivity](hotdeck-sensitivity.md): repeated hypothetical assignments drawn from similar respondents; the variation between draws is not a confidence interval.
20. [Donor masking test](hotdeck-masking-validation.md), [general-health balance audit](hotdeck-balance-audit.md), [health-matched sensitivity](hotdeck-health-sensitivity.md), [matching-rule holdout comparison](hotdeck-health-masking.md), and [repeated holdout checks](hotdeck-repeated-masking.md): checks and alternative assumptions for the donor method, with no validation of genuinely missing answers.

The main figures show [survey cost barriers](figure_brfss_cost_barriers.png) and [hospital readmission](figure_hospital_readmission.png), with separate missing-data scenario figures linked below. The main survey figure displays point estimates; the package cross-check reports an approximate design-based interval for one 2023 standardized contrast.

Each report includes interpretation, limitations, and reproducibility details. Each script also writes a JSON results file. The UCI archive is retained alongside the scripts and its SHA-256 is recorded in each report.

## Run the experiments

The initial experiment uses Python's standard library. The extended experiments and checks additionally need NumPy:

```text
python -m pip install numpy
python readmission_experiment.py
python model_experiment.py
python robustness_experiment.py
python standardization_experiment.py
python -m unittest test_experiments.py
```

For the 2023 survey analyses, additionally install pandas and DuckDB, then run:

```text
python -m pip install pandas duckdb
python brfss_prepare_mirror.py
python brfss_analysis.py
python brfss_access_context.py
python brfss_access_standardization.py
python brfss_design_audit.py
python brfss_year_comparison.py
python brfss_3year_check.py
python verify_brfss.py
```

The preparation script downloads a 29 MB third-party conversion of the CDC dataset and verifies its recorded checksum. The original CDC XPT preparation script is also included, but that download returned HTTP 403 in the environment used here. The survey reports explain the mirror, denominators, and why design-based intervals still need independent validation.

To regenerate the figures, install `matplotlib` and run `python make_figures.py` after producing the 2023 survey and initial hospital results. Run these scripts sequentially on computers with limited memory.

For the survey validation and simulations, install `svy` and Polars in addition to NumPy and pandas, then run `python standardized_contrast_probe.py`, `python svy_contrast_validation.py`, `python contrast_simulation.py`, and `python cluster_simulation.py` in that order. After `brfss_3year_check.py`, run `python annual_contrast_probe.py`, `python annual_direct_validation.py`, and `python annual_simulation.py`. After `brfss_access_standardization.py`, run `python access_missingness_audit.py`, `python verify_access_missingness.py`, `python missingness_standardized_probe.py`, `python missingness_svy_validation.py`, `python access_uncertainty_probe.py`, `python access_svy_score_validation.py`, `python access_svy_nonlinear_validation.py`, and `python access_bootstrap_probe.py`. Additional checks can be run with `python -m unittest test_annual_contrast.py test_access_bootstrap.py`.

Alternatively, with NumPy, pandas, DuckDB, matplotlib, Polars, and svy installed, `python run_pipeline.py` runs the stages sequentially, checks the results, builds figures and synthesis, and records input and script hashes in `pipeline-run.json`. The pipeline replaces the generated reports, JSON, and figures; save any manual edits before running it. Initial runs download the source datasets.

After the main pipeline, run `python run_missingness_pipeline.py` to rebuild the fixed-assignment scenarios, both [varying-reference](figure_missing_covariate_scenarios.png) and [fixed-reference](figure_missing_covariate_fixed.png) figures, donor experiments, and their tests. It records input, script, and output hashes in `missingness-pipeline-run.json` and replaces the supplemental generated files. Then run `python summarize_missingness_research.py` to rebuild the synthesis and verify its inputs. The supplemental analyses are exploratory and the donor draws alone do not provide survey confidence intervals.


Run these commands from this folder. The first script downloads the UCI archive only when the local copy is absent. Running a script replaces its generated findings and results files; save a copy first if you have edited them.

The bundled workspace Python used for this run was Python 3 with NumPy; the primary computer's `python` may require the installation step above. Model random seeds are fixed in the source. Numbers may differ slightly between NumPy versions or platforms.

## What this work can and cannot establish

The comparisons describe associations and evaluate a simple ranking model on random patient splits of the same historical data. They do not establish causal treatment effects, validate a model in another hospital or period, or demonstrate that using the model improves patient outcomes. The source file does not provide the hospital IDs or dates needed for strong temporal or site-based validation. No patient-level predictions or clinical-use model are distributed.
