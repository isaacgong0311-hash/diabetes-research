"""Repeat donor-method masking checks across several random holdout splits."""
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

SEED = 83710
SPLITS = 8
DRAWS_PER_SPLIT = 10


def main():
    rng = np.random.default_rng(SEED)
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
    prior = json.loads((HERE / 'brfss-access-standardization-results.json').read_text(encoding='utf-8'))
    if len(d) != prior['complete_n']:
        raise ValueError('Complete-case domain does not match previous analysis')
    reference = np.bincount(age * 6 + income * 2 + insurance, weights=weight, minlength=18)
    reference /= reference.sum()
    truth_rates, _ = scenario_estimate(weight, age, income, insurance, group, outcome, 0, 0, reference)
    truth = truth_rates[1] - truth_rates[0]
    records = []
    for split in range(SPLITS):
        holdout = rng.random(len(d)) < .20
        for mode in ('income', 'insurance', 'both'):
            masked_income, masked_insurance = income.copy(), insurance.copy()
            if mode in ('income', 'both'):
                masked_income[holdout] = -1
            if mode in ('insurance', 'both'):
                masked_insurance[holdout] = -1
            original = build_pools(age, group, outcome, masked_income, masked_insurance, weight)
            expanded = add_health_matching(original, health, weight)
            actual = income if mode == 'income' else insurance if mode == 'insurance' else income * 2 + insurance
            for rule, pools in [('original', original), ('health', expanded)]:
                if sum(len(p['recipients']) for p in pools) != holdout.sum():
                    raise ValueError('Incorrect number of holdout recipients')
                if any(np.any(holdout[p['donors']]) for p in pools):
                    raise ValueError('Held-out case used as donor')
                accuracies, errors = [], []
                for _ in range(DRAWS_PER_SPLIT):
                    inc, ins = impute_once(masked_income, masked_insurance, pools, rng)
                    predicted = inc if mode == 'income' else ins if mode == 'insurance' else inc * 2 + ins
                    accuracies.append(weighted_accuracy(actual[holdout], predicted[holdout], weight[holdout]))
                    rates, _ = scenario_estimate(weight, age, inc, ins, group, outcome, 0, 0, reference)
                    errors.append(rates[1] - rates[0] - truth)
                records.append({'split': split + 1, 'mode': mode, 'rule': rule, 'holdout_n': int(holdout.sum()),
                                'mean_accuracy': float(np.mean(accuracies)), 'mean_gap_error': float(np.mean(errors)),
                                'minimum_donor_n': min(len(p['donors']) for p in pools),
                                'fallback_recipients': sum(len(p['recipients']) for p in pools if p.get('fallback', False))})
        print(f'Completed random split {split + 1}/{SPLITS}', flush=True)
    summary = {}
    for mode in ('income', 'insurance', 'both'):
        summary[mode] = {}
        for rule in ('original', 'health'):
            subset = [r for r in records if r['mode'] == mode and r['rule'] == rule]
            accuracy = np.array([r['mean_accuracy'] for r in subset])
            error = np.array([r['mean_gap_error'] for r in subset])
            summary[mode][rule] = {'mean_accuracy': float(accuracy.mean()), 'split_sd_accuracy': float(accuracy.std(ddof=1)),
                                   'mean_gap_error': float(error.mean()), 'split_sd_gap_error': float(error.std(ddof=1)),
                                   'min_donor_n': min(r['minimum_donor_n'] for r in subset),
                                   'max_fallback_recipients': max(r['fallback_recipients'] for r in subset)}
    result = {'seed': SEED, 'splits': SPLITS, 'draws_per_rule_pattern_split': DRAWS_PER_SPLIT,
              'complete_n': len(d), 'truth_gap': float(truth), 'summary': summary, 'splits_detail': records,
              'limitation': 'Artificial random masking among observed respondents; no inference for real missing cases.'}
    (HERE / 'hotdeck-repeated-masking-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    labels = {'income': 'Income only', 'insurance': 'Insurance only', 'both': 'Income and insurance'}
    rows = []
    for mode, label in labels.items():
        for rule, rule_label in (('original', 'Original'), ('health', 'Health matched')):
            v = summary[mode][rule]
            rows.append(f"| {label} | {rule_label} | {100*v['mean_accuracy']:.1f}% | {100*v['split_sd_accuracy']:.2f} | {100*v['mean_gap_error']:+.3f} | {100*v['split_sd_gap_error']:.3f} |")
    report = f'''# Repeated artificial-masking checks for donor matching

Run date: {date.today().isoformat()}. This is a repeatability check among respondents with known answers; it cannot validate imputation for the actually missing cases.

Starting with {len(d):,} complete respondents, we created {SPLITS} independently generated random holdout splits, each targeting 20% of records (seed {SEED}). For each split we masked income only, insurance only, or both; holdout records could not donate. The original and health-matched donor rules each generated {DRAWS_PER_SPLIT} random completed datasets per pattern and split. Both use the same fixed complete-case reference distribution and the known complete-case comparison gap of {100*truth:+.3f} percentage points. Each table row summarizes the split-level mean of the donor draws. Matching rules and fallback are described in the [health-matched experiment](hotdeck-health-sensitivity.md).

| Hidden fields | Rule | Mean weighted accuracy | SD across split accuracies, percentage points | Mean gap error, points | SD across split gap errors, points |
|---|---|---:|---:|---:|---:|
{chr(10).join(rows)}

Gap error is the reconstructed gap minus the known complete-case gap. Both-field accuracy requires both categories to match. Split SDs summarize this small set of overlapping random splits, including finite donor-draw noise; they are **not** independent-study standard errors or confidence intervals. Accuracies target individual guesses, while the gap error targets a population summary, so one can improve without the other. The smallest health-matched pool observed across all splits contained {min(summary[m]['health']['min_donor_n'] for m in summary)} donor(s).

Random masking of observed cases is much easier to study than real nonresponse. These results do not establish that missing answers are missing at random, demonstrate donor exchangeability for those respondents, include complex-survey variance, or justify clinical conclusions. The true missing-income or insurance distributions remain unknown. Pool details and split results are in `hotdeck-repeated-masking-results.json`.

## Reproduce

Run `python hotdeck_repeated_masking.py` after producing the complete-case analysis, with NumPy and pandas installed. Seed {SEED} and the numbers of splits and draws are fixed in the script. No individual imputations or donor links are saved.
'''
    (HERE / 'hotdeck-repeated-masking.md').write_text(report, encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
