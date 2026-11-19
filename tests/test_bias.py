import numpy as np
import pandas as pd
import pytest
from backend.bias import evaluate, resolve, VERSION
from backend.analysis import analyze, demo


def candles(n=100,trend=.002):
    t=pd.date_range('2022-01-01',periods=n,freq='D',tz='UTC')
    c=1+np.arange(n)*trend+.03*np.sin(np.arange(n)/2)
    return pd.DataFrame({'open':c-.001,'high':c+.003,'low':c-.003,'close':c,'close_time':[int(x.timestamp())+86400 for x in t]},index=t)


def result(df,horizon='daily',sentiment=None):
    return evaluate(df,horizon,'EUR/USD','test',int(df.close_time.iloc[-1]),sentiment or {'status':'unavailable','reason':'No source'})


@pytest.mark.parametrize('trend,direction',[(.002,'bullish'),(-.002,'bearish')])
def test_directional_scenarios(trend,direction):
    b=result(candles(trend=trend))
    assert b['direction']==direction
    assert b['version']==VERSION and b['levels'] and b['invalidation']
    assert all(e['available_at']<=b['as_of'] for e in b['evidence'])


def test_flat_neutral_and_missing_history():
    df=candles();df[['open','high','low','close']]=1.
    assert result(df)['direction']=='neutral'
    small=result(df.iloc[:49]);assert small['direction']=='unavailable' and not small['levels']
    monotonic=candles(trend=.004);monotonic[['open','high','low','close']]=np.repeat(np.arange(100)[:,None]*.001+1,4,axis=1)
    assert result(monotonic)['direction']=='unavailable'


def test_conflicting_horizons_and_context():
    assert result(candles(trend=.002))['direction']=='bullish'
    assert result(candles(trend=-.002),'weekly')['direction']=='bearish'
    assert resolve('bullish','bearish','bullish','neutral')=='mixed'
    assert resolve('bullish','bullish','bullish','mixed')=='mixed'
    assert resolve('bullish','bullish','bullish','bearish')=='mixed'
    assert resolve('unavailable','bullish','bullish','neutral')=='unavailable'
    a=result(candles());b=result(candles(),sentiment={'status':'available','reason':'Opposing book'})
    assert a['direction']==b['direction'] and a['components']==b['components']
    assert a['sentiment_context']['status']=='unavailable'


def test_no_future_bars_and_determinism():
    df=candles();clock=int(df.close_time.iloc[79])
    a=evaluate(df,'daily','EUR/USD','test',clock,{'status':'unavailable','reason':'none'})
    changed=df.copy();changed.iloc[80:,changed.columns.get_loc('close')]=9.
    assert a==evaluate(changed,'daily','EUR/USD','test',clock,{'status':'unavailable','reason':'none'})
    assert a==evaluate(df.iloc[:80],'daily','EUR/USD','test',clock,{'status':'unavailable','reason':'none'})


def test_contract_bias_references_and_chart_levels():
    r=analyze(demo('EUR/USD'),'EUR/USD','1h',10000,calendar='utc-weekdays-v1')
    evidence={e['id']:e for e in r['contract']['evidence']}
    findings={f['id']:f for f in r['contract']['findings']}
    for key in ['daily_bias','weekly_bias']:
        b=r[key]
        assert b['evidence_ids'] and all(e in evidence for e in b['evidence_ids'])
        assert all(evidence[e]['available_at']<=r['contract']['snapshot']['as_of'] for e in b['evidence_ids'])
        assert all(findings[f]['kind']=='bias_reference' for f in b['finding_ids'])
        assert any(a['kind']==key and a['calculation_version']==VERSION for a in r['contract']['assessments'])


def test_zone_confirmation_and_invalidation():
    df=candles();b=result(df)
    zones=b['components'][-1]['zones']
    assert zones and all(z['confirmed_at']<=b['as_of'] for z in zones)
    for z in zones:
        after=df[df.close_time>=z['confirmed_at']].close
        broken=(after>z['top']).any() if z['name']=='supply' else (after<z['bottom']).any()
        assert z['active']==(not bool(broken))
    # A new high on the last bar cannot replace the confirmed supply anchor.
    changed=df.copy();changed.iloc[-1,changed.columns.get_loc('high')]=10.
    again=result(changed)['components'][-1]['zones']
    assert next(z for z in again if z['name']=='supply')==next(z for z in zones if z['name']=='supply')
