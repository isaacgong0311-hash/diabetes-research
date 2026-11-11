"""Compare observed general health between recipients and their donor pools."""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '.surveydeps'))
import numpy as np
import pandas as pd

from hotdeck_sensitivity import build_pools


def main():
    d = pd.read_csv(HERE / 'brfss2023-selected.csv.gz')
    domain = (d['_STATE'].between(1, 56) & (d['_LLCPWT'] > 0) & d.DIABETE4.isin([1, 3])
              & d.MEDCOST1.isin([1, 2]) & d['_AGEG5YR'].between(1, 13)).to_numpy()
    d = d.loc[domain]
    age = np.select([d['_AGEG5YR'] <= 5, d['_AGEG5YR'] <= 9], [0, 1], default=2)
    income = np.where(d['_INCOMG1'].between(1, 7),
                      np.select([d['_INCOMG1'] <= 2, d['_INCOMG1'] <= 4], [0, 1], default=2), -1)
    insurance = np.where(d['_HLTHPL1'].isin([1, 2]), np.where(d['_HLTHPL1'] == 1, 0, 1), -1)
    group = (d.DIABETE4 == 1).to_numpy().astype(int)
    outcome = (d.MEDCOST1 == 1).to_numpy().astype(int)
    weight = d['_LLCPWT'].to_numpy(dtype=float)
    health_known = d.GENHLTH.isin([1, 2, 3, 4, 5]).to_numpy()
    poor_health = d.GENHLTH.isin([4, 5]).to_numpy(dtype=float)
    pools = build_pools(age, group, outcome, income, insurance, weight)
    records = []
    for p in pools:
        rec, donor = p['recipients'], p['donors']
        rec = rec[health_known[rec]]
        donor = donor[health_known[donor]]
        if len(rec) == 0:
            continue
        if len(donor) == 0:
            raise ValueError('A recipient pool has no donor with known general health')
        rw, dw = weight[rec], weight[donor]
        recipient_rate = float(np.dot(rw, poor_health[rec]) / rw.sum())
        donor_rate = float(np.dot(dw, poor_health[donor]) / dw.sum())
        records.append({'pattern': p['pattern'], 'group': p['group'], 'recipient_n': len(rec),
                        'recipient_weight': float(rw.sum()), 'recipient_rate': recipient_rate,
                        'donor_rate': donor_rate, 'difference': donor_rate - recipient_rate,
                        'known_health_donor_n': len(donor)})

    def combine(rows):
        weights = np.array([x['recipient_weight'] for x in rows])
        observed = np.array([x['recipient_rate'] for x in rows])
        donor = np.array([x['donor_rate'] for x in rows])
        return {'recipient_n': sum(x['recipient_n'] for x in rows), 'pools': len(rows),
                'recipient_rate': float(np.average(observed, weights=weights)),
                'donor_pool_rate_reweighted': float(np.average(donor, weights=weights)),
                'difference': float(np.average(donor - observed, weights=weights)),
                'mean_absolute_pool_difference': float(np.average(np.abs(donor - observed), weights=weights))}
    summaries = {'all': combine(records)}
    for g, label in ((0, 'no_diabetes'), (1, 'diabetes')):
        summaries[label] = combine([r for r in records if r['group'] == g])
    for pattern in ('income_only', 'insurance_only', 'both'):
        summaries[pattern] = combine([r for r in records if r['pattern'] == pattern])
    recipient_total = sum(len(p['recipients']) for p in pools)
    result = {'recipient_total': recipient_total, 'recipient_known_health': summaries['all']['recipient_n'],
              'summaries': summaries, 'pool_diagnostics': records,
              'limitation': 'An auxiliary-variable diagnostic, not a test of donor exchangeability for missing covariates.'}
    (HERE / 'hotdeck-balance-audit-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    labels = [('all', 'All recipients'), ('no_diabetes', 'Reports no diabetes'), ('diabetes', 'Reports diabetes'),
              ('income_only', 'Income missing only'), ('insurance_only', 'Insurance missing only'), ('both', 'Both missing')]
    rows = [f"| {label} | {summaries[name]['recipient_n']:,} | {100*summaries[name]['recipient_rate']:.1f}% | {100*summaries[name]['donor_pool_rate_reweighted']:.1f}% | {100*summaries[name]['difference']:+.2f} |" for name, label in labels]
    report = f'''# Donor-pool balance audit: observed general health

Run date: {date.today().isoformat()}. This diagnostic compares an observed auxiliary variable that was **not** used to construct the donor pools. It does not establish whether donors represent recipients on missing income or insurance.

For the [donor-draw experiment](hotdeck-sensitivity.md), donor pools match age band, diabetes response, cost-barrier response, and any observed income/insurance category. Among {recipient_total:,} recipients with missing income or insurance, {summaries['all']['recipient_n']:,} have a definite general-health answer. Within each pool, we calculate the weighted fair-or-poor health rate among recipients and among eligible donors with definite health answers. Donor rates are then averaged using **recipient pool weights**, so the two columns compare the same pool mix. General health codes 4 and 5 represent fair or poor health; codes 1–3 are the comparison, according to the [CDC 2023 variable documentation](https://www.cdc.gov/brfss/annual_data/2023/pdf/2023-calculated-variables-version4-508.pdf). Unknown health is excluded separately among donors and recipients.

| Recipient subgroup | Known-health recipients, n | Recipients reporting fair/poor health | Donor-pool rate with recipient-pool weights | Donor minus recipient, percentage points |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

The recipient-pool-weighted mean **absolute** donor-minus-recipient difference across pools is {100*summaries['all']['mean_absolute_pool_difference']:.2f} percentage points; signed differences can cancel in the overall row. A difference on observed general health may indicate that the matching variables leave meaningful differences between donors and recipients, but this descriptive comparison has no design-based interval and cannot determine the reason for the difference. Similarity on general health would not prove similarity in the missing fields or establish a missing-at-random assumption. Within-pool rates may be unstable in small groups, and donor pools can overlap across patterns, so donor counts must not be summed as unique people.

## Reproduce

Run `python hotdeck_balance_audit.py` with NumPy and pandas after preparing the 2023 extract. Pool-level summaries are in `hotdeck-balance-audit-results.json`; no person-level donor links are saved.
'''
    (HERE / 'hotdeck-balance-audit.md').write_text(report, encoding='utf-8')
    print(json.dumps({'recipient_total': recipient_total, 'summaries': summaries}, indent=2))


if __name__ == '__main__':
    main()
