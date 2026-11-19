from copy import deepcopy
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.accounting import AccountCommand, AccountSettings, execute_account
from backend.dataset_api import store
from backend.datasets import DatasetStore
from backend.main import app

T=1704153600

def bar(i,o=1.1,h=None,l=None,c=None):
    return dict(time=T+i*60,open=o,high=h if h is not None else o,low=l if l is not None else o,close=c if c is not None else o,volume=None)

def order(oid='a',time=T,**kw):
    return AccountCommand(command_id='submit-'+oid,order_id=oid,time=time,action='submit',side=kw.pop('side','buy'),kind=kw.pop('kind','market'),units=kw.pop('units',1000),**kw)

def close(time=T+60,units=None,oid='a',cid='close'):
    return AccountCommand(command_id=cid,order_id=oid,time=time,action='close',units=units)

def run(commands,rows=None,clock=None,symbol='EUR/USD',spread=1,**settings):
    rows=rows if rows is not None else [bar(0),bar(1,1.101)]
    return execute_account(rows,symbol,T,clock if clock is not None else rows[-1]['time']+60,commands,spread,AccountSettings(**settings))

def exits(s):return [e for e in s['events'] if e['type']=='closed']

def reconcile(s):
    a={k:Decimal(v) for k,v in s['account'].items()}
    assert a['balance']==Decimal(str(s['settings']['initial_balance']))+a['realized_pnl']-a['commission_paid']
    assert a['equity']==a['balance']+a['unrealized_pnl']
    assert a['free_margin']==a['equity']-a['used_margin']

@pytest.mark.parametrize('side,next_open', [('buy',1.101),('sell',1.099)])
def test_long_short_manual_costs(side,next_open):
    s=run([order(side=side),close()],rows=[bar(0),bar(1,next_open)])
    assert s['account']['realized_pnl']=='0.90'
    assert s['account']['commission_paid']=='0.08'
    assert s['account']['balance']=='10000.82'
    assert s['account']['used_margin']=='0.00'
    assert s['positions'][0]['remaining_units']==0
    assert exits(s)[0]['time']==T+120
    reconcile(s)

def test_partial_close_round_trip_and_mark():
    commands=[order(units=100000),close(units=40000),close(T+120,cid='last')]
    rows=[bar(0),bar(1,1.101),bar(2,1.102)]
    early=run(commands[:2],rows[:2])
    assert early['account']['balance']=='10031.10'
    assert early['account']['unrealized_pnl']=='54.00'
    assert early['account']['equity']=='10085.10'
    assert early['account']['used_margin']=='2202.00'
    s=run(commands,rows)
    assert [e['units'] for e in exits(s)]==[40000,60000]
    assert s['account']['realized_pnl']=='150.00'
    assert s['account']['balance']=='10143.00'
    assert s['account']['commission_paid']=='7.00'
    reconcile(early);reconcile(s)

def test_slippage_applies_once_per_market_side():
    s=run([order(),close()],slippage_pips=1)
    assert s['positions'][0]['entry_price']=='1.10020'
    assert exits(s)[0]['price']=='1.10090'
    assert s['account']['realized_pnl']=='0.70'
    reconcile(s)

@pytest.mark.parametrize('side,sl,tp,expected',[
    ('buy',1.099,1.102,'1.09900'),('sell',1.102,1.099,'1.10200')])
def test_both_exits_stop_first(side,sl,tp,expected):
    s=run([order(side=side,stop_loss=sl,take_profit=tp)],rows=[bar(0,h=1.103,l=1.098)])
    e=exits(s)[0]
    assert e['reason']=='stop_loss' and e['ambiguous'] and e['price']==expected
    reconcile(s)

