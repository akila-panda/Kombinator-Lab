from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.dataset_api import store
from backend.datasets import DatasetStore
from backend.orders import OrderCommand, OrderReplayRequest, execute
from backend.order_api import replay

T = 1704153600

def bar(i, o=1.1, h=1.102, l=1.098, c=1.101):
    return dict(time=T+i*60, open=o, high=h, low=l, close=c, volume=None)

def submit(oid='a', time=T, **kw):
    return OrderCommand(command_id='submit-'+oid, order_id=oid, time=time,
                        action='submit', side=kw.pop('side','buy'), kind=kw.pop('kind','market'),
                        units=kw.pop('units',1000), **kw)

def cancel(oid='a', time=T):
    return OrderCommand(command_id='cancel-'+oid, order_id=oid, time=time, action='cancel')

def run(commands, rows=None, clock=T+120, symbol='EUR/USD', spread=1):
    return execute(rows if rows is not None else [bar(0),bar(1)],symbol,T,clock,commands,spread)

def test_market_next_bar_and_spread():
    commands=[submit('buy',T+60),submit('sell',T+60,side='sell')]
    s=run(commands,clock=T+60)
    assert not s['positions']
    s=run(commands,rows=[bar(0),bar(1,o=1.101)])
    assert [p['entry_price'] for p in s['positions']]==['1.10110','1.10100']
    assert all(p['opened_at']==T+120 and p['bar_open_time']==T+60 for p in s['positions'])
    assert [e['type'] for e in s['events']]==['submitted','accepted','submitted','accepted','filled','filled']

@pytest.mark.parametrize('side,kind,trigger,expected',[
    ('buy','limit',1.099,'1.09900'),('sell','limit',1.101,'1.10100'),
    ('buy','stop',1.101,'1.10100'),('sell','stop',1.099,'1.09900'),
])
def test_four_intrabar_triggers(side,kind,trigger,expected):
    s=run([submit(side=side,kind=kind,price=trigger)],clock=T+60)
    assert s['positions'][0]['entry_price']==expected
    assert s['events'][-1]['intrabar_time_unknown']
    assert s['events'][-1]['time']==T+60

@pytest.mark.parametrize('side,kind,trigger,opened,expected',[
    ('buy','limit',1.100,1.099,'1.09910'),('sell','limit',1.100,1.101,'1.10100'),
    ('buy','stop',1.100,1.101,'1.10110'),('sell','stop',1.100,1.099,'1.09900'),
])
def test_gaps_use_observed_open(side,kind,trigger,opened,expected):
    s=run([submit(side=side,kind=kind,price=trigger)],rows=[bar(10,o=opened)],clock=T+660)
    assert s['positions'][0]['entry_price']==expected
    assert s['events'][-1]['price_basis']=='open'
    assert s['events'][-1]['time']==T+660

def test_buy_triggers_use_ask_not_bid():
    s=run([submit(kind='limit',price=1.098)],clock=T+60)
    assert not s['positions'] # bid low reaches 1.098; simulated ask low is 1.0981

def test_cancel_before_next_bar_and_same_close_after_fill():
    s=run([submit(),cancel()])
    assert s['orders'][0]['status']=='cancelled' and not s['positions']
    s=run([submit(),cancel(time=T+60)])
    assert s['orders'][0]['status']=='filled'
    assert s['events'][-1]['type']=='cancel_rejected'
    s=run([submit(),cancel(time=T+120)],rows=[bar(10)],clock=T+660)
    assert not s['positions']

@pytest.mark.parametrize('fields',[
    {'units':0},{'units':-1},{'units':100_000_001},
    {'kind':'limit'},{'kind':'stop','price':-1},{'kind':'limit','price':0},
    {'kind':'limit','price':.000001},{'price':1.1},
])
def test_invalid_business_orders_have_rejection_ledger(fields):
    s=run([submit(**fields)])
    assert s['orders'][0]['status']=='rejected'
    assert [e['type'] for e in s['events']]==['submitted','rejected']
    assert not s['positions']

