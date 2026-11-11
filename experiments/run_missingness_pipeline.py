"""Rebuild the supplemental missing-covariate experiments and verify inputs.

This replaces their generated reports, results, and scenario figures. Requires
NumPy, pandas, and matplotlib; run the main pipeline first.
"""
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = [
    ['-m', 'unittest', '-v', 'test_missing_covariate_scenarios.py', 'test_hotdeck_sensitivity.py'],
    ['missing_covariate_scenarios.py'],
    ['plot_missing_covariate_scenarios.py'],
    ['hotdeck_sensitivity.py'],
    ['hotdeck_masking_validation.py'],
    ['hotdeck_balance_audit.py'],
    ['hotdeck_health_sensitivity.py'],
    ['hotdeck_health_masking.py'],
    ['hotdeck_repeated_masking.py'],
]
INPUTS = ['brfss2023-selected.csv.gz', 'missingness-standardized-probe-results.json',
          'brfss-access-standardization-results.json', 'pipeline-run.json']
SCRIPTS = ['missing_covariate_scenarios.py', 'plot_missing_covariate_scenarios.py',
           'hotdeck_sensitivity.py', 'hotdeck_masking_validation.py', 'hotdeck_balance_audit.py',
           'hotdeck_health_sensitivity.py', 'hotdeck_health_masking.py', 'hotdeck_repeated_masking.py',
           'test_missing_covariate_scenarios.py', 'test_hotdeck_sensitivity.py', 'run_missingness_pipeline.py']
OUTPUTS = ['missing-covariate-scenarios.md', 'missing-covariate-scenarios-results.json',
           'figure_missing_covariate_scenarios.png', 'figure_missing_covariate_scenarios.svg',
           'figure_missing_covariate_fixed.png', 'figure_missing_covariate_fixed.svg',
           'hotdeck-sensitivity.md', 'hotdeck-sensitivity-results.json',
           'hotdeck-masking-validation.md', 'hotdeck-masking-validation-results.json',
           'hotdeck-balance-audit.md', 'hotdeck-balance-audit-results.json',
           'hotdeck-health-sensitivity.md', 'hotdeck-health-sensitivity-results.json',
           'hotdeck-health-masking.md', 'hotdeck-health-masking-results.json',
           'hotdeck-repeated-masking.md', 'hotdeck-repeated-masking-results.json']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    before = {name: sha(HERE / name) for name in INPUTS}
    scripts = {name: sha(HERE / name) for name in SCRIPTS}
    print('Rebuilding supplemental missingness reports and figures.', flush=True)
    for number, command in enumerate(STEPS, 1):
        print(f'[{number}/{len(STEPS)}] {" ".join(command)}', flush=True)
        subprocess.run([sys.executable, *command], cwd=HERE, check=True)
    after = {name: sha(HERE / name) for name in INPUTS}
    if before != after:
        raise RuntimeError('An upstream input changed during the run; repeat after resolving concurrent changes')
    if scripts != {name: sha(HERE / name) for name in SCRIPTS}:
        raise RuntimeError('A script changed during the run; repeat after resolving concurrent changes')
    record = {'finished_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
              'platform': platform.platform(), 'input_sha256': before, 'script_sha256': scripts,
              'output_sha256': {name: sha(HERE / name) for name in OUTPUTS},
              'note': 'Completed supplemental steps; hashes record files, not the validity of statistical assumptions.'}
    (HERE / 'missingness-pipeline-run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print('Supplemental pipeline complete; see missingness-pipeline-run.json.', flush=True)


if __name__ == '__main__':
    main()
