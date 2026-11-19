import math
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.datasets import DatasetStore
from backend.dataset_api import store
from backend.replay_api import ReplayRequest,replay_state,completed_analysis

START=1704153600
@pytest.fixture
def history(tmp_path):
    db=DatasetStore(tmp_path)
    rows=[]
    for i in range(3700):
        p=1.1+.002*math.sin(i/80)
        rows.append(dict(time=START+i*60,open=p,high=p+.0002,low=p-.0002,close=p+.0001,volume=None))
    meta=db.save(rows,symbol='EUR/USD',base_timeframe='1m',calendar='fixed-utc-v1',source_kind='synthetic',source_label='replay fixture')
    yield db,meta,rows
    completed_analysis.cache_clear()


def state(db,meta,clock,action='seek',timeframe='15m'):
    return replay_state(db,ReplayRequest(dataset_id=meta['id'],clock=clock,action=action,timeframe=timeframe))


def test_pause_step_forming_and_completion(history):
    db,m,rows=history;s=state(db,m,START)
    assert not s['views']['15m']['completed'] and not s['views']['15m']['forming']
    assert s==state(db,m,START) # no wall-time state
    one=state(db,m,START,'minute')
    assert one['clock']==START+60
    for tf in ('15m','1h'):
        f=one['views'][tf]['forming'];assert f['high']==rows[0]['high'] and f['close']==rows[0]['close']
        assert one['views'][tf]['clock']==one['clock']
    done=state(db,m,START,'candle')
    assert done['clock']==START+900
    assert len(done['views']['15m']['completed'])==1 and done['views']['15m']['forming'] is None
    assert done['views']['1h']['forming']['revealed_minutes']==15
    assert done['analysis'] is None


def test_out_of_coverage_and_end(history):
    db,m,_=history
    for clock in (START-60,m['end']+60,START+1):
        with pytest.raises(ValueError):state(db,m,clock)
    s=state(db,m,m['end'],'minute');assert s['state']=='ended' and s['clock']==m['end'] and s['next_minute_close'] is None


def test_future_prices_never_reach_forming_or_signals(history):
    db,m,rows=history;clock=START+3601*60
    a=state(db,m,clock)
    altered=[dict(r) for r in rows]
    for r in altered[3601:]:
        for k in ('open','high','low','close'):r[k]*=2
    other=db.save(altered,symbol='EUR/USD',base_timeframe='1m',calendar='fixed-utc-v1',source_kind='synthetic',source_label='future mutation')
    b=state(db,other,clock)
    assert a['views']==b['views']
    assert a['analysis_status']=='available'
    assert a['analysis']['indicators']==b['analysis']['indicators']
    assert a['analysis']['candles']==b['analysis']['candles']
    assert a['analysis']['contract']['snapshot']['as_of']==START+3600*60
    assert all(e['available_at']<=START+3600*60 for e in a['analysis']['contract']['evidence'])
    # Revealing part of the next hour does not recalculate complete-hour signals.
    later=state(db,m,clock+60)
    assert a['analysis']==later['analysis']


def test_missing_minute_not_fabricated(history):
    db,_,rows=history
    missing=rows[:5]+rows[6:40]
    m=db.save(missing,symbol='EUR/USD',base_timeframe='1m',calendar='fixed-utc-v1',source_kind='synthetic',source_label='gaps')
    s=state(db,m,START+5*60);assert s['state']=='data_gap'
    n=state(db,m,s['clock'],'minute');assert n['advanced_seconds']==120
    assert n['views']['15m']['forming']['state']=='forming_with_gaps'
    done=state(db,m,START+15*60);assert not done['views']['15m']['completed']
    assert done['views']['15m']['excluded']['missing_input']==1


def test_closed_market_seek_and_skip(tmp_path):
    db=DatasetStore(tmp_path)
    friday=1704491940;sunday=1704664800
    rows=[dict(time=t,open=1.,high=1.1,low=.9,close=1.,volume=None) for t in (friday,sunday)]
    m=db.save(rows,symbol='EUR/USD',base_timeframe='1m',calendar='fx-ny-17-v1',source_kind='synthetic',source_label='weekend')
    closed=state(db,m,friday+60);assert closed['state']=='closed_market'
    n=state(db,m,friday+60,'minute');assert n['clock']==sunday+60 and n['revealed_minutes']==2


def test_http_contract_and_hourly_rejection(history):
    db,m,rows=history;app.dependency_overrides[store]=lambda:db
    try:
        with TestClient(app) as client:
            q={'dataset_id':m['id'],'clock':START+60}
            assert client.post('/api/replay/state',json=q).status_code==200
            assert client.post('/api/replay/state',json=q|{'clock':START-60}).status_code==422
            assert client.post('/api/replay/state',json=q|{'action':'trade'}).status_code==422
            h=db.save(rows[::60],symbol='EUR/USD',base_timeframe='1h',calendar='fixed-utc-v1',source_kind='synthetic',source_label='hourly')
            assert client.post('/api/replay/state',json=q|{'dataset_id':h['id']}).status_code==422
    finally:app.dependency_overrides.pop(store,None)
