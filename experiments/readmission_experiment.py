"""Exploratory analyses of UCI diabetes hospital readmission data.

Run: python readmission_experiment.py
Downloads the original UCI archive on first use; needs only the Python standard library.
"""
from __future__ import annotations

import csv
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
URL = 'https://archive.ics.uci.edu/static/public/296/diabetes+130-us+hospitals+for+years+1999-2008.zip'
ARCHIVE = HERE / 'uci-diabetes-130-hospitals.zip'
EXCLUDED = {'11', '13', '14', '19', '20', '21'}


def load():
    if not ARCHIVE.exists():
        request = Request(URL, headers={'User-Agent': 'DiabetesResearchExperiment/1.0'})
        with urlopen(request, timeout=120) as response:
            data = response.read()
        # Validate the archive before saving it for reuse.
        with ZipFile(io.BytesIO(data)) as z:
            if z.testzip() is not None:
                raise ValueError('Corrupt downloaded archive')
        ARCHIVE.write_bytes(data)
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    with ZipFile(ARCHIVE) as z:
        path = next(name for name in z.namelist() if name.endswith('diabetic_data.csv'))
        with z.open(path) as raw, io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
    return rows, digest


def stats(rows):
    n = len(rows)
    events = sum(row['readmitted'] == '<30' for row in rows)
    p = events / n
    z = 1.959963984540054
    denominator = 1 + z*z/n
    center = (p + z*z/(2*n))/denominator
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))/denominator
    return {'n': n, 'events': events, 'rate': p, 'ci_low': center-half, 'ci_high': center+half}


def group(rows, field, definitions):
    return [{'group': name, **stats([r for r in rows if fn(r[field])])} for name, fn in definitions]


def pct(value):
    return f'{100*value:.1f}%'


def table(groups):
    result = ['| Group | Encounters | Readmitted within 30 days | Rate | 95% Wilson interval |',
              '|---|---:|---:|---:|---:|']
    for x in groups:
        result.append(f"| {x['group']} | {x['n']:,} | {x['events']:,} | {pct(x['rate'])} | {pct(x['ci_low'])}–{pct(x['ci_high'])} |")
    return '\n'.join(result)


