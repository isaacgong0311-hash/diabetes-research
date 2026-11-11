"""Download and extract selected fields from CDC's public 2023 BRFSS XPT file.

Dependencies: pandas, numpy. The source archive is approximately 64 MB.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile
import hashlib
import json
import os
import tempfile

import pandas as pd

HERE = Path(__file__).resolve().parent
SOURCE = 'https://www.cdc.gov/brfss/annual_data/2023/files/LLCP2023XPT.zip'
ARCHIVE = HERE / 'cdc-brfss-2023-xpt.zip'
EXTRACT = HERE / 'brfss2023-selected.csv.gz'
METADATA = HERE / 'brfss2023-metadata.json'
FIELDS = ['_STATE', '_LLCPWT', '_STSTR', '_PSU', '_AGEG5YR', '_AGE_G', 'SEXVAR', 'DIABETE4', 'MEDCOST1', 'GENHLTH', 'CHECKUP1', '_HLTHPL1', '_INCOMG1']


def main():
    if not ARCHIVE.exists():
        print('Downloading CDC 2023 BRFSS archive...', flush=True)
        request=Request(SOURCE, headers={'User-Agent':'DiabetesResearchProject/1.0'})
        # Atomic rename avoids mistaking a partial download for a valid archive.
        with tempfile.NamedTemporaryFile(dir=HERE, prefix='brfss-download-', suffix='.tmp', delete=False) as temp:
            tmp=Path(temp.name)
            try:
                with urlopen(request, timeout=180) as response:
                    while True:
                        chunk=response.read(1024*1024)
                        if not chunk: break
                        temp.write(chunk)
            except Exception:
                temp.close()
                tmp.unlink(missing_ok=True)
                raise
        try:
            with ZipFile(tmp) as archive:
                if archive.testzip() is not None: raise ValueError('Corrupt archive')
            os.replace(tmp, ARCHIVE)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
    digest=hashlib.sha256()
    with ARCHIVE.open('rb') as src:
        for block in iter(lambda:src.read(1024*1024),b''): digest.update(block)
    pieces=[]
    with ZipFile(ARCHIVE) as archive:
        name=next(n for n in archive.namelist() if n.upper().endswith('.XPT'))
        print(f'Reading {name} in chunks...',flush=True)
        with archive.open(name) as f:
            reader=pd.read_sas(f,format='xport',chunksize=10000)
            for chunk in reader:
                absent=set(FIELDS)-set(chunk.columns)
                if absent: raise ValueError(f'Missing expected columns: {sorted(absent)}')
                pieces.append(chunk[FIELDS].copy())
                if len(pieces)%10==0: print(f'  {len(pieces)*10000:,} rows processed',flush=True)
    data=pd.concat(pieces,ignore_index=True)
    data.to_csv(EXTRACT,index=False,compression='gzip')
    metadata={'source':SOURCE,'archive_sha256':digest.hexdigest(),'archive_member':name,'n_rows':len(data),'fields':FIELDS,'extract':EXTRACT.name,'pandas_version':pd.__version__}
    METADATA.write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(f'Saved {len(data):,} selected records; archive SHA-256: {digest.hexdigest()}',flush=True)


if __name__ == '__main__': main()