def test_price_rounding_and_jpy_units():
    s=run([submit(kind='stop',price=1.100005)])
    assert s['orders'][0]['price']=='1.10001'
    s=run([submit(units=123)],symbol='USD/JPY',rows=[bar(0,150,151,149,150)],clock=T+60)
    assert s['positions'][0]['entry_price']=='150.010'
    assert s['positions'][0]['units']==123
    with pytest.raises(ValueError,match='ticks'):
        run([],spread=.015)

def test_future_mutation_and_chunk_invariance():
    rows=[bar(i) for i in range(4)];changed=deepcopy(rows)
    for r in changed[2:]:
        for k in ('open','high','low','close'):r[k]*=2
    commands=[submit(),submit('later',T+60,kind='stop',price=1.2)]
    early=run(commands,rows,clock=T+120)
    assert early==run(commands,changed,clock=T+120)==run(commands,rows[:2],clock=T+120)
    later=run(commands,rows,clock=T+240)
    assert later['events'][:len(early['events'])]==early['events']
    assert run(commands,rows,clock=T+240)==later

def test_command_order_duplicate_and_boundary_validation():
    with pytest.raises(ValueError,match='unique'):run([submit(),submit()])
    with pytest.raises(ValueError,match='chronological'):run([submit('a',T+60),submit('b')])
    with pytest.raises(ValueError,match='minute-aligned'):run([submit(time=T+1)])
    with pytest.raises(ValueError,match='minute-aligned'):run([submit(time=T+180)])
    s=run([submit(),OrderCommand(command_id='again',order_id='a',action='submit',time=T,side='sell',kind='market',units=100)])
    assert len(s['positions'])==1 and s['orders'][0]['side']=='buy'
    assert any(e['type']=='rejected' for e in s['events'])
    assert run([cancel()])['events'][0]['type']=='cancel_rejected'

@pytest.fixture
def dataset(tmp_path):
    db=DatasetStore(tmp_path)
    meta=db.save([bar(i) for i in range(4)],symbol='EUR/USD',base_timeframe='1m',calendar='fixed-utc-v1',source_kind='synthetic',source_label='paper fixture')
    return db,meta

def test_api_uses_stored_prices_and_keeps_pending_at_end(dataset):
    db,meta=dataset;app.dependency_overrides[store]=lambda:db
    body=dict(dataset_id=meta['id'],start=T,clock=T+240,input_price_basis='bid',commands=[submit(kind='limit',price=.5).model_dump()])
    try:
        with TestClient(app) as client:
            r=client.post('/api/paper/replay',json=body)
            assert r.status_code==200
            s=r.json();assert s['ended'] and s['orders'][0]['status']=='pending' and not s['positions']
            assert not s['input_price_basis_verified']
            assert client.post('/api/paper/replay',json={**body,'candles':[bar(0)]}).status_code==422
            assert client.post('/api/paper/replay',json={**body,'clock':T+300}).status_code==422
            assert client.post('/api/paper/replay',json={**body,'dataset_id':'0'*64}).status_code==404
            assert client.post('/api/paper/replay',json={**body,'input_price_basis':'mid'}).status_code==422
            for units in (1.5, True, '100'):
                bad=deepcopy(body);bad['commands'][0]['units']=units
                assert client.post('/api/paper/replay',json=bad).status_code==422
    finally:app.dependency_overrides.clear()

def test_endpoint_repeatability_and_start_exclusion(dataset):
    db,meta=dataset
    req=OrderReplayRequest(dataset_id=meta['id'],start=T+60,clock=T+120,input_price_basis='bid',commands=[submit(time=T+60)])
    first=replay(db,req)
    assert first==replay(db,req)
    assert first['positions'][0]['bar_open_time']==T+60


def test_zero_rounded_quote_is_not_an_executable_price():
    tiny=bar(0,.000001,.000002,.000001,.000001)
    with pytest.raises(ValueError,match='quote rounds to zero'):
        run([submit(side='sell')],rows=[tiny],clock=T+60)
