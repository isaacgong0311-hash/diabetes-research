"""Build a concise index of completed missing-data sensitivity experiments."""
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = ['missing-covariate-scenarios-results.json', 'hotdeck-sensitivity-results.json',
          'hotdeck-balance-audit-results.json', 'hotdeck-health-sensitivity-results.json',
          'hotdeck-repeated-masking-results.json', 'missingness-pipeline-run.json']


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    before = {name: sha(HERE / name) for name in INPUTS}
    fixed = load(INPUTS[0]); donor = load(INPUTS[1]); balance = load(INPUTS[2])
    health = load(INPUTS[3]); repeated = load(INPUTS[4])
    manifest = load(INPUTS[5])
    for name in INPUTS[:5]:
        if manifest['output_sha256'].get(name) != before[name]:
            raise ValueError(f'{name} differs from the completed supplemental pipeline')
    low = fixed['fixed_reference_minimum']['fixed_reference_difference']
    high = fixed['fixed_reference_maximum']['fixed_reference_difference']
    all_balance = balance['summaries']['all']
    original = repeated['summary']['income']['original']
    matched = repeated['summary']['income']['health']
    report = f'''# Missing-data experiments: synthesis

Updated: {date.today().isoformat()}. These are exploratory analyses of 2023 BRFSS responses from 48 states and DC, not clinical advice, causal estimates, or nationally complete results. The diabetes question does not identify diabetes type. See the broader [research synthesis](research-synthesis.md) for the data and provenance.

## Question and denominator

Among {donor['domain_n']:,} respondents with known age and definite diabetes and cost-barrier responses, {donor['recipient_n']:,} lack income, insurance, or both. The detailed standardization cannot directly use their unknown categories. In the original analysis, people with unknown age are also excluded.

## What the experiments found

1. **Strong fixed assignments:** Across 36 homogeneous hypothetical assignments, the diabetes-minus-no-diabetes cost-barrier gap ranges from {100*low:+.2f} to {100*high:+.2f} percentage points with the complete-case reference population held fixed. These assignments are not exhaustive, statistical bounds, or claims about the missing values. [Scenario details](missing-covariate-scenarios.md).
2. **Weighted donor draws:** Selecting respondents with matching age band, diabetes response, cost response, and any observed covariate produced an average fixed-reference gap of {100*donor['fixed_reference']['mean']:+.2f} percentage points across {donor['draws']} draws. The draw-to-draw SD was {100*donor['fixed_reference']['sd_between_draws']:.2f} points; it is **not** a confidence interval and excludes survey sampling and donor-model uncertainty. [Donor experiment](hotdeck-sensitivity.md).
3. **Observed mismatch:** Among recipients with known general health, {100*all_balance['recipient_rate']:.1f}% reported fair or poor health, versus {100*all_balance['donor_pool_rate_reweighted']:.1f}% in their eligible donor pools after matching the recipient pool mix. The descriptive difference does not determine how missing income or insurance differs. [Balance audit](hotdeck-balance-audit.md).
4. **Alternative matching:** Adding general health to donor matching gave an average gap of {100*health['fixed_reference_mean']:+.2f} points in a separate {health['draws']}-draw run, compared with {100*health['baseline_fixed_mean']:+.2f} points without health matching. Some pools became very small; the minimum donor count was {health['minimum_donor_n']}. [Alternative matching](hotdeck-health-sensitivity.md).
5. **Artificial holdouts:** Across {repeated['splits']} random splits of respondents whose answers were known, mean weighted income-band accuracy was {100*original['mean_accuracy']:.1f}% with the original donor rule and {100*matched['mean_accuracy']:.1f}% with health matching. These are random donor draws, not optimized individual predictions. The respondents' outcomes, age, and diabetes response were known to the matcher. [Repeated masking](hotdeck-repeated-masking.md).

The donor method assumes that observed donors are informative about missing respondents within the chosen matching cells. Randomly hiding answers among complete respondents cannot verify that assumption for people who did not answer; health imbalance and small donor pools make independent scrutiny especially important. None of the experiments estimates a treatment effect, fixes missing-data bias, or supplies valid survey confidence intervals after imputation. Unmeasured factors, self-report, survey nonresponse, and absent states remain relevant.

## Reproduce

Run the main `python run_pipeline.py`, then `python run_missingness_pipeline.py`, then `python summarize_missingness_research.py`. The supplemental pipeline records input, script, and output hashes; this synthesis verifies its source results against that completed run and records its own input hashes in `missingness-synthesis-provenance.json`.
'''
    (HERE / 'missingness-synthesis.md').write_text(report, encoding='utf-8')
    if before != {name: sha(HERE / name) for name in INPUTS}:
        raise RuntimeError('Inputs changed while building the synthesis')
    provenance = {'finished_utc': datetime.now(timezone.utc).isoformat(), 'input_sha256': before,
                  'script_sha256': sha(HERE / 'summarize_missingness_research.py'),
                  'output_sha256': sha(HERE / 'missingness-synthesis.md')}
    (HERE / 'missingness-synthesis-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    print('Wrote missingness-synthesis.md and verified inputs against supplemental pipeline hashes.')


if __name__ == '__main__':
    main()
