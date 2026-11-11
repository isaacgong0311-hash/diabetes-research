"""Descriptive audit of missing covariates in the 2023 complete-case analysis."""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '.surveydeps'))
import numpy as np
import pandas as pd


def summarize(frame):
    w = frame['_LLCPWT'].to_numpy(dtype=float)
    if len(w) == 0 or w.sum() <= 0:
        raise ValueError('Empty or unweighted group')
    event = (frame.MEDCOST1 == 1).to_numpy(dtype=float)
    return {'n': len(frame), 'weight': float(w.sum()), 'cost_rate': float(np.dot(w, event) / w.sum())}


def main():
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    base = d[d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0)
             & d.DIABETE4.isin([1, 3]) & d.MEDCOST1.isin([1, 2])].copy()
    base['missing_age'] = ~base['_AGEG5YR'].between(1, 13)
    base['missing_income'] = ~base['_INCOMG1'].between(1, 7)
    base['missing_insurance'] = ~base['_HLTHPL1'].isin([1, 2])
    fields = ['missing_age', 'missing_income', 'missing_insurance']
    base['complete'] = ~base[fields].any(axis=1)
    saved = json.loads((HERE / 'brfss-access-standardization-results.json').read_text(encoding='utf-8'))
    if len(base) != saved['base_n'] or int(base['complete'].sum()) != saved['complete_n']:
        raise ValueError('Base or complete-case sample does not match prior report')
    results = {}
    for code, name in ((1, 'diabetes'), (3, 'no_diabetes')):
        frame = base[base.DIABETE4 == code]
        total = summarize(frame)
        complete = summarize(frame[frame.complete])
        excluded = summarize(frame[~frame.complete])
        missing = {}
        for field in fields:
            mask = frame[field]
            missing[field] = {'n': int(mask.sum()), 'weighted_fraction': float(frame.loc[mask, '_LLCPWT'].sum() / total['weight'])}
        results[name] = {'total': total, 'complete': complete, 'excluded': excluded,
                         'excluded_weighted_fraction': excluded['weight'] / total['weight'], 'missing': missing}

    # Compare missingness groups within age to make age-composition effects visible.
    base['age_band'] = np.select([base['_AGEG5YR'].between(1, 5), base['_AGEG5YR'].between(6, 9),
                                  base['_AGEG5YR'].between(10, 13)], [0, 1, 2], default=-1)
    age_rows = []
    for code, name in ((1, 'diabetes'), (3, 'no_diabetes')):
        for age, label in ((0, '18–44'), (1, '45–64'), (2, '65+')):
            sub = base[(base.DIABETE4 == code) & (base.age_band == age)]
            complete = summarize(sub[sub.complete])
            excluded = summarize(sub[~sub.complete])
            age_rows.append({'group': name, 'age': label, 'complete_n': complete['n'],
                             'excluded_n': excluded['n'], 'complete_cost_rate': complete['cost_rate'],
                             'excluded_cost_rate': excluded['cost_rate'],
                             'excluded_weighted_fraction': excluded['weight'] / (complete['weight'] + excluded['weight'])})
    result = {'base_n': len(base), 'complete_n': int(base.complete.sum()), 'groups': results,
              'within_age': age_rows,
              'limitations': 'Descriptive weighted rates; no survey variance, causal interpretation, or missing-data model.'}
    (HERE / 'access-missingness-audit-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    rows = [f"| {label} | {r['total']['n']:,} | {r['excluded']['n']:,} | {100*r['excluded_weighted_fraction']:.1f}% | {100*r['complete']['cost_rate']:.1f}% | {100*r['excluded']['cost_rate']:.1f}% |" for label, r in [('Reports diabetes', results['diabetes']), ('Reports no diabetes', results['no_diabetes'])]]
    arows = [f"| {r['group'].replace('_', ' ')} | {r['age']} | {r['complete_n']:,} | {r['excluded_n']:,} | {100*r['excluded_weighted_fraction']:.1f}% | {100*r['complete_cost_rate']:.1f}% | {100*r['excluded_cost_rate']:.1f}% |" for r in age_rows]
    mrows = []
    for key, label in [('missing_age', 'Unknown age'), ('missing_income', 'Unknown income'), ('missing_insurance', 'Unknown insurance')]:
        x, y = results['diabetes']['missing'][key], results['no_diabetes']['missing'][key]
        mrows.append(f"| {label} | {x['n']:,} ({100*x['weighted_fraction']:.1f}%) | {y['n']:,} ({100*y['weighted_fraction']:.1f}%) |")
    report = f'''# Missing-covariate audit for the 2023 access comparison

Run date: {date.today().isoformat()}. This is a descriptive sensitivity check; it does not determine the missing-data mechanism or estimate effects of income, insurance, or diabetes.

The [complete-case analysis](brfss-access-standardization.md) begins with {len(base):,} adults with definite diabetes and cost-barrier responses, positive survey weights, and the 48-state-plus-DC footprint. It retains {base.complete.sum():,} with known age, household income, and insurance. Counts below are unweighted; percentages and cost-barrier rates use survey weights. Unknown diabetes or cost responses were already excluded before this audit.

| Response group | Base n | Excluded n | Excluded, weighted | Complete-case cost rate | Excluded cost rate |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

| Reason for exclusion | Reports diabetes: n (weighted %) | Reports no diabetes: n (weighted %) |
|---|---:|---:|
{chr(10).join(mrows)}

The exclusion reasons overlap, so counts and percentages across reasons do not sum to total exclusions. Income is defined as known only for `_INCOMG1` codes 1–7; insurance requires `_HLTHPL1` codes 1 or 2. A respondent can have more than one unknown field.

## Within broad age bands

These rows include respondents with known age only; those missing age appear in the preceding tables but cannot be assigned an age band here. No further adjustment has been made.

| Group | Age | Complete n | Excluded n | Excluded, weighted | Complete cost rate | Excluded cost rate |
|---|---|---:|---:|---:|---:|---:|
{chr(10).join(arows)}

Differences between complete and excluded respondents may reflect age composition, other measured or unmeasured characteristics, selection, or random error. Comparing observed cost rates cannot prove that values are missing at random or not at random, cannot reveal the missing covariates, and does not correct selection bias. No confidence intervals or significance tests are provided. The self-reported cost question concerns any needed doctor visit, and diabetes type is not identified.

## Reproduce

Run `python brfss_access_standardization.py` then `python access_missingness_audit.py`. It uses the previously checksum-verified 2023 extract and writes `access-missingness-audit-results.json`. Run `python verify_access_missingness.py` with DuckDB installed for a separate SQL check of the group counts, missing income, weights, and excluded-group cost rates.
'''
    (HERE / 'access-missingness-audit.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
