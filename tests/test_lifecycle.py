import copy
import json
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.lifecycle import replay, project, summary, Event, VERSION
from backend.analysis import analyze, demo, frame
from backend.calendars import aggregate_frame
from backend.datasets import DatasetStore
from backend.dataset_api import store
from backend.main import app


def fixture(n=80):
    index=pd.date_range('2024-01-01',periods=n,freq='h',tz='UTC')
    return pd.DataFrame({'open':1.,'high':1.01,'low':.99,'close':1.,'volume':0.,'close_time':[(int(t.timestamp())+3600) for t in index]},index=index)
def events(df):return replay(df,source_id='fixture',symbol='EUR/USD',timeframe='1h',calendar='fixed-utc-v1')
def clock(df,i):return int(df.close_time.iloc[i])


def test_pivot_not_available_until_right_close_and_preserved():
    df=fixture(90);df.loc[df.index[20],'high']=1.03;df.loc[df.index[70],'high']=1.04
    early=events(df.iloc[:23]);candidate=next(e for e in early if e['finding_kind']=='pivot_high' and e['kind']=='occurrence')
    assert candidate['available_at']==clock(df,20)
    assert not summary(early,clock(df,22))['available_findings']
    confirmed=events(df.iloc[:24]);confirmation=next(e for e in confirmed if e['kind']=='confirmation')
    assert confirmation['available_at']==clock(df,23)
    assert max(e['close_time'] for e in confirmation['evidence'])==clock(df,23)
    full=events(df)
    assert confirmation in full
    assert any(e['kind']=='revision' and e['finding_id']==candidate['finding_id'] for e in full)
    assert next(f for f in project(full,clock(df,23)) if f['id']==candidate['finding_id'])['status']=='confirmed'


def test_candidate_defeated_before_confirmation():
    df=fixture(30);df.loc[df.index[20],'high']=1.03;df.loc[df.index[22],'high']=1.04
    ev=events(df);first=next(e for e in ev if e['kind']=='occurrence')
    history=[e for e in ev if e['finding_id']==first['finding_id']]
    assert [e['kind'] for e in history]==['occurrence','invalidation']
    assert history[-1]['available_at']==clock(df,22)
    state=next(f for f in project(ev,clock(df,29)) if f['id']==first['finding_id'])
    assert state['confirmed_at'] is None and state['status']=='invalidated'


def test_break_uses_only_prior_confirmed_level_and_current_atr():
    df=fixture(70);df.loc[df.index[20],'high']=1.03
    df.loc[df.index[30],['open','close','high']]=[1.,1.04,1.05]
    early=events(df.iloc[:31]);breaks=[e for e in early if e['finding_kind']=='bos' and e['kind']=='confirmation']
    assert len(breaks)==1 and breaks[0]['available_at']==clock(df,30)
    assert breaks[0]['prices']==[1.03]
    # Later volatility/trend changes must not change the saved break or its ATR buffer.
    df.loc[df.index[40]:,['high','low']]=[2.,.5]
    assert [e for e in events(df) if e['available_at']<=clock(df,30)]==early
    invalid=next(e for e in early if e['finding_kind']=='pivot_high' and e['kind']=='invalidation')
    assert invalid['available_at']==clock(df,30)


def test_expiration_has_clock_and_evidence():
    df=fixture(190);df.loc[df.index[20],'high']=1.03
    ev=events(df);expiry=next(e for e in ev if e['kind']=='expiration')
    assert expiry['available_at']==clock(df,183)
    assert expiry['evidence'][-1]['close_time']==clock(df,183)
    assert next(f for f in project(ev,clock(df,182)) if f['id']==expiry['finding_id'])['status']=='confirmed'
    assert next(f for f in project(ev,clock(df,183)) if f['id']==expiry['finding_id'])['status']=='expired'