def main():
    rows, digest = load()
    required = {'patient_nbr','encounter_id','discharge_disposition_id','readmitted','number_inpatient','time_in_hospital','A1Cresult'}
    if not rows or not required.issubset(rows[0]):
        raise ValueError('Source data are missing required columns')
    if any(r['readmitted'] not in ('<30', '>30', 'NO') for r in rows):
        raise ValueError('Unexpected outcome value')
    # Select the smallest encounter ID per patient as a proxy for the first recorded encounter.
    # This choice is made before exclusions; encounter ID is not a verified admission date.
    first = {}
    for row in rows:
        patient = row['patient_nbr']
        if patient not in first or int(row['encounter_id']) < int(first[patient]['encounter_id']):
            first[patient] = row
    cohort = [r for r in first.values() if r['discharge_disposition_id'] not in EXCLUDED]
    all_eligible = [r for r in rows if r['discharge_disposition_id'] not in EXCLUDED]
    prior_defs = [('0',lambda x:int(x)==0),('1',lambda x:int(x)==1),('2 or more',lambda x:int(x)>=2)]
    stay_defs = [('1–3 days',lambda x:int(x)<=3),('4–7 days',lambda x:4<=int(x)<=7),('8–14 days',lambda x:int(x)>=8)]
    test_defs = [('No A1C result recorded',lambda x:x=='None'),('A1C result recorded',lambda x:x!='None')]
    prior = group(cohort,'number_inpatient',prior_defs)
    stay = group(cohort,'time_in_hospital',stay_defs)
    a1c = group(cohort,'A1Cresult',test_defs)
    sensitivity = group(all_eligible,'number_inpatient',prior_defs)
    for collection in (prior,stay,a1c,sensitivity):
        assert sum(x['n'] for x in collection) == (len(all_eligible) if collection is sensitivity else len(cohort))
    result = {'dataset_url':URL,'archive_sha256':digest,'raw_encounters':len(rows),'unique_patients':len(first),'primary_cohort':len(cohort),'eligible_encounters':len(all_eligible),'overall':stats(cohort),'prior_inpatient':prior,'length_of_stay':stay,'a1c_recorded':a1c,'sensitivity_all_encounters_prior_inpatient':sensitivity}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    a,b=prior[0],prior[-1]
    report=f'''# Exploratory experiment: diabetes hospital readmission

Run date: {date.today().isoformat()}. The results are deterministic for a fixed dataset. This is an observational, retrospective exploration—not an intervention or a clinical prediction tool.

## Question and dataset

How does recorded readmission within 30 days vary by previous inpatient use, length of stay, and whether an A1C result was recorded? The [UCI Diabetes 130-US Hospitals dataset](https://doi.org/10.24432/C5230J) contains inpatient encounters from 1999–2008 in which any type of diabetes was recorded. It is not restricted to type 2 diabetes. An encounter qualified for the source dataset if it lasted 1–14 days and involved lab tests and medication. Readmission reflects the dataset's recorded outcome, not necessarily all readmissions elsewhere.

The archive had {len(rows):,} encounters and {len(first):,} distinct patient identifiers. For the main analysis, the encounter with the smallest encounter ID per patient was selected as a proxy for the earliest recorded encounter, then discharges coded as death or hospice (11, 13, 14, 19, 20, 21) were excluded. This left **{len(cohort):,} encounters**, with {stats(cohort)['events']:,} recorded early readmissions ({pct(stats(cohort)['rate'])}). Encounter IDs are a proxy, not independently verified dates. Exclusion was applied after selecting the first encounter; later eligible encounters for excluded patients were not substituted.

## Experiment 1: previous inpatient visits

Grouping is the recorded number of inpatient visits in the year preceding the encounter.

{table(prior)}

The recorded rate for the 2-or-more group exceeded the 0 group by **{100*(b['rate']-a['rate']):.1f} percentage points**. This is an unadjusted difference, not evidence that reducing visits would itself reduce readmissions.

## Experiment 2: length of stay

{table(stay)}

Length of stay may reflect illness severity, discharge planning, and other factors. These results cannot establish an effect of shortening or extending a hospital stay.

## Experiment 3: A1C result recorded

{table(a1c)}

“No A1C result recorded” is the source's `None` category; it does not prove a test was never performed. The groups may differ in care, illness, and other characteristics. This comparison cannot establish whether ordering an A1C test affects readmission.

## Sensitivity check: all eligible encounters

This repeats experiment 1 without selecting one encounter per patient. It retains {len(all_eligible):,} encounters, so patients with more visits contribute more than once. The change in rates shows the impact of the unit of analysis; these rows are correlated and should not be treated as independent patients.

{table(sensitivity)}

## Interpretation and limitations

- The percentages are descriptive and unadjusted. Confounding, selection bias, and changes in care since 2008 limit interpretation and generalization.
- The outcome combines `>30` and `NO` as “not recorded as readmitted within 30 days.” Follow-up and capture outside the contributing system may be incomplete.
- Group intervals are 95% Wilson intervals for individual proportions, not confidence intervals for differences. In the all-encounter sensitivity analysis, repeated patients make the displayed intervals too narrow if interpreted as independent observations.
- The three comparisons were exploratory; no causal claim or multiple-testing inference is made.
- The data include all diabetes types, and may not represent current care, all U.S. hospitals, or all people with diabetes.
- No external validation, adjustment, data linkage, or prospective evaluation was performed. Do not use these results for patient-level decisions.

## Reproduce

Run `python readmission_experiment.py` in this folder. The script downloads the UCI archive if absent, then saves `results.json` and this report. Source dataset: Clore, Cios, DeShazo, and Strack, *Diabetes 130-US Hospitals for Years 1999-2008* (2014), UCI Machine Learning Repository, DOI [10.24432/C5230J](https://doi.org/10.24432/C5230J); licensed CC BY 4.0. Archive SHA-256: `{digest}`. The archive is retained for reproducibility.
'''
    (HERE/'findings.md').write_text(report,encoding='utf-8')
    print(f'Analyzed {len(cohort):,} patients; results written to {HERE}')
    print(table(prior))


if __name__ == '__main__':
    main()
