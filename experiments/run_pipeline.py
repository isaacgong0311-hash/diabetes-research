"""Rebuild the research artifacts in a consistent, memory-conscious order.

Run only when you are ready to replace generated Markdown/JSON/figure files.
Install numpy, pandas, duckdb, matplotlib, polars, and svy into the active Python environment.
"""
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
STEPS=[
    ['-m','unittest','-v','test_experiments.py','test_annual_contrast.py','test_access_bootstrap.py'],
    ['readmission_experiment.py'],
    ['model_experiment.py'],
    ['robustness_experiment.py'],
    ['standardization_experiment.py'],
    ['brfss_prepare_mirror.py'],
    ['brfss_analysis.py'],
    ['brfss_access_context.py'],
    ['brfss_access_standardization.py'],
    ['access_missingness_audit.py'],
    ['verify_access_missingness.py'],
    ['missingness_standardized_probe.py'],
    ['missingness_svy_validation.py'],
    ['access_uncertainty_probe.py'],
    ['access_svy_score_validation.py'],
    ['access_svy_nonlinear_validation.py'],
    ['access_bootstrap_probe.py'],
    ['brfss_design_audit.py'],
    ['survey_variance_probe.py'],
    ['standardized_contrast_probe.py'],
    ['svy_contrast_validation.py'],
    ['contrast_simulation.py'],
    ['cluster_simulation.py'],
    ['brfss_year_comparison.py'],
    ['brfss_3year_check.py'],
    ['annual_contrast_probe.py'],
    ['annual_direct_validation.py'],
    ['annual_simulation.py'],
    ['verify_brfss.py'],
    ['make_figures.py'],
    ['make_research_summary.py'],
]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def main():
    print('This run replaces generated findings, results, and figures.',flush=True)
    for index,command in enumerate(STEPS,1):
        print(f'[{index}/{len(STEPS)}] {" ".join(command)}',flush=True)
        subprocess.run([sys.executable,*command],cwd=HERE,check=True)
    sources=['uci-diabetes-130-hospitals.zip','brfss-2023-mirror.parquet',
             'brfss-2024-mirror.parquet','brfss-2025-mirror.parquet']
    scripts=['readmission_experiment.py','model_experiment.py','robustness_experiment.py',
             'standardization_experiment.py','brfss_prepare_mirror.py','brfss_analysis.py',
             'brfss_access_context.py','brfss_access_standardization.py','access_missingness_audit.py','verify_access_missingness.py',
             'missingness_standardized_probe.py','missingness_svy_validation.py','access_uncertainty_probe.py',
             'access_svy_score_validation.py','access_svy_nonlinear_validation.py','access_bootstrap_probe.py',
             'brfss_design_audit.py','survey_variance_probe.py','standardized_contrast_probe.py','svy_contrast_validation.py','contrast_simulation.py','cluster_simulation.py',
             'brfss_year_comparison.py','brfss_3year_check.py','annual_contrast_probe.py','annual_direct_validation.py','annual_simulation.py',
             'verify_brfss.py','make_figures.py','make_research_summary.py','test_experiments.py','test_annual_contrast.py','test_access_bootstrap.py','run_pipeline.py']
    record={'finished_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,
            'platform':platform.platform(),'input_sha256':{name:sha(HERE/name) for name in sources},
            'script_sha256':{name:sha(HERE/name) for name in scripts},
            'note':'Successful completion of all steps; hashes identify inputs and code. See reports for package and method limitations.'}
    (HERE/'pipeline-run.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('Pipeline complete; see research-synthesis.md and pipeline-run.json.',flush=True)


if __name__=='__main__':main()
