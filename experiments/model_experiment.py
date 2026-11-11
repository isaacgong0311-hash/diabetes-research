"""Patient-held-out readmission models, subgroup checks, and age-stratified rates.

Requires NumPy. This is a historical data experiment, not a clinical tool.
"""
from __future__ import annotations

import json
import math
import os
from datetime import date
from pathlib import Path

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np

from readmission_experiment import EXCLUDED, load, pct, stats

HERE = Path(__file__).resolve().parent
SEED = 1729
AGE_BANDS = [('0–39',0,40),('40–59',40,60),('60–79',60,80),('80+',80,110)]


def age(row):
    return int(row['age'].lstrip('[').split('-')[0]) + 5


def cohort_from(rows):
    first = {}
    for r in rows:
        patient = r['patient_nbr']
        if patient not in first or int(r['encounter_id']) < int(first[patient]['encounter_id']):
            first[patient] = r
    return [r for r in first.values() if r['discharge_disposition_id'] not in EXCLUDED]


def auc(y, p):
    order = np.argsort(p, kind='mergesort')
    sorted_p = p[order]
    edges = np.r_[0, np.flatnonzero(np.diff(sorted_p)) + 1, len(y)]
    rank_sums = float(np.dot((edges[:-1] + 1 + edges[1:]) / 2.0,
                             np.add.reduceat(y[order], edges[:-1])))
    positives = int(y.sum()); negatives = len(y)-positives
    return float((rank_sums - positives*(positives+1)/2)/(positives*negatives)) if positives and negatives else float('nan')


def average_precision(y, p):
    order = np.argsort(-p, kind='mergesort')
    y, p = y[order], p[order]
    ends = np.r_[np.flatnonzero(np.diff(p)) + 1, len(y)]
    cumulative = np.cumsum(y)
    tp = cumulative[ends-1]
    return float(np.sum((tp - np.r_[0,tp[:-1]]) * (tp/ends)) / tp[-1])


def measures(y, p):
    return {'auc':auc(y,p), 'average_precision':average_precision(y,p), 'brier':float(np.mean((p-y)**2))}


def make_features(rows):
    result = []
    for r in rows:
        result.append([age(r), math.log1p(int(r['number_inpatient'])),
                       math.log1p(int(r['number_emergency'])), math.log1p(int(r['number_outpatient'])),
                       int(r['time_in_hospital']), int(r['num_lab_procedures']),
                       int(r['num_medications']), int(r['number_diagnoses'])])
    return np.asarray(result,dtype=float)


def fit_predict(x, y, test):
    # Fixed, prespecified gradient descent; preprocessing is learned from training data only.
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale==0] = 1
    x = np.column_stack((np.ones(len(x)),(x-mean)/scale))
    test = np.column_stack((np.ones(len(test)),(test-mean)/scale))
    weights = np.zeros(x.shape[1]); weights[0] = math.log(y.mean()/(1-y.mean()))
    for _ in range(600):
        prob = 1/(1+np.exp(-np.clip(x@weights,-30,30)))
        grad = (x.T@(prob-y))/len(y)
        grad[1:] += 0.001*weights[1:]
        weights -= 0.3*grad
    p = 1/(1+np.exp(-np.clip(test@weights,-30,30)))
    return p, float(np.linalg.norm(grad))


def operating(y, p, threshold):
    predicted = p >= threshold
    tp=int(np.sum(predicted & (y==1))); fp=int(np.sum(predicted & (y==0)))
    fn=int(np.sum(~predicted & (y==1))); tn=int(np.sum(~predicted & (y==0)))
    return {'threshold':threshold,'tp':tp,'fp':fp,'fn':fn,'tn':tn,'flagged':tp+fp,
            'sensitivity':tp/(tp+fn), 'ppv':tp/(tp+fp) if tp+fp else None}


