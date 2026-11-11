"""Prepare a selected extract from a documented CDC BRFSS 2023 data mirror.

The mirror is the brfssdata project, not the CDC's original XPT. Its published
SHA-256 is verified. Dependencies: duckdb and pandas.
"""
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import urlopen

HERE=Path(__file__).resolve().parent
try:
    import duckdb
except ModuleNotFoundError:
    sys.path.insert(0,str(HERE/'.deps'))
    import duckdb

SOURCE='https://github.com/muntasirmasum/brfssdata/releases/download/data-2023/brfss_2023.parquet'
EXPECTED='128ef26a1c0a84e271e1e35e6584f3c7bfd7690c8cd7ba602313c0d738021ffe'
PARQUET=HERE/'brfss-2023-mirror.parquet'
FIELDS=['_STATE','_LLCPWT','_STSTR','_PSU','_AGEG5YR','_AGE_G','SEXVAR','DIABETE4','MEDCOST1','GENHLTH','CHECKUP1','_HLTHPL1','_INCOMG1']


def main():
    if not PARQUET.exists():
        print('Downloading documented BRFSS mirror (about 29 MB)...',flush=True)
        with urlopen(SOURCE,timeout=180) as response:
            data=response.read()
        if hashlib.sha256(data).hexdigest()!=EXPECTED:
            raise ValueError('Downloaded data did not match recorded mirror checksum')
        PARQUET.write_bytes(data)
    digest=hashlib.sha256(PARQUET.read_bytes()).hexdigest()
    if digest!=EXPECTED: raise ValueError('Local parquet does not match recorded mirror checksum')
    db=duckdb.connect()
    columns=[r[0] for r in db.execute('DESCRIBE SELECT * FROM read_parquet(?)',[str(PARQUET)]).fetchall()]
    mapping={c.upper():c for c in columns}
    missing=set(FIELDS)-set(mapping)
    if missing: raise ValueError(f'Missing required fields: {sorted(missing)}')
    selected=', '.join('"'+mapping[c].replace('"','""')+'" AS "'+c+'"' for c in FIELDS)
    data=db.execute(f'SELECT {selected} FROM read_parquet(?)',[str(PARQUET)]).df()
    data.to_csv(HERE/'brfss2023-selected.csv.gz',index=False,compression='gzip')
    metadata={'source':SOURCE,'original_cdc':'https://www.cdc.gov/brfss/annual_data/annual_2023.html','mirror_description':'https://muntasirmasum.github.io/brfssdata/articles/datasets.html','mirror_sha256':digest,'n_rows':len(data),'fields':FIELDS,'duckdb_version':duckdb.__version__,'caveat':'Converted third-party copy; not independently compared row-by-row with CDC XPT.'}
    (HERE/'brfss2023-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(data):,} records; mirror SHA-256 {digest}',flush=True)


if __name__=='__main__': main()
