"""Compare 2023 and 2024 BRFSS on their common state footprint.

Uses point estimates only. Requires pandas, numpy and duckdb.
"""
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from urllib.request import urlopen

HERE=Path(__file__).resolve().parent
try:
    import duckdb
except ModuleNotFoundError:
    sys.path.insert(0,str(HERE/'.deps'))
    import duckdb
import numpy as np
import pandas as pd

from brfss_analysis import AGE, measure

SOURCE='https://github.com/muntasirmasum/brfssdata/releases/download/data-2024/brfss_2024.parquet'
SHA256='00c40d2c741bc5594b5a146b433249dd02b30c4963c85a9133f35d91fc70829b'
FILE=HERE/'brfss-2024-mirror.parquet'


def load_2024():
    if not FILE.exists():
        print('Downloading checksum-pinned 2024 mirror...',flush=True)
        with urlopen(SOURCE,timeout=180) as response: data=response.read()
        if hashlib.sha256(data).hexdigest()!=SHA256: raise ValueError('2024 mirror checksum mismatch')
        FILE.write_bytes(data)
    if hashlib.sha256(FILE.read_bytes()).hexdigest()!=SHA256:raise ValueError('Local 2024 mirror checksum mismatch')
    fields=['_STATE','_LLCPWT','_STSTR','_PSU','_AGEG5YR','DIABETE4','MEDCOST1']
    db=duckdb.connect()
    cols=[r[0] for r in db.execute('DESCRIBE SELECT * FROM read_parquet(?)',[str(FILE)]).fetchall()]
    mapping={c.upper():c for c in cols}
    if set(fields)-set(mapping):raise ValueError(f'2024 fields missing: {set(fields)-set(mapping)}')
    select=', '.join('"'+mapping[c]+'" AS "'+c+'"' for c in fields)
    return db.execute(f'SELECT {select} FROM read_parquet(?)',[str(FILE)]).df()


def eligible(d):
    # KY and PA absent in 2023; TN absent in 2024. Keep only the common footprint.
    return d[d['_STATE'].between(1,56)&~d['_STATE'].isin([21,42,47])&(d['_LLCPWT']>0)&
             d.DIABETE4.isin([1,3])&d.MEDCOST1.isin([1,2])&d['_AGEG5YR'].between(1,13)].copy()


def age_rates(d):
    rows=[]
    for label,low,high in AGE:
        s=d[d['_AGEG5YR'].between(low,high)]
        row={'label':label,'weight':float(s['_LLCPWT'].sum()),'groups':{}}
        for name,code in [('diabetes',1),('no_diabetes',3)]:
            group=s[s.DIABETE4==code]
            row['groups'][name]=measure(group,'MEDCOST1',lambda x:x==1)
        rows.append(row)
    return rows


