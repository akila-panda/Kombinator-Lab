import copy,json
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.sentiment import ArchiveInput,ArchiveStore,ArchiveProvider,UnavailableProvider,FRESHNESS
from backend.requests import BookSnapshotInput
from backend.analysis import sentiment, demo
from backend.main import app

T=1704067200
def iso(t):return datetime.fromtimestamp(t,timezone.utc).isoformat()
def book(t=T,retrieved=T,price=1.08):
    return {'instrument':'EUR_USD','positionBook':{'time':iso(t),'retrieved_at':iso(retrieved),'buckets':[{'price':price,'longCountPercent':80,'shortCountPercent':20}]},'orderBook':{'time':iso(t),'retrieved_at':iso(retrieved),'price':price,'buckets':[{'price':price,'longCountPercent':60,'shortCountPercent':40}]}}
def archive(db,snapshots):return db.save(ArchiveInput(label='fixture',snapshots=snapshots))['id']


def test_provider_selection_is_clock_bounded_and_per_book(tmp_path):
    db=ArchiveStore(tmp_path);old=book();future=book(T+100,T+200)
    future['positionBook']['retrieved_at']=iso(T+300)
    aid=archive(db,[future,old]);provider=ArchiveProvider(db,aid)
    before=provider.select('EUR/USD',T-1);assert before.snapshot is None
    mid=provider.select('EUR/USD',T+200).snapshot
    assert mid['positionBook']['time']==iso(T) and mid['orderBook']['time']==iso(T+100)
    assert provider.select('EUR/USD',T+300).snapshot['positionBook']['time']==iso(T+100)
    assert provider.select('GBP/USD',T+300).snapshot is None
    assert provider.select('EUR/USD',T+86501).snapshot is None


def test_missing_retrieval_is_not_historical_evidence(tmp_path):
    b=book();del b['positionBook']['retrieved_at'];del b['orderBook']['retrieved_at']
    assert sentiment(b,'EUR/USD',pd.Timestamp(T,unit='s',tz='UTC'))['status']=='unavailable'
    db=ArchiveStore(tmp_path);aid=archive(db,[b])
    assert ArchiveProvider(db,aid).select('EUR/USD',T).snapshot is None
    assert UnavailableProvider().select('EUR/USD',T).snapshot is None

@pytest.mark.parametrize('delta,available',[(0,True),(86400,True),(86401,False),(-1,False)])
def test_freshness_edges(delta,available):
    r=sentiment(book(),'EUR/USD',pd.Timestamp(T+delta,unit='s',tz='UTC'))
    assert (r['status']=='available')==available


def test_archive_persistence_identity_and_provenance(tmp_path):
    db=ArchiveStore(tmp_path);body=ArchiveInput(label='fixture',snapshots=[book()]);first=db.save(body)
    assert db.save(body)==first
    reopened=ArchiveStore(tmp_path);assert reopened.metadata(first['id'])==first
    assert first['source_kind']=='user_upload' and first['provenance_verified'] is False
    assert len(reopened.list())==1
    assert reopened.list(offset=1)==[]
    old=ArchiveProvider(reopened,first['id']).select('EUR/USD',T)
    archive(db,[book(T+50,T+50)])
    assert ArchiveProvider(reopened,first['id']).select('EUR/USD',T)==old

@pytest.mark.parametrize('mutation',['duplicate','overlap','percent_sum','bool_width','reverse_time','conflict'])
def test_bad_geometry_and_ambiguous_correction(mutation,tmp_path):
    b=book();pb=b['positionBook']
    if mutation=='duplicate':pb['buckets']*=2
    if mutation=='overlap':pb['bucketWidth']=.01;pb['buckets'].append({'price':1.081,'longCountPercent':0,'shortCountPercent':0})
    if mutation=='percent_sum':pb['buckets'][0]['shortCountPercent']=30
    if mutation=='bool_width':pb['bucketWidth']=True
    if mutation=='reverse_time':pb['retrieved_at']=iso(T-1)
    if mutation=='conflict':
        other=copy.deepcopy(b);other['positionBook']['buckets'][0]['longCountPercent']=70
        with pytest.raises(ValueError):archive(ArchiveStore(tmp_path),[b,other])
    else:
        with pytest.raises(ValueError):BookSnapshotInput.model_validate(b)


def test_instrument_timezone_sorting_and_jpy_score():
    b=book(price=150.);b['instrument']='usd/jpy';b['positionBook']['time']='2024-01-01T05:30:00+05:30'
    normalized=BookSnapshotInput.model_validate(b)
    assert normalized.instrument=='USD_JPY' and normalized.positionBook.time==iso(T)
    r=sentiment(normalized.model_dump(exclude_none=True),'USD/JPY',pd.Timestamp(T,unit='s',tz='UTC'))
    assert r['parts']['orderBook']['score']==pytest.approx(.2)
    assert r['parts']['positionBook']['score']==pytest.approx(-.15/.35)


def test_zero_mass_and_no_nearby_orders_are_unavailable():
    b=book();b['positionBook']['buckets'][0].update(longCountPercent=0,shortCountPercent=0)
    b['orderBook']['price']=2.
    r=sentiment(b,'EUR/USD',pd.Timestamp(T,unit='s',tz='UTC'))
    assert r['status']=='unavailable' and all(p['score'] is None for p in r['parts'].values())


def test_api_pinned_archive_analysis_and_future_exclusion(tmp_path,monkeypatch):
    monkeypatch.setenv('CONFLUENCE_DATA_DIR',str(tmp_path));c=TestClient(app)
    candles=demo('EUR/USD')[:100];clock=candles[-1]['time']+3600;b=book(clock-100,clock)
    aid=c.post('/api/sentiment/archives',json={'label':'api fixture','snapshots':[b]}).json()['id']
    r=c.post('/api/analyze',json={'candles':candles,'archive_id':aid})
    assert r.status_code==200,r.text
    result=r.json();obs=result['contract']['sentiment']['observations']
    assert len(obs)==2 and all(o['source']['id']=='archive:'+aid for o in obs)
    assert all(o['availability_basis']=='retrieval_time' for o in obs)
    assert c.get(f'/api/sentiment/archives/{aid}/at',params={'symbol':'EUR/USD','as_of':clock-1}).json()['status']=='unavailable'
    assert c.get('/api/sentiment/providers').json()['providers'][1]['available'] is False
    assert c.get('/api/sentiment/archives').json()['archives'][0]['id']==aid
    assert c.get('/api/sentiment/archives/unknown').status_code==404
    assert c.post('/api/analyze',json={'candles':candles,'archive_id':aid,'snapshot':b}).status_code==422
    meta=c.post('/api/datasets/demo').json()
    d=c.post('/api/datasets/analyze',json={'dataset_id':meta['id'],'cutoff':100,'archive_id':aid})
    assert d.status_code==200 and d.json()['contract']['sentiment']==result['contract']['sentiment']
    # A later archive cannot silently change the pinned historical result.
    c.post('/api/sentiment/archives',json={'label':'other','snapshots':[book(clock-50,clock)]})
    assert c.post('/api/analyze',json={'candles':candles,'archive_id':aid}).json()==result


def test_archive_schema_matches_export():
    path=Path(__file__).resolve().parents[1]/'docs/contracts/sentiment-archive.schema.json'
    assert json.loads(path.read_text())==ArchiveInput.model_json_schema()
