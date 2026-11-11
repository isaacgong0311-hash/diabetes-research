"""Sensitivity analyses for the historical readmission research.

Requires NumPy. Run from this folder with Python and NumPy installed.
"""
import json
from datetime import date
from pathlib import Path

import numpy as np

from model_experiment import cohort_from, fit_predict, make_features, measures
from readmission_experiment import EXCLUDED, load, pct, stats

HERE = Path(__file__).resolve().parent
SEEDS = [1729, 11, 42, 99, 2026]


def split(y, seed):
    rng = np.random.default_rng(seed)
    train, test = [], []
    for outcome in (0, 1):
        indices = np.flatnonzero(y == outcome)
        rng.shuffle(indices)
        cut = int(len(indices) * 0.8)
        train.extend(indices[:cut]); test.extend(indices[cut:])
    train, test = np.asarray(train), np.asarray(test)
    rng.shuffle(train); rng.shuffle(test)
    return train, test


def summarized(rows):
    none = [r for r in rows if int(r['number_inpatient']) == 0]
    prior = [r for r in rows if int(r['number_inpatient']) > 0]
    return {'all': stats(rows), 'none': stats(none), 'prior': stats(prior)}


def main():
    rows, digest = load()
    main_cohort = cohort_from(rows)
    eligible_first = {}
    for r in rows:
        if r['discharge_disposition_id'] in EXCLUDED:
            continue
        pid = r['patient_nbr']
        if pid not in eligible_first or int(r['encounter_id']) < int(eligible_first[pid]['encounter_id']):
            eligible_first[pid] = r
    alternate = list(eligible_first.values())
    all_eligible = [r for r in rows if r['discharge_disposition_id'] not in EXCLUDED]
    groups = {'main_first_then_exclude':summarized(main_cohort),
              'exclude_then_first':summarized(alternate),
              'all_eligible_encounters':summarized(all_eligible)}
    y = np.asarray([r['readmitted'] == '<30' for r in main_cohort], dtype=int)
    x = make_features(main_cohort)
    runs=[]
    for seed in SEEDS:
        train,test=split(y,seed)
        assert not set(train).intersection(test)
        p_prior,prior_gradient=fit_predict(x[train,1:2],y[train],x[test,1:2])
        p_full,full_gradient=fit_predict(x[train],y[train],x[test])
        runs.append({'seed':seed,'test_n':len(test),'test_events':int(y[test].sum()),
                     'prior':measures(y[test],p_prior),'expanded':measures(y[test],p_full),
                     'gradient_norm':{'prior':prior_gradient,'expanded':full_gradient}})
    # Negative control: an independent permutation breaks the association in training labels.
    train,test=split(y,SEEDS[0]); rng=np.random.default_rng(9182)
    shuffled = rng.permutation(y[train])
    predicted, gradient = fit_predict(x[train],shuffled,x[test])
    negative = {'seed':9182, 'test_metrics':measures(y[test],predicted), 'gradient_norm':gradient}
    results={'archive_sha256':digest,'cohort_sensitivity':groups,'random_splits':runs,'permuted_training_labels':negative}
    (HERE/'robustness_results.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    group_rows=['| Selection method | Units | Overall rate | No prior visits: n; rate | One or more: n; rate |',
                '|---|---:|---:|---:|---:|']
    labels={'main_first_then_exclude':'First encounter, then exclude','exclude_then_first':'Exclude, then first eligible encounter','all_eligible_encounters':'All eligible encounters'}
    for key,result in groups.items():
        group_rows.append(f"| {labels[key]} | {result['all']['n']:,} | {pct(result['all']['rate'])} | {result['none']['n']:,}; {pct(result['none']['rate'])} | {result['prior']['n']:,}; {pct(result['prior']['rate'])} |")
    split_rows=['| Split seed | Test patients | Test events | Prior-only AUC | Expanded AUC | Expanded average precision | Expanded Brier |',
                '|---|---:|---:|---:|---:|---:|---:|']
    for r in runs:
        split_rows.append(f"| {r['seed']} | {r['test_n']:,} | {r['test_events']:,} | {r['prior']['auc']:.3f} | {r['expanded']['auc']:.3f} | {r['expanded']['average_precision']:.3f} | {r['expanded']['brier']:.4f} |")
    report=f'''# Robustness checks: diabetes readmission experiments

Run date: {date.today().isoformat()}. Data source: [UCI Diabetes 130-US Hospitals, 1999–2008](https://doi.org/10.24432/C5230J). These are retrospective exploratory checks, not clinical validation. See [findings.md](findings.md) and [extended-findings.md](extended-findings.md) for definitions and limitations.

## Experiment 8: effect of cohort selection

The main analysis selects the smallest encounter ID for each patient, then excludes death/hospice. The alternative excludes those encounters first and selects the smallest remaining ID for each patient, potentially including a later encounter. The third approach includes every eligible encounter, so the same patient can contribute more than once.

{chr(10).join(group_rows)}

All rates are raw descriptions. The first two analyses contain one encounter per patient; the all-encounter analysis is encounter-weighted, so it is not a rate for unique patients. Encounter ID is a proxy for ordering, and we cannot verify dates from this file. These comparisons reflect both inclusion and weighting changes, not a randomized experiment.

## Experiment 9: repeated patient-level splits

Five fixed random seeds produce five stratified 80/20 patient splits. Each model is re-trained from scratch on its training split; preprocessing is fitted only there. The test groups overlap across runs, so this is a stability check on the same historical dataset, not five independent replications or external validation. The first seed reproduces the original held-out experiment.

{chr(10).join(split_rows)}

The expanded model uses age-band midpoint, prior inpatient/emergency/outpatient visits, length of stay, laboratory test count, medication count, and diagnoses count. Its test AUC ranges from **{min(r['expanded']['auc'] for r in runs):.3f} to {max(r['expanded']['auc'] for r in runs):.3f}** over these seeds. Comparing that range with the original single split helps show sampling sensitivity but is not a confidence interval.

## Experiment 10: shuffled-label negative control

For seed {SEEDS[0]}, we randomly permuted the training outcomes while keeping the test outcomes intact. The expanded model trained on scrambled labels obtained test AUC **{negative['test_metrics']['auc']:.3f}**, average precision **{negative['test_metrics']['average_precision']:.3f}**, and Brier score **{negative['test_metrics']['brier']:.4f}**. It should generally perform near chance on average; any single random shuffle can deviate from 0.5. This control checks that the pipeline does not automatically produce a useful ranking from scrambled training labels; it does not prove absence of all leakage or confounding.

## Reproduce and interpret

Run `python robustness_experiment.py` with NumPy installed and the other experiment scripts in the same directory. Machine-readable outputs are in `robustness_results.json`; the original archive has SHA-256 `{digest}`. All three analyses use the same data source; repeated random splits are not an independent dataset. No study here demonstrates causality, transport to a new hospital, clinical benefit, or suitability for an individual patient.
'''
    (HERE/'robustness-findings.md').write_text(report,encoding='utf-8')
    print(f"Runs: {len(runs)}; expanded AUC range {min(r['expanded']['auc'] for r in runs):.3f}–{max(r['expanded']['auc'] for r in runs):.3f}; shuffled-label AUC {negative['test_metrics']['auc']:.3f}")


if __name__ == '__main__':
    main()