@pytest.mark.parametrize('side,sl,tp,opened,expected,reason',[
    ('buy',1.099,1.102,1.097,'1.09690','stop_loss'),
    ('sell',1.102,1.099,1.104,'1.10420','stop_loss'),
    ('buy',1.099,1.102,1.104,'1.10400','take_profit'),
    ('sell',1.102,1.099,1.097,'1.09710','take_profit'),
])
def test_gap_exits_and_limit_price_protection(side,sl,tp,opened,expected,reason):
    s=run([order(side=side,stop_loss=sl,take_profit=tp)],rows=[bar(0),bar(10,opened)],slippage_pips=1)
    e=exits(s)[0]
    assert e['price']==expected and e['reason']==reason and not e['ambiguous']
    assert e['bar_open_time']==T+600
    reconcile(s)

def test_intrabar_entry_tp_only_deferred_then_stop():
    c=order(kind='stop',price=1.101,stop_loss=1.099,take_profit=1.102)
    first=bar(0,h=1.103,l=1.1,c=1.101)
    s=run([c],rows=[first])
    assert not exits(s)
    assert any(e['type']=='ambiguous_exit_deferred' for e in s['events'])
    s=run([c],rows=[first,bar(1,1.101,h=1.103,l=1.098)])
    assert exits(s)[0]['reason']=='stop_loss' and exits(s)[0]['ambiguous']
    s=run([c],rows=[bar(0,h=1.103,l=1.098)])
    assert exits(s)[0]['ambiguous'] and exits(s)[0]['reason']=='stop_loss'

def test_new_market_entry_stop_inside_spread_uses_open_quote():
    s=run([order(stop_loss=1.10005)],rows=[bar(0)])
    assert exits(s)[0]['price']=='1.10000'
    assert s['account']['realized_pnl']=='-0.10'

def test_insufficient_margin_rejects_fill_without_charging():
    s=run([order(units=100000)],initial_balance=100,leverage=30)
    assert not s['positions'] and s['orders'][0]['status']=='rejected'
    assert 'margin' in s['orders'][0]['reason']
    assert s['account']['balance']=='100.00' and s['account']['commission_paid']=='0.00'
    reconcile(s)

def test_entry_costs_and_pending_orders_compete_for_margin():
    s=run([order(units=1000)],initial_balance=36.7,leverage=30)
    assert not s['positions'] # 36.67 margin plus spread and commission
    s=run([order('a',units=1000),order('b',units=1000)],initial_balance=50)
    assert len(s['positions'])==1 and s['orders'][1]['status']=='rejected'
    reconcile(s)

def test_margin_call_visible_without_hidden_liquidation():
    s=run([order(units=100000)],rows=[bar(0),bar(1,.99)],initial_balance=4000)
    assert s['margin_call'] and s['positions'][0]['status']=='open'
    assert s['policy']['automatic_liquidation']=='excluded' and s['policy']['financing']=='excluded'
    reconcile(s)

def test_jpy_conversion_and_usd_base_margin():
    s=run([order(units=1000),close()],rows=[bar(0,150),bar(1,151)],symbol='USD/JPY')
    assert s['account']['realized_pnl']=='6.56' # 990 JPY / 151
    assert exits(s)[0]['conversion_price']=='151.000'
    early=run([order(units=1000)],rows=[bar(0,150)],symbol='USD/JPY')
    assert early['account']['used_margin']=='33.33'
    assert early['account']['unrealized_pnl']=='-0.07'
    reconcile(s);reconcile(early)

def test_close_rejections_and_gap_protection_priority():
    s=run([close(time=T)])
    assert s['events'][0]['type']=='close_rejected'
    s=run([order(),close(units=1001)])
    assert any(e['type']=='close_rejected' for e in s['events'])
    s=run([order(stop_loss=1.099),close()],rows=[bar(0),bar(1,1.098)])
    assert len(exits(s))==1 and exits(s)[0]['reason']=='stop_loss'
    assert s['events'][-1]['type']=='close_rejected'
    s=run([order(),close(),close(cid='duplicate')])
    assert len(exits(s))==1 and any(e.get('reason')=='A close is already pending for this position' for e in s['events'])