def main():
    d23=pd.read_csv(HERE/'brfss2023-selected.csv.gz');d24=load_2024()
    if len(d24)!=457670:raise ValueError(f'Unexpected 2024 row count: {len(d24)}')
    if (d24['_STATE']==47).any():raise ValueError('Unexpected Tennessee records in 2024')
    wisconsin=d24[d24['_STATE']==55]
    wi_yes=int((wisconsin.DIABETE4==1).sum())
    wi_rate=float((wisconsin['_LLCPWT']*(wisconsin.DIABETE4==1)).sum()/wisconsin['_LLCPWT'].sum())
    if len(wisconsin)!=13096 or wi_yes!=2098 or abs(wi_rate-.1190)>.0001:
        raise ValueError('2024 Wisconsin codebook cross-check failed')
    frames={2023:eligible(d23),2024:eligible(d24)}
    if any(frame['_STATE'].nunique()!=48 for frame in frames.values()):
        raise ValueError('Unexpected number of states in the common footprint')
    groups={year:age_rates(frame) for year,frame in frames.items()}
    weights=np.asarray([r['weight'] for r in groups[2023]]);weights/=weights.sum()
    output={}
    for year,frame in frames.items():
        ratios={name:float(np.dot(weights,[r['groups'][name]['weighted_rate'] for r in groups[year]])) for name in ('diabetes','no_diabetes')}
        output[year]={'n':len(frame),'age_rows':groups[year],'standardized_rates':ratios}
    result={'mirror_2024_sha256':SHA256,'source_2024':SOURCE,'wisconsin_codebook_check':{'n':len(wisconsin),'yes':wi_yes,'weighted_yes_all_responses':wi_rate},'common_state_reference':'47 states and DC excluding Kentucky, Pennsylvania, Tennessee','reference_weights_2023':weights.tolist(),'years':output}
    (HERE/'brfss-year-comparison-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    table=['| Year | Respondents | Diabetes group | No diabetes reported | Difference |','|---|---:|---:|---:|---:|']
    for year in (2023,2024):
        z=output[year];a=z['standardized_rates']['diabetes'];b=z['standardized_rates']['no_diabetes']
        table.append(f"| {year} | {z['n']:,} | {100*a:.1f}% | {100*b:.1f}% | {100*(a-b):+.1f} percentage points |")
    strata=['| Year | Age | Diabetes: n; rate | No diabetes: n; rate |','|---|---|---:|---:|']
    for year in (2023,2024):
        for row in groups[year]:
            a=row['groups']['diabetes'];b=row['groups']['no_diabetes']
            strata.append(f"| {year} | {row['label']} | {a['n']:,}; {100*a['weighted_rate']:.1f}% | {b['n']:,}; {100*b['weighted_rate']:.1f}% |")
    report=f'''# BRFSS 2023–2024: common-footprint sensitivity check

Run date: {date.today().isoformat()}. This is an exploratory comparison of two independent annual telephone survey samples, not a longitudinal study of the same respondents. It uses weighted point estimates only; survey-design confidence intervals and significance tests have not been validated.

## Coverage and measurement

The [CDC 2023 documentation](https://www.cdc.gov/brfss/annual_data/annual_2023.html) says Kentucky and Pennsylvania were absent; the [2024 documentation](https://www.cdc.gov/brfss/annual_data/annual_2024.html) says Tennessee was absent. We exclude all three states in both years, yielding 47 states and DC. Territory records are excluded. This footprint does not represent all U.S. states. The analyses use the `_LLCPWT` weight, diabetes responses of 1 (yes) or 3 (no), definite yes/no answers to `MEDCOST1`, and known age. Borderline and pregnancy-only diabetes responses, missing/unknown responses, and unknown ages are excluded. Counts are unweighted.

The 2023 and 2024 files are checksum-verified [third-party conversions](https://muntasirmasum.github.io/brfssdata/articles/datasets.html), not independently checked row-by-row against CDC's source files. The 2024 file contains {len(d24):,} records and SHA-256 `{SHA256}`. As an additional check against an independent official source, the 2024 Wisconsin records contain {wi_yes:,} diabetes-yes responses among {len(wisconsin):,} respondents; the weighted yes percentage is {100*wi_rate:.2f}%, matching the [Wisconsin 2024 codebook](https://www.dhs.wisconsin.gov/stats/2024-wisconsin-brfss-codebook.pdf). Questions are self-reported, and the diabetes question does not identify type 2 specifically. A cost barrier refers to any needed doctor visit, not necessarily diabetes care.

## Same age reference for both years

We standardize both diabetes groups and both years to the same weighted three-band age distribution of the pooled 2023 common-footprint comparison sample: 18–44 ({100*weights[0]:.1f}%), 45–64 ({100*weights[1]:.1f}%), and 65+ ({100*weights[2]:.1f}%). This reference differs from the 48-state-and-DC reference in the 2023 report, so estimates can differ slightly.

{chr(10).join(table)}

The difference column is within-year diabetes minus no-diabetes, not an estimated causal effect. Differences across years can reflect sampling, changing population composition within age groups, coverage, nonresponse, and other factors. Without complex-design uncertainty estimates, do not infer a trend or a significant year-to-year change.

## Within-age-group estimates

{chr(10).join(strata)}

The counts are the numbers of eligible survey respondents in each cell; rates are weighted. Common geography and age standardization do not make these samples identical or eliminate confounding.

## Reproduce

Install NumPy, pandas, and DuckDB. Run `python brfss_prepare_mirror.py` then `python brfss_year_comparison.py`. The latter downloads the 2024 Parquet mirror if absent, verifies its pinned hash, and writes `brfss-year-comparison-results.json` and this report. Before publication, verify both years against the original CDC files and codebooks and compute design-based uncertainty with validated survey software.
'''
    (HERE/'brfss-year-comparison.md').write_text(report,encoding='utf-8')
    for row in table:print(row)


if __name__=='__main__': main()
