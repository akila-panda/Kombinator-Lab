import copy
import json
from datetime import datetime
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.dataset_api import store
from backend.datasets import DatasetStore, read_csv, parse_time
from backend.calendars import aggregate_frame, bar_bounds, quality_report, is_open, expected_slots
from backend.analysis import frame, demo
from backend.contracts import AnalysisEnvelope


def stamp(s):return int(pd.Timestamp(s).timestamp())
def rows(start='2024-01-01T00:00:00Z',count=120,step=60):
    return [{'time':stamp(start)+i*step,'open':1.+i/10000,'high':1.01+i/10000,'low':.99+i/10000,'close':1.005+i/10000,'volume':2.} for i in range(count)]
def csv_bytes(data):
    keys=['time','open','high','low','close','volume']
    return (','.join(keys)+'\n'+'\n'.join(','.join(str(r[k]) for k in keys) for r in data)).encode()
META=dict(symbol='EUR/USD',base_timeframe='1m',calendar='fixed-utc-v1',input_timezone='UTC',timestamp_unit='seconds',volume_type='unknown')
def agg(data,interval,asof,base='1m',calendar='fixed-utc-v1'):
    return aggregate_frame(frame(data,len(data)),interval,pd.Timestamp(asof),base,calendar)

@pytest.fixture
def client(tmp_path):
    db=DatasetStore(tmp_path)
    app.dependency_overrides[store]=lambda:db
    with TestClient(app) as c:yield c,db
    app.dependency_overrides.clear()

def test_known_ohlcv_and_incomplete():
    data=rows(count=125)
    got=agg(data,'1h','2024-01-01T02:05Z')
    assert len(got)==2
    assert got.iloc[0].to_dict()==dict(open=1.,high=1.0159,low=.99,close=1.0109,volume=120.,close_time=stamp('2024-01-01T01:00Z'))
    assert got.attrs['aggregation']['excluded_groups']==dict(unfinished=1,missing_input=0)
    missing=agg(data[:3]+data[4:],'1h','2024-01-01T02:05Z')
    assert len(missing)==1 and missing.index[0]==got.index[1]
    assert missing.attrs['aggregation']['excluded_groups']['missing_input']==1
    assert agg(data,'1h','2024-01-01T00:59:59Z').empty

@pytest.mark.parametrize('day,utc_hour',[('2024-03-11',21),('2024-11-04',22)])
def test_ny_daily_fourhour_boundaries(day,utc_hour):
    start=f'{day}T{utc_hour}:00:00Z';data=rows(start,24,3600)
    result=agg(data,'d1',pd.Timestamp(start)+pd.Timedelta(days=1),'1h','fx-ny-17-v1')
    assert len(result)==1 and int(result.index[0].timestamp())==stamp(start)
    assert result.iloc[0].close_time==stamp(start)+86400
    four=agg(data,'4h',pd.Timestamp(start)+pd.Timedelta(days=1),'1h','fx-ny-17-v1')
    assert len(four)==6 and int(four.index[0].timestamp())==stamp(start)

@pytest.mark.parametrize('friday,sunday,hours',[('2024-03-08T22:00Z','2024-03-10T21:00Z',47),('2024-11-01T21:00Z','2024-11-03T22:00Z',49)])
def test_dst_weekend_closure(friday,sunday,hours):
    a=stamp(friday);b=stamp(sunday)
    assert (b-a)//3600==hours
    assert expected_slots(a,b,3600,'fx-ny-17-v1')==0
    data=[rows(count=1)[0]|{'time':a-3600},rows(count=1)[0]|{'time':b}]
    q=quality_report(data,'1h','fx-ny-17-v1')
    assert q['missing_bars']==0 and q['scheduled_closed_slots']==hours
    assert not is_open(a,'fx-ny-17-v1') and is_open(b,'fx-ny-17-v1')


def test_weekly_session_and_missing_weekday():
    data=rows('2024-03-10T21:00Z',120,3600)
    got=agg(data,'w1','2024-03-15T21:00Z','1h','fx-ny-17-v1')
    assert len(got)==1 and got.iloc[0].close_time==stamp('2024-03-15T21:00Z')
    assert agg(data[:-1],'w1','2024-03-15T21:00Z','1h','fx-ny-17-v1').empty
    assert agg(data,'w1','2024-03-15T20:00Z','1h','fx-ny-17-v1').empty
    q=quality_report(data[:40]+data[41:],'1h','fx-ny-17-v1')
    assert q['missing_bars']==1 and q['scheduled_closed_slots']==0