def test_end_pending_close_and_future_isolation():
    commands=[order(),close()];rows=[bar(0),bar(1),bar(2,1.2)]
    s=run(commands,rows,clock=T+60)
    assert not exits(s) and len(s['pending_closes'])==1
    changed=deepcopy(rows);changed[1]=bar(1,2);changed[2]=bar(2,3)
    assert s==run(commands,changed,clock=T+60)==run(commands,rows[:1])
    later=run(commands,rows)
    assert later['events'][:len(s['events'])]==s['events']
    assert later==run(commands,rows)

def test_invalid_bracket_and_settings():
    s=run([order(stop_loss=1.2)])
    assert not s['positions'] and s['orders'][0]['status']=='rejected'
    with pytest.raises(ValueError,match='ticks'):run([],slippage_pips=.015)
    with pytest.raises(ValueError,match='0.01'):run([],initial_balance=.001)


def test_account_endpoint(tmp_path):
    db=DatasetStore(tmp_path)
    meta=db.save([bar(0),bar(1,1.101)],symbol='EUR/USD',base_timeframe='1m',calendar='fixed-utc-v1',source_kind='synthetic',source_label='account fixture')
    body=dict(dataset_id=meta['id'],start=T,clock=T+120,input_price_basis='bid',commands=[order().model_dump(),close().model_dump()])
    app.dependency_overrides[store]=lambda:db
    try:
        with TestClient(app) as client:
            r=client.post('/api/paper/account-replay',json=body)
            assert r.status_code==200
            assert r.json()['account']['balance']=='10000.82'
            assert client.post('/api/paper/account-replay',json=body).json()==r.json()
            assert client.post('/api/paper/account-replay',json={**body,'clock':T+180}).status_code==422
            for settings in ({'leverage':0},{'commission_per_100k':-1},{'slippage_pips':-1},{'initial_balance':0}):
                assert client.post('/api/paper/account-replay',json={**body,'account':settings}).status_code==422
    finally:app.dependency_overrides.clear()

def test_short_partial_close_and_remaining_protection():
    s=run([order(side='sell',units=100000,take_profit=1.098),close(units=40000)],
          rows=[bar(0),bar(1,1.099,h=1.099,l=1.0979,c=1.098)])
    assert [e['reason'] for e in exits(s)]==['manual','take_profit']
    assert [e['units'] for e in exits(s)]==[40000,60000]
    assert s['account']['realized_pnl']=='156.00' # 36 + 120
    assert s['account']['balance']=='10149.00'
    reconcile(s)

def test_limit_entry_has_no_adverse_slippage():
    s=run([order(kind='limit',price=1.101)],rows=[bar(0)],slippage_pips=10)
    assert s['positions'][0]['entry_price']=='1.10010'
    assert s['account']['unrealized_pnl']=='-0.10'
    reconcile(s)

def test_intrabar_exit_proceeds_cannot_fund_earlier_entry():
    commands=[order('a',units=1000,take_profit=1.2),order('b',time=T+60,units=1000)]
    s=run(commands,rows=[bar(0),bar(1,1.1,h=1.2)],initial_balance=50)
    assert s['orders'][1]['status']=='rejected' # b opens before a's future TP
    assert exits(s)[0]['reason']=='take_profit'
    reconcile(s)

def test_gap_close_and_stale_valuation_are_explicit():
    s=run([order(),close(T+120)],rows=[bar(0)],clock=T+600)
    assert s['mark_time']==T+60 and s['pending_closes'] and not exits(s)
    later=run([order(),close(T+120)],rows=[bar(0),bar(20,1.102)])
    assert exits(later)[0]['bar_open_time']==T+1200
    assert exits(later)[0]['price']=='1.10200'


def test_gbp_usd_account_conversion_is_identity():
    s=run([order(),close()],symbol='GBP/USD')
    assert s['account']['realized_pnl']=='0.90'
    reconcile(s)


def test_jpy_short_uses_ask_conversion():
    s=run([order(side='sell'),close()],rows=[bar(0,150),bar(1,149)],symbol='USD/JPY')
    assert exits(s)[0]['conversion_price']=='149.010'
    assert s['account']['realized_pnl']=='6.64'
    reconcile(s)
