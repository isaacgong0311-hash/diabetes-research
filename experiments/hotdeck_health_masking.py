"""Compare original and health-matched donor rules on the same artificial holdout."""
import json
import os
import sys
from datetime import date
from pathlib import Path

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '.surveydeps'))
import numpy as np
import pandas as pd

from hotdeck_sensitivity import build_pools, impute_once
from hotdeck_health_sensitivity import add_health_matching
from hotdeck_masking_validation import weighted_accuracy
from missing_covariate_scenarios import scenario_estimate

SEED = 67032
DRAWS = 50


def main():
    baseline = json.loads((HERE / 'hotdeck-masking-validation-results.json').read_text(encoding='utf-8'))
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    domain = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)
              & d['_INCOMG1'].between(1, 7) & d['_HLTHPL1'].isin([1, 2])).to_numpy()
    d = d.loc[domain]
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    income = np.select([d['_INCOMG1'] <= 2, d['_INCOMG1'] <= 4], [0, 1], default=2)
    insurance = np.where(d['_HLTHPL1'] == 1, 0, 1)
    group = (d.DIABETE4 == 1).to_numpy().astype(int)
    outcome = (d.MEDCOST1 == 1).to_numpy().astype(int)
    health = np.select([d.GENHLTH.isin([1, 2, 3]), d.GENHLTH.isin([4, 5])], [0, 1], default=2)
    weight = d['_LLCPWT'].to_numpy(dtype=float)
    rng = np.random.default_rng(SEED)
    holdout = rng.random(len(d)) < baseline['holdout_fraction']
    if len(d) != baseline['complete_n'] or int(holdout.sum()) != baseline['results']['income']['holdout_n']:
        raise ValueError('Unable to reproduce the baseline holdout split')
    reference = np.bincount(age * 6 + income * 2 + insurance, weights=weight, minlength=18)
    reference /= reference.sum()
    truth_rates, _ = scenario_estimate(weight, age, income, insurance, group, outcome, 0, 0, reference)
    truth = truth_rates[1] - truth_rates[0]
    results = {}
    for mode in ('income', 'insurance', 'both'):
        masked_income, masked_insurance = income.copy(), insurance.copy()
        if mode in ('income', 'both'):
            masked_income[holdout] = -1
        if mode in ('insurance', 'both'):
            masked_insurance[holdout] = -1
        pools = add_health_matching(build_pools(age, group, outcome, masked_income, masked_insurance, weight), health, weight)
        fallback_n = sum(len(p['recipients']) for p in pools if p['fallback'])
        actual = income if mode == 'income' else insurance if mode == 'insurance' else income * 2 + insurance
        accuracy, contrasts = [], []
        for _ in range(DRAWS):
            filled_income, filled_insurance = impute_once(masked_income, masked_insurance, pools, rng)
            predicted = (filled_income if mode == 'income' else filled_insurance if mode == 'insurance'
                         else filled_income * 2 + filled_insurance)
            accuracy.append(weighted_accuracy(actual[holdout], predicted[holdout], weight[holdout]))
            rates, _ = scenario_estimate(weight, age, filled_income, filled_insurance, group, outcome, 0, 0, reference)
            contrasts.append(rates[1] - rates[0])
        contrasts = np.asarray(contrasts)
        results[mode] = {'accuracy': float(np.mean(accuracy)), 'gap_mean': float(contrasts.mean()),
                         'gap_minus_truth': float(contrasts.mean() - truth),
                         'gap_draw_sd': float(contrasts.std(ddof=1)),
                         'min_donors': min(len(p['donors']) for p in pools),
                         'fallback_recipients': fallback_n, 'pool_count': len(pools)}
        print(f"{mode}: health-matched accuracy {100*np.mean(accuracy):.1f}%; fallback {fallback_n}", flush=True)
    result = {'seed': SEED, 'draws_per_mode': DRAWS, 'holdout_n': int(holdout.sum()),
              'truth_gap': float(truth), 'health_matched': results, 'original': baseline['results'],
              'limitation': 'Single random split of observed cases; does not validate truly missing answers.'}
    (HERE / 'hotdeck-health-masking-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    labels = {'income': 'Income only', 'insurance': 'Insurance only', 'both': 'Income and insurance'}
    rows = []
    for mode, label in labels.items():
        a, b = baseline['results'][mode], results[mode]
        rows.append(f"| {label} | {100*a['weighted_accuracy_mean']:.1f}% | {100*b['accuracy']:.1f}% | {100*a['contrast_bias_from_masking']:+.3f} | {100*b['gap_minus_truth']:+.3f} | {b['fallback_recipients']:,} |")
    report = f'''# Holdout comparison of donor matching rules

Run date: {date.today().isoformat()}. This is an artificial masking experiment, not a validation on actually missing responses.

We reuse the same {int(holdout.sum()):,}-person random holdout of complete respondents from the [original masking experiment](hotdeck-masking-validation.md). For each hidden-field pattern, the original donor matching rule is compared with splitting pools by general health as in the [health-matched sensitivity experiment](hotdeck-health-sensitivity.md). General health unknown is treated as its own category; when no donor exists in a health category, the original pool is used. The health-matched runs use {DRAWS} donor draws per pattern. Both methods use the same held-out respondents and fixed complete-case reference distribution, but different random donor draws.

| Hidden fields | Original weighted accuracy | Health-matched weighted accuracy | Original gap error, points | Health-matched gap error, points | Holdouts using fallback |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Gap error means mean reconstructed standardized gap minus the fully observed gap ({100*truth:+.3f} percentage points). Accuracy for the two-field pattern requires both categories to be correct. These results are descriptive for **one random split**; the variance of donor draws and uncertainty across holdout splits are not shown in the table. The smallest health-matched donor pool across patterns had {min(r['min_donors'] for r in results.values())} donor(s). Additional conditioning may improve, worsen, or barely change a particular metric while creating sparse pools.

Holdouts have observed income and insurance and were masked randomly, unlike genuinely missing cases. Similar or higher accuracy on them does not establish validity for nonrespondents, and matching general health does not prove missing-at-random or a causal effect. Survey-design variance and donor-model uncertainty are not estimated. Full summaries are in `hotdeck-health-masking-results.json`.

## Reproduce

Run `python hotdeck_masking_validation.py` followed by `python hotdeck_health_masking.py` with NumPy and pandas installed. No person-level donor links are saved.
'''
    (HERE / 'hotdeck-health-masking.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
