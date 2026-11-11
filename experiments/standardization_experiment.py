"""Age and prior-inpatient standardization of recorded A1C and readmission."""
import json
from datetime import date
from pathlib import Path

import numpy as np

from model_experiment import AGE_BANDS, age, cohort_from
from readmission_experiment import load, pct

HERE = Path(__file__).resolve().parent
SEED = 3701


def estimate(y, recorded, strata):
    # Eight strata crossed with two exposure groups, pooled-cohort standard weights.
    counts = np.bincount(strata * 2 + recorded, minlength=16).reshape(8, 2)
    events = np.bincount(strata * 2 + recorded, weights=y, minlength=16).reshape(8, 2)
    if np.any(counts == 0):
        raise ValueError('At least one stratum lacks an exposure group; standardization is undefined')
    weights = counts.sum(axis=1) / len(y)
    rates = events / counts
    standardized = weights @ rates
    return counts, events, standardized


def main():
    rows,digest=load(); data=cohort_from(rows)
    y=np.asarray([r['readmitted']=='<30' for r in data],dtype=int)
    a1c=np.asarray([int(r['A1Cresult']!='None') for r in data],dtype=int)
    age_group=np.asarray([next(i for i,(_,low,high) in enumerate(AGE_BANDS) if low<=age(r)<high) for r in data])
    prior=np.asarray([int(int(r['number_inpatient'])>0) for r in data])
    strata=age_group*2+prior
    counts,events,std=estimate(y,a1c,strata)
    crude=np.array([y[a1c==v].mean() for v in (0,1)])
    rng=np.random.default_rng(SEED); diffs=[]
    for _ in range(500):
        i=rng.integers(0,len(y),len(y))
        try:
            _,_,estimate_i=estimate(y[i],a1c[i],strata[i])
            diffs.append(estimate_i[1]-estimate_i[0])
        except ValueError:
            pass
    if len(diffs)<475:
        raise RuntimeError('Insufficient bootstrap replicates with both groups in every stratum')
    interval=np.quantile(diffs,[.025,.975])
    result={'archive_sha256':digest,'seed':SEED,'n':len(y),'raw_rates':crude.tolist(),'standardized_rates':std.tolist(),'difference_recorded_minus_not_recorded':float(std[1]-std[0]),'bootstrap_ci':interval.tolist(),'successful_bootstraps':len(diffs),'counts':counts.tolist(),'events':events.astype(int).tolist()}
    (HERE/'standardization_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    table=['| Age band | Prior inpatient visits | A1C not recorded: n; rate | A1C recorded: n; rate |','|---|---|---:|---:|']
    for i,(label,_,_) in enumerate(AGE_BANDS):
        for j,prior_label in enumerate(('0','1 or more')):
            k=i*2+j
            table.append(f"| {label} | {prior_label} | {counts[k,0]:,}; {pct(events[k,0]/counts[k,0])} | {counts[k,1]:,}; {pct(events[k,1]/counts[k,1])} |")
    report=f'''# A1C-recording comparison: stratified sensitivity analysis

Run date: {date.today().isoformat()}. Historical source: [UCI Diabetes 130-US Hospitals](https://doi.org/10.24432/C5230J), 1999–2008. See [findings.md](findings.md) for cohort construction and limitations.

## Question

Does the observed difference in recorded 30-day readmission between encounters with and without a recorded A1C result change when the two groups are compared using the same age-band and prior inpatient-use distribution? This is an observational association, not a test of the effect of ordering an A1C test.

The cohort includes {len(y):,} patients selected by smallest encounter ID, with death or hospice excluded afterwards. A1C “not recorded” is the source's `None` category and does not establish that a test never occurred. The data include multiple diabetes types, and the dataset does not capture every possible measure of disease severity or clinical context.

## Crude and standardized rates

| Outcome | A1C not recorded | A1C recorded | Difference: recorded minus not recorded |
|---|---:|---:|---:|
| Crude recorded readmission rate | {pct(crude[0])} | {pct(crude[1])} | {100*(crude[1]-crude[0]):+.2f} percentage points |
| Standardized to pooled age/prior-use distribution | {pct(std[0])} | {pct(std[1])} | {100*(std[1]-std[0]):+.2f} percentage points |

The standardized difference has a 95% patient-bootstrap percentile interval of **{100*interval[0]:+.2f} to {100*interval[1]:+.2f} percentage points** ({len(diffs)} successful resamples; seed {SEED}). The interval quantifies sampling variation under this resampling approach; it does not remove bias or support a causal conclusion.

## Stratum-specific rates

{chr(10).join(table)}

The standardization uses eight strata: four age groups crossed with zero versus one or more prior inpatient visits. Each group's within-stratum readmission rate is weighted by that stratum's proportion in the full analysis cohort. Small or uneven cells make individual stratum rates less stable; the table makes the overlap visible.

## What the comparison does and does not tell us

Only two broad characteristics were accounted for. Residual confounding from illness severity, diabetes type, reasons for ordering tests, other care, hospital differences, access, missing results and discharge context may be substantial. Recorded readmission may also be incomplete. This analysis cannot tell us whether performing an A1C test changes readmission, nor can it guide individual care.

## Reproduce

Install NumPy and run `python standardization_experiment.py` in this folder. It writes `standardization_results.json` and this report. Archive SHA-256: `{digest}`.
'''
    (HERE/'standardization-findings.md').write_text(report,encoding='utf-8')
    print(f"Crude difference: {100*(crude[1]-crude[0]):+.2f} pp; standardized: {100*(std[1]-std[0]):+.2f} pp; bootstrap 95% CI {100*interval[0]:+.2f} to {100*interval[1]:+.2f} pp")


if __name__=='__main__':
    main()