def test_gap_and_block_confirmation_and_invalidation():
    df=fixture(40)
    df.loc[df.index[20],['open','high','low','close']]=[1.,1.01,.99,.995]
    df.loc[df.index[21],['open','high','low','close']]=[.995,1.06,.99,1.055]
    df.loc[df.index[22]:df.index[30],['open','high','low','close']]=[1.055,1.07,1.04,1.06]
    df.loc[df.index[31],['open','high','low','close']]=[1.06,1.07,.97,.98]
    ev=events(df)
    fvg=next(e for e in ev if e['finding_kind']=='fvg' and e['kind']=='confirmation')
    ob=next(e for e in ev if e['finding_kind']=='order_block' and e['kind']=='confirmation')
    assert fvg['available_at']==clock(df,22) and ob['available_at']==clock(df,21)
    assert fvg['occurred_at']==int(df.index[20].timestamp())
    for e in (fvg,ob):
        assert any(x['finding_id']==e['finding_id'] and x['kind']=='invalidation' and x['available_at']==clock(df,31) for x in ev)


def test_divergence_only_at_pivot_confirmation():
    df=fixture(60)
    close=np.r_[np.linspace(1.2,1.,20),.9,np.linspace(.95,1.1,10),np.linspace(1.08,.89,10),np.linspace(.95,1.05,19)]
    df['open']=df['close']=close;df['high']=close+.005;df['low']=close-.005
    ev=events(df)
    div=next(e for e in ev if e['finding_kind']=='rsi_divergence' and e['kind']=='confirmation')
    assert div['direction']=='bullish'
    origin=next(i for i,t in enumerate(df.index) if int(t.timestamp())==div['occurred_at'])
    assert div['available_at']==clock(df,origin+3)
    assert not any(e['finding_id']==div['finding_id'] for e in events(df.iloc[:origin+3]))


def test_every_prefix_matches_full_replay_event_by_event():
    raw=demo('EUR/USD')[:90];df=frame(raw,len(raw));df['close_time']=[int(t.timestamp())+3600 for t in df.index]
    full=events(df)
    for end in range(1,len(df)+1):
        expected=[e for e in full if e['available_at']<=clock(df,end-1)]
        assert events(df.iloc[:end])==expected
        assert project(full,clock(df,end-1))==project(expected,clock(df,end-1))


def test_future_evidence_and_bad_transition_rejected():
    df=fixture(30);df.loc[df.index[20],'high']=1.03
    ev=events(df)[0]
    bad=copy.deepcopy(ev);bad['evidence'][-1]['close_time']=bad['available_at']+3600
    with pytest.raises(ValueError):Event.model_validate(bad)
    with pytest.raises(ValueError):Event.model_validate(ev|{'status':'confirmed'})


def test_store_persistence_earlier_clock_and_idempotence(tmp_path):
    db=DatasetStore(tmp_path);data=demo('EUR/USD')[:200]
    meta=db.save(data,symbol='EUR/USD',base_timeframe='1h',calendar='utc-weekdays-v1',source_kind='synthetic',source_label='journal fixture')
    df=frame(data,len(data));df['close_time']=[int(t.timestamp())+3600 for t in df.index]
    full=events(df);old=events(df.iloc[:80]);oldclock=clock(df,79)
    db.record_events(meta['id'],'1h',VERSION,old,oldclock)
    saved=db.events(meta['id'],'1h',VERSION,oldclock,limit=1000)
    db.record_events(meta['id'],'1h',VERSION,full,clock(df,199))
    db.record_events(meta['id'],'1h',VERSION,old,oldclock)
    reopened=DatasetStore(tmp_path);got=reopened.events(meta['id'],'1h',VERSION,oldclock,limit=1000)
    assert got==saved
    assert got['events']==old
    first=reopened.events(meta['id'],'1h',VERSION,clock(df,199),limit=3)
    second=reopened.events(meta['id'],'1h',VERSION,clock(df,199),after=first['next_after'],limit=3)
    assert first['events']+second['events']==full[:6]
    bad=copy.deepcopy(old);bad[0]['reason']='rewritten'
    with pytest.raises(RuntimeError):db.record_events(meta['id'],'1h',VERSION,bad,oldclock)
    assert db.events(meta['id'],'1h',VERSION,oldclock,limit=1000)['events']==old