@pytest.mark.parametrize('local',['2024-03-10T02:30:00','2024-11-03T01:30:00'])
def test_dst_ambiguous_nonexistent_rejected(local):
    with pytest.raises(ValueError,match='Ambiguous/nonexistent'):parse_time(local,'America/New_York')

def test_timezone_and_millisecond_explicit():
    assert parse_time('2024-11-03T01:30:00-04:00')==stamp('2024-11-03T05:30:00Z')
    assert parse_time('2024-01-01T05:30:00','Asia/Colombo')==stamp('2024-01-01T00:00Z')
    assert parse_time('1704067200000',timestamp_unit='milliseconds')==1704067200

@pytest.mark.parametrize('mutation',[
 lambda r:r+[r[-1]],lambda r:list(reversed(r)),lambda r:[r[0]|{'high':.5}],
 lambda r:[r[0]|{'close':float('nan')}],lambda r:[r[0]|{'volume':-1}],
 lambda r:[r[0]|{'time':r[0]['time']+1}],
])
def test_invalid_rows_rejected(mutation):
    with pytest.raises(ValueError):read_csv(csv_bytes(mutation(rows(count=2))),**META)

@pytest.mark.parametrize('text',[
 'time,open,high,low,close\n2024-01-01,1,2,0.5',
 'time,open,high,low,close,complete\n2024-01-01,1,2,0.5,1,false',
 'time,open,high,low,close,symbol\n2024-01-01,1,2,0.5,1,GBP/USD',
 'time,time,open,high,low,close\n',
])
def test_malformed_csv(text):
    with pytest.raises(ValueError):read_csv(text.encode(),**META)

def test_persistence_fingerprint_and_atomic_import(client):
    c,db=client;data=csv_bytes(rows())
    query=META|{'source_label':'sample.csv'}
    response=c.post('/api/datasets/import',params=query,content=data)
    assert response.status_code==200,response.text
    meta=response.json();did=meta['id']
    assert c.post('/api/datasets/import',params=query,content=data).json()==meta
    assert DatasetStore(db.directory).get(did)==meta
    assert meta['raw_sha256'] and meta['content_sha256'] and meta['provenance_verified'] is False
    assert meta['source_kind']=='user_upload' and meta['count']==120
    changed=c.post('/api/datasets/import',params=query|{'source_label':'different-source'},content=data).json()
    assert changed['content_sha256']==meta['content_sha256'] and changed['id']!=did
    assert c.post('/api/datasets/import',params=query,content=csv_bytes(rows()+rows())).status_code==422
    assert len(db.list())==2
    assert c.get('/api/datasets',params={'symbol':'GBP/USD'}).json()['datasets']==[]


def test_range_clock_pagination_and_warmup(client):
    c,db=client;data=rows();meta=db.import_csv(csv_bytes(data),source_label='range',**META);path=f"/api/datasets/{meta['id']}/candles"
    got=c.get(path,params={'start':data[10]['time'],'end':data[25]['time'],'as_of':data[20]['time'],'limit':5,'warmup':15}).json()
    assert got['warmup_returned']==10 and not got['warmup_sufficient']
    assert got['candles']==data[10:15] and got['next_start']==data[15]['time']
    second=c.get(path,params={'start':got['next_start'],'end':data[25]['time'],'as_of':data[20]['time']}).json()
    assert second['candles']==data[15:20] and not second['truncated']
    assert c.get(path,params={'start':10,'end':9}).status_code==422
    assert c.get(path,params={'limit':0}).status_code==422
    assert c.get('/api/datasets/unknown').status_code==404


def test_aggregate_range_keeps_full_input_and_warmup(client):
    c,db=client;data=rows(count=245);meta=db.import_csv(csv_bytes(data),source_label='agg',**META)
    got=c.get(f"/api/datasets/{meta['id']}/aggregate",params={'interval':'1h','as_of':data[-1]['time']+60,'start':data[120]['time'],'warmup':3,'limit':1}).json()
    assert len(got['candles'])==1 and got['candles'][0]['time']==data[120]['time']
    assert got['candles'][0]['volume'] is None and got['candles'][0]['state']=='completed'
    assert got['warmup_returned']==2 and not got['warmup_sufficient'] and got['truncated']
    assert got['next_start']==data[180]['time']


