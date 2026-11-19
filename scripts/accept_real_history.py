"""P09 offline acceptance of three explicitly downloaded Dukascopy H1 JSON files.
Run: .venv/bin/python scripts/accept_real_history.py JAN.json FEB.json MAR.json
No gap filling, credentials, network calls or broker actions.
"""
import csv
import hashlib
import io
import json
import math
import sys
from decimal import Decimal
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from backend.main import app
from backend.datasets import DatasetStore,read_csv
from backend.dataset_api import store


def decode(data, shift=3600000, allow_empty=False):
    fields=('open','high','low','close')
    n=len(data['times'])
    if data['shift']!=shift or (not n and not allow_empty):raise ValueError('Unexpected candle granularity or empty data')
    for key in ('times','volumes',*(k+'s' for k in fields)):
        if len(data[key])!=n or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in data[key]):raise ValueError('Invalid column')
    if not n:return []
    multiplier=Decimal(str(data['multiplier']))
    if not multiplier.is_finite() or multiplier<=0:raise ValueError('Invalid multiplier')
    units={k:int((Decimal(str(data[k]))/multiplier).to_integral_value()) for k in fields}
    t=data['timestamp'];rows=[]
    for i,delta in enumerate(data['times']):
        if int(delta)!=delta or delta<0 or (i and delta==0):raise ValueError('Invalid time delta')
        t+=int(delta)*data['shift']
        if t%shift:raise ValueError('Unaligned candle timestamp')
        for k in fields:
            change=data[k+'s'][i]
            if int(change)!=change:raise ValueError('Invalid price delta')
            units[k]+=int(change)
        rows.append({'time':t//1000,**{k:float(units[k]*multiplier) for k in fields}})
    return rows


def main(paths):
    if len(paths)!=3:raise ValueError('Supply January, February and March 2024 JSON files')
    rows=[];sources=[]
    for month,path in enumerate(paths,1):
        raw=Path(path).read_bytes();decoded=decode(json.loads(raw))
        if any(datetime.fromtimestamp(r['time'],timezone.utc).strftime('%Y-%m')!=f'2024-{month:02d}' for r in decoded):raise ValueError('Unexpected coverage')
        rows.extend(decoded);sources.append({'url':f'https://jetta.dukascopy.com/v1/candles/hour/EUR-USD/BID/2024/{month}','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'observed_rows':len(decoded)})
    buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=['time','open','high','low','close']);writer.writeheader();writer.writerows(rows)
    csvbytes=buf.getvalue().encode()
    metadata=dict(symbol='EUR/USD',base_timeframe='1h',calendar='fx-ny-17-v1',input_timezone='UTC',timestamp_unit='seconds',volume_type='unknown')
    validated=read_csv(csvbytes,**metadata)
    folder=Path('.data/p09');folder.mkdir(parents=True,exist_ok=True)
    (folder/'eurusd-2024-q1-bid-h1.csv').write_bytes(csvbytes)
    db=DatasetStore('.data');app.dependency_overrides[store]=lambda:db
    try:
        with TestClient(app) as client:
            response=client.post('/api/datasets/import',params={**metadata,'source_label':'Dukascopy EUR/USD BID H1 · 2024 Q1 · observed bars'},content=csvbytes,headers={'Content-Type':'text/csv'})
            assert response.status_code==200,response.text
            meta=response.json();results={}
            for interval in ('1h','4h','d1'):
                query={'dataset_id':meta['id'],'cutoff':len(rows),'interval':interval}
                response=client.post('/api/datasets/analyze',json=query);assert response.status_code==200,response.text
                r=response.json();assert r['sentiment']['status']=='unavailable'
                assert all(m['status']=='succeeded' for m in r['module_runs'])
                assert all(e['available_at']<=r['contract']['snapshot']['as_of'] for e in r['contract']['evidence'])
                assert r==client.post('/api/datasets/analyze',json=query).json()
                examples={}
                for f in r['contract']['findings']:
                    examples.setdefault(f['kind'],{'title':f['title'],'id':f['id'],'prices':f['prices'],'explanation':f['explanation'],'evidence_ids':f['evidence_ids'][:3]})
                results[interval]={'visible_candles':len(r['candles']),'module_runs':r['module_runs'],'examples':examples,'historical_events':r['historical']['event_count'],'daily_bias':r['daily_bias']['direction'],'weekly_bias':r['weekly_bias']['direction']}
                (folder/f'analysis-{interval}.json').write_text(json.dumps(r))
            cutoff=900
            from backend.analysis import analyze
            prefix=validated[:cutoff];mutated=[dict(r) for r in validated]
            for r in mutated[cutoff:]:
                for k in ('open','high','low','close'):r[k]*=2
            a=analyze(prefix,'EUR/USD','1h',cutoff,calendar='fx-ny-17-v1')
            assert a==analyze(mutated,'EUR/USD','1h',cutoff,calendar='fx-ny-17-v1')
            bad=client.post('/api/datasets/import',params={**metadata,'source_label':'invalid acceptance fixture'},content=b'time,open,high,low,close\n1704153600,1.1,1.0,1.2,1.1',headers={'Content-Type':'text/csv'})
            assert bad.status_code==422
            report={'phase':'P09','source':'Dukascopy current public historical endpoint','price_side':'bid','granularity':'1h','raw_sources':sources,'csv_sha256':hashlib.sha256(csvbytes).hexdigest(),'dataset':meta,'checks':{'integrity':'strict CSV parser: ordered unique UTC opens, OHLC bounds, finite positive prices, session calendar','missing_bars':'retained as gaps; no flat bar fabrication','repeatability':'exact repeated API responses for 1h/4h/d1','future_mutation':'identical 900-hour prefix result','invalid_import':'422'},'results':results}
            Path('docs/real-data-p09.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps({'rows':len(rows),'dataset_id':meta['id'],'quality':meta['quality'],'timeframes':{k:v['visible_candles'] for k,v in results.items()}}))
    finally:app.dependency_overrides.pop(store,None)

if __name__=='__main__':main(sys.argv[1:])