def test_dataset_event_api_and_retrospective_separation(tmp_path):
    db=DatasetStore(tmp_path);app.dependency_overrides[store]=lambda:db
    try:
        client=TestClient(app);meta=client.post('/api/datasets/demo').json();path=f"/api/datasets/{meta['id']}/events"
        assert client.get(path).json()['status']=='unavailable'
        r=client.post('/api/datasets/analyze',json={'dataset_id':meta['id'],'cutoff':150}).json()
        assert r['retrospective_only'] and r['contract']['retrospective_findings_only']
        assert all(f['status']=='provisional' and f['confirmed_at'] is None for f in r['contract']['findings'])
        asof=r['historical']['as_of'];saved=client.get(path,params={'as_of':asof,'limit':1000}).json()
        assert saved['status']=='available' and saved['events']
        later=client.post('/api/datasets/analyze',json={'dataset_id':meta['id'],'cutoff':180})
        assert later.status_code==200
        assert client.get(path,params={'as_of':asof,'limit':1000}).json()['events']==saved['events']
        assert client.post('/api/datasets/analyze',json={'dataset_id':meta['id'],'cutoff':150}).json()==r
    finally:app.dependency_overrides.pop(store,None)


def test_calendar_close_times_drive_availability():
    raw=demo('EUR/USD')[:2000];base=frame(raw,len(raw))
    daily=aggregate_frame(base,'d1',pd.Timestamp(raw[-1]['time']+3600,unit='s',tz='UTC'),'1h','utc-weekdays-v1')
    ev=replay(daily,source_id='calendar-fixture',symbol='EUR/USD',timeframe='d1',calendar='utc-weekdays-v1')
    assert ev
    closes=set(int(x) for x in daily.close_time)
    assert all(e['available_at'] in closes for e in ev)
    cut=40;clock_=int(daily.close_time.iloc[cut-1])
    prefix=replay(daily.iloc[:cut],source_id='calendar-fixture',symbol='EUR/USD',timeframe='d1',calendar='utc-weekdays-v1')
    assert prefix==[e for e in ev if e['available_at']<=clock_]


def test_schema_export_and_nondestructive_v1_migration(tmp_path):
    from pathlib import Path
    import sqlite3
    db=DatasetStore(tmp_path)
    meta=db.save(demo('EUR/USD')[:100],symbol='EUR/USD',base_timeframe='1h',calendar='utc-weekdays-v1',source_kind='synthetic',source_label='migration')
    # Recreate the exact pre-journal table set/version, preserving stored candles.
    with sqlite3.connect(db.path) as conn:
        conn.execute('DROP TABLE finding_events');conn.execute('DROP TABLE event_runs');conn.execute('PRAGMA user_version=1')
    migrated=DatasetStore(tmp_path)
    assert migrated.get(meta['id'])==meta
    assert len(migrated.prefix(meta['id'],100)[1])==100
    with sqlite3.connect(db.path) as conn:assert conn.execute('PRAGMA user_version').fetchone()[0]==2
    schema=json.loads((Path(__file__).resolve().parents[1]/'docs/contracts/historical-event.schema.json').read_text())
    assert schema==Event.model_json_schema()


def test_journal_integrity_failure_is_explicit(tmp_path,monkeypatch):
    from backend.datasets import EventJournalError
    db=DatasetStore(tmp_path);app.dependency_overrides[store]=lambda:db
    try:
        c=TestClient(app);meta=c.post('/api/datasets/demo').json()
        def conflict(*args):raise EventJournalError('Internal mismatch')
        monkeypatch.setattr(db,'record_events',conflict)
        response=c.post('/api/datasets/analyze',json={'dataset_id':meta['id'],'cutoff':100})
        assert response.status_code==500 and response.json()['detail']['error']=='event_journal_conflict'
        result=analyze(demo('EUR/USD'),'EUR/USD','1h',100)
        assert result['module_runs'][-1]['calculation_version']==VERSION
    finally:app.dependency_overrides.pop(store,None)
