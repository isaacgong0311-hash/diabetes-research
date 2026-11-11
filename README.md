# Diabetes research workspace

An evidence-focused research workspace on adult type 2 diabetes, prevention and remission, modern therapies, cardiovascular and kidney outcomes, continuous glucose monitoring (CGM), and reproducible exploratory analyses of public health datasets.

This repository is research and education—not medical advice, diagnosis, or a clinical prediction tool. Treatment decisions and unexpected glucose patterns should be reviewed with a qualified health professional.

## Start here

- [Type 2 diabetes research brief](type-2-diabetes-research-brief.md): the main synthesis and clinical framework.
- [Research protocol](research-protocol.md): scope, evidence hierarchy, appraisal rules, and update plan.
- [Source log](source-log.md): guideline and primary-evidence provenance.
- [Stelo N-of-1 protocol](stelo-n-of-1-protocol.md): prospective randomized paired experiment for a standardized dinner followed by either a 10-minute walk or sedentary control.

## Pivotal evidence modules

1. [Prevention and remission](pivotal-evidence-prevention-remission.md)
2. [GLP-1/GIP-based therapies and metabolic surgery](pivotal-evidence-incretins-surgery.md)
3. [Cardiovascular and kidney outcomes](pivotal-evidence-cardiorenal.md)
4. [CGM evidence and Stelo interpretation](pivotal-evidence-cgm.md)

The modules report study populations, comparators, follow-up, absolute event rates where available, harms, funding, and applicability limits. They are selected evidence extractions rather than completed systematic reviews.

## Reproducible experiments

The [experiments](experiments/) directory contains scripts, tests, generated results, figures, and synthesis reports for:

- the UCI Diabetes 130-US Hospitals dataset;
- 2023–2025 Behavioral Risk Factor Surveillance System analyses;
- age and access standardization;
- survey variance diagnostics;
- missing-covariate sensitivity analyses; and
- synthetic coverage and cluster simulations.

Read [experiments/README.md](experiments/README.md) before running the pipeline. The analyses are historical and exploratory. They do not establish causal treatment effects or validate patient-level clinical predictions.

### Local setup

Python 3.11 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd experiments
python run_pipeline.py
python run_missingness_pipeline.py
python summarize_missingness_research.py
```

The pipeline downloads public source data when absent and records input, script, and output hashes. Large downloaded datasets and local dependency folders are intentionally excluded from Git because they can be regenerated and would add hundreds of megabytes.

## Dashboard

The [dashboard](dashboard/) is a static research browser. To view it locally from the repository root:

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000/dashboard/`.

## Reproducibility and interpretation boundaries

- Raw downloads are not committed; preparation scripts and checksums preserve provenance.
- Generated reports and JSON results are committed so findings can be inspected without rerunning the pipeline.
- CGM is not used here to diagnose diabetes or prediabetes.
- The Stelo protocol estimates a short-term, within-person behavioral effect. It cannot establish long-term cardiovascular, kidney, or diabetes outcomes.
- Public datasets may contain measurement error, missingness, selection effects, and limited variables. Every report documents its specific limits.

## Repository status

Initial evidence extraction and exploratory analyses were current through November 10, 2026. Medical guidance, device labeling, and the evidence base change over time; verify current authoritative sources before applying conclusions.