def test_dataset_analysis_and_future_prefix_identity(client):
    c,db=client
    meta=c.post('/api/datasets/demo').json();body={'dataset_id':meta['id'],'cutoff':200,'interval':'1h'}
    a=c.post('/api/datasets/analyze',json=body)
    assert a.status_code==200,a.text
    result=a.json();contract=AnalysisEnvelope.model_validate(result['contract'])
    assert contract.snapshot.calendar=='utc-weekdays-v1' and contract.snapshot.source.kind=='synthetic'
    assert 'scheduled_closures' in contract.snapshot.quality_flags
    assert 'missing_scheduled_bars' not in contract.snapshot.quality_flags
    assert len(result['modules'])==4 and result['dataset_id']==meta['id']
    assert c.post('/api/datasets/analyze',json=body).json()==result
    assert c.post('/api/datasets/analyze',json=body|{'cutoff':10001}).status_code==422
    assert c.post('/api/datasets/analyze',json=body|{'candles':[]}).status_code==422
    assert c.post('/api/datasets/analyze',json=body|{'cutoff':10}).status_code==422


def test_minute_dataset_to_hour_analysis(client):
    c,db=client;data=rows(count=60*65)
    meta=db.import_csv(csv_bytes(data),source_label='minutes',**META)
    r=c.post('/api/datasets/analyze',json={'dataset_id':meta['id'],'cutoff':len(data),'interval':'1h'})
    assert r.status_code==200,r.text
    contract=AnalysisEnvelope.model_validate(r.json()['contract'])
    assert contract.snapshot.base_timeframe=='1m' and len(contract.candles)==65
    assert contract.snapshot.input_end==data[-1]['time']+60


def test_ny_analysis_contract_across_dst(client):
    c,db=client
    data=rows('2024-03-07T22:00Z',24*8,3600)
    data=[r for r in data if is_open(r['time'],'fx-ny-17-v1')]
    meta=db.import_csv(csv_bytes(data),source_label='NY fixture',**(META|{'base_timeframe':'1h','calendar':'fx-ny-17-v1'}))
    r=c.post('/api/datasets/analyze',json={'dataset_id':meta['id'],'cutoff':len(data),'interval':'1h'})
    assert r.status_code==200,r.text
    contract=AnalysisEnvelope.model_validate(r.json()['contract'])
    assert all(x.calendar=='fx-ny-17-v1' for x in contract.candles)
    pivot=next(e for e in contract.evidence if e.id.startswith('daily-pivot-input'))
    assert pivot.available_at%86400==21*3600

@pytest.mark.parametrize('interval',['4h','d1'])
def test_ny_higher_timeframe_analysis(client,interval):
    c,db=client
    data=rows('2024-01-07T22:00Z',24*120,3600)
    data=[r for r in data if is_open(r['time'],'fx-ny-17-v1')]
    meta=db.import_csv(csv_bytes(data),source_label='NY higher timeframe fixture',**(META|{'base_timeframe':'1h','calendar':'fx-ny-17-v1'}))
    r=c.post('/api/datasets/analyze',json={'dataset_id':meta['id'],'cutoff':len(data),'interval':interval})
    assert r.status_code==200,r.text
    contract=AnalysisEnvelope.model_validate(r.json()['contract'])
    assert len(contract.candles)>=60
    assert all(bar_bounds(x.open_time,interval,'fx-ny-17-v1')==(x.open_time,x.close_time) for x in contract.candles)
    assert any(x.open_time%86400==21*3600 for x in contract.candles)


def test_import_outside_calendar_and_volume_units():
    with pytest.raises(ValueError,match='outside selected calendar'):
        read_csv(csv_bytes(rows('2024-03-09T12:00Z',1)),**(META|{'calendar':'fx-ny-17-v1'}))
    with pytest.raises(ValueError,match='Missing volume'):
        read_csv(b'time,open,high,low,close\n2024-01-01T00:00Z,1,2,0.5,1\n',**(META|{'volume_type':'tick_count'}))