def main():
    rows, digest = load(); data = cohort_from(rows)
    y=np.asarray([r['readmitted']=='<30' for r in data],dtype=int)
    features=make_features(data)
    rng=np.random.default_rng(SEED)
    # Patient-level split: the cohort has one row per patient. Stratification preserves outcome prevalence.
    train=[]; test=[]
    for outcome in (0,1):
        indices=np.flatnonzero(y==outcome); rng.shuffle(indices)
        cut=int(len(indices)*0.8);train.extend(indices[:cut]);test.extend(indices[cut:])
    train=np.asarray(train);test=np.asarray(test);rng.shuffle(train);rng.shuffle(test)
    train_y,test_y=y[train],y[test]
    baseline=np.full(len(test),train_y.mean())
    prior,prior_grad=fit_predict(features[train,1:2],train_y,features[test,1:2])
    full,full_grad=fit_predict(features[train],train_y,features[test])
    evaluations={'baseline':measures(test_y,baseline),'prior_visits':measures(test_y,prior),'expanded':measures(test_y,full)}
    operating_points=[operating(test_y,full,t) for t in (0.10,0.20)]
    calibration=[]
    # Equal-count risk groups are descriptive, not cross-validated estimates of calibration.
    for i,ids in enumerate(np.array_split(np.argsort(full),10),1):
        calibration.append({'decile':i,'n':len(ids),'predicted':float(full[ids].mean()),'observed':float(test_y[ids].mean())})
    age_strata=[]
    for label,low,high in AGE_BANDS:
        subset=[r for r in data if low<=age(r)<high]
        no=[r for r in subset if int(r['number_inpatient'])==0]
        any_prior=[r for r in subset if int(r['number_inpatient'])>0]
        age_strata.append({'band':label,'none':stats(no),'one_or_more':stats(any_prior)})
    subgroup=[]
    for label,low,high in AGE_BANDS:
        idx=np.asarray([i for i,j in enumerate(test) if low<=age(data[j])<high])
        if len(idx) and 0<test_y[idx].sum()<len(idx):
            subgroup.append({'band':label,'n':len(idx),'events':int(test_y[idx].sum()),'auc':auc(test_y[idx],full[idx]),'brier':float(np.mean((full[idx]-test_y[idx])**2))})
    # Paired bootstrap reflects test-set sampling uncertainty, not model-development uncertainty.
    boot=[]
    for _ in range(200):
        ids=rng.integers(0,len(test),len(test))
        boot.append([auc(test_y[ids],full[ids]),auc(test_y[ids],full[ids])-auc(test_y[ids],prior[ids])])
    boot=np.asarray(boot)
    intervals={'auc':np.quantile(boot[:,0],[.025,.975]).tolist(),'auc_difference':np.quantile(boot[:,1],[.025,.975]).tolist()}
    result={'seed':SEED,'archive_sha256':digest,'cohort_n':len(data),'train_n':len(train),'test_n':len(test),'test_events':int(test_y.sum()),'models':evaluations,'gradient_norm':{'prior':prior_grad,'expanded':full_grad},'bootstrap_200_percentile_intervals':intervals,'operating_points':operating_points,'calibration_deciles':calibration,'age_strata':age_strata,'age_test_subgroups':subgroup}
    (HERE/'model_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    def metric_table():
        out=['| Model | ROC AUC | Average precision | Brier score |','|---|---:|---:|---:|']
        for name,label in [('baseline','Constant training prevalence'),('prior_visits','Prior inpatient visits only'),('expanded','Expanded model')]:
            m=evaluations[name];out.append(f"| {label} | {m['auc']:.3f} | {m['average_precision']:.3f} | {m['brier']:.4f} |")
        return '\n'.join(out)
    age_rows=['| Age band | No prior inpatient visits: n; rate | One or more: n; rate |','|---|---:|---:|']
    for x in age_strata:
        n,p=x['none'],x['one_or_more'];age_rows.append(f"| {x['band']} | {n['n']:,}; {pct(n['rate'])} | {p['n']:,}; {pct(p['rate'])} |")
    op_rows=['| Threshold | Flagged | True positives | False positives | Sensitivity | Positive predictive value |','|---|---:|---:|---:|---:|---:|']
    for x in operating_points:op_rows.append(f"| {pct(x['threshold'])} | {x['flagged']:,} | {x['tp']:,} | {x['fp']:,} | {pct(x['sensitivity'])} | {pct(x['ppv'])} |")
    cal_rows=['| Risk tenth, lowest to highest | n | Mean predicted risk | Observed event rate |','|---|---:|---:|---:|']
    for x in calibration:cal_rows.append(f"| {x['decile']} | {x['n']:,} | {pct(x['predicted'])} | {pct(x['observed'])} |")
    sub_rows=['| Age band | Test patients | Events | ROC AUC | Brier score |','|---|---:|---:|---:|---:|']
    for x in subgroup:sub_rows.append(f"| {x['band']} | {x['n']:,} | {x['events']:,} | {x['auc']:.3f} | {x['brier']:.4f} |")
    report=f'''# Extended readmission experiments

Run date: {date.today().isoformat()}. These experiments use the historical [UCI diabetes hospital dataset](https://doi.org/10.24432/C5230J). They are exploratory, not suitable for medical decision-making.

## Cohort and setup

We reused the cohort defined in [findings.md](findings.md): one encounter per patient using the smallest encounter ID as a proxy for the earliest recorded encounter, followed by exclusions for death or hospice. It contains {len(data):,} patients. Diabetes type is not restricted to type 2. We randomly split patients, stratified by the recorded <30-day readmission outcome, into {len(train):,} training and {len(test):,} test patients (seed {SEED}); {int(test_y.sum()):,} test patients had an event. No patient appears in both sets.

The expanded logistic model uses age-band midpoint, log-transformed prior inpatient, emergency and outpatient visits, length of stay, number of lab procedures, number of medications, and number of diagnoses. These are encounter-level data available by discharge, not necessarily at admission. It excludes sex and race, but the other features can still reflect unequal access or care. All scaling uses training data only. The model uses fixed settings with no test-set tuning. The prior-only model uses just prior inpatient visits; the constant model assigns the training event rate to everyone.

## Experiment 4: does the prior-use pattern appear across age bands?

Rates are unadjusted; one row per patient across the full cohort. Age is recorded in 10-year bands and grouped here into four broader bands.

{chr(10).join(age_rows)}

This is a check for a pattern within age groups, not a fully adjusted analysis. Differences in illness, insurance, facility, and other factors may remain within each age band.

## Experiment 5: patient-held-out prediction

{metric_table()}

ROC AUC describes ranking ability (0.5 is chance); average precision summarizes precision across recall levels, with prevalence as the constant baseline; Brier score measures average squared probability error (lower is better). These are test-set estimates, not estimates for a new hospital or a future year. The expanded model's ROC AUC has a paired test-set bootstrap 95% interval of **{intervals['auc'][0]:.3f}–{intervals['auc'][1]:.3f}**. Its AUC difference versus prior visits alone is **{evaluations['expanded']['auc']-evaluations['prior_visits']['auc']:.3f}** (200-resample paired percentile interval {intervals['auc_difference'][0]:.3f}–{intervals['auc_difference'][1]:.3f}). This bootstrap holds the fitted models fixed and excludes training and dataset-selection uncertainty.

## Experiment 6: what a risk threshold would flag

The following thresholds are illustrations, not recommended cutoffs. Positive predictive value is the fraction of flagged patients who experienced the recorded outcome; sensitivity is the fraction of all test events flagged.

{chr(10).join(op_rows)}

False negatives and true negatives are in the JSON file. The choice of any threshold would depend on the intervention, resources, harms, and prospective evaluation, none of which was assessed here.

## Experiment 7: calibration and subgroup performance

The test cohort was divided into ten equal-sized groups by predicted risk. Close agreement is desirable, but this table does not validate calibration at other hospitals, times, or within every subgroup.

{chr(10).join(cal_rows)}

| Overall test events | Overall test patients | Observed rate |
|---:|---:|---:|
| {int(test_y.sum()):,} | {len(test):,} | {pct(test_y.mean())} |

Age-specific test results:

{chr(10).join(sub_rows)}

The age bands have different sample sizes and event counts; subgroup estimates are uncertain, and differences in AUC alone do not establish fairness. We did not perform a comprehensive fairness audit.

## Limitations and next steps

- A random patient split does not assess temporal or geographic transport. Hospital identifiers and actual encounter dates are not available for a reliable hospital-held-out or chronological validation in this file.
- The data cover 1999–2008 and all recorded diabetes types; clinical practice and coding have changed. The source dataset already selects encounters with lab tests, medications, and stays of 1–14 days.
- Recorded readmissions may not include all care outside the contributing system. Patients discharged to death or hospice were excluded after first-encounter selection; unknown disposition codes remain.
- Calibration, subgroup analysis, and thresholds were explored on this same test set. No external validation, model selection study, intervention evaluation, formal causal adjustment, or prospective trial was conducted.
- The model's associations are not causal effects. With an imbalanced outcome, a high accuracy score alone would be misleading, so we report ranking, probability error, and threshold tradeoffs.
- Reasonable follow-up: access a current, appropriately governed dataset with dates and site identifiers; define intended use and outcome capture; validate prospectively, including subgroup calibration and intervention harms.

## Reproduce

Install NumPy in your chosen Python environment (`python -m pip install numpy`), then run `python model_experiment.py` in this folder. The original archive is downloaded by `readmission_experiment.py` if needed. Results are saved as `model_results.json`. Python, NumPy, seed, and archive hash affect reproducibility; archive SHA-256: `{digest}`. The fitted model is intentionally not saved as a clinical artifact.
'''
    (HERE/'extended-findings.md').write_text(report,encoding='utf-8')
    print(f"Test n={len(test):,}; expanded AUC={evaluations['expanded']['auc']:.3f}; prior-only AUC={evaluations['prior_visits']['auc']:.3f}")
    print(f"Gradient norms: prior={prior_grad:.6f}, expanded={full_grad:.6f}")


if __name__=='__main__':
    main()
