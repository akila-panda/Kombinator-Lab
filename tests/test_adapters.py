import copy
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.analysis import analyze, demo, frame
from backend import adapters
from backend.adapters import AnalysisContext, run
from backend.indicators import ema, atr, rsi, Indicators
from backend.contract_adapter import make_snapshot
from backend.vendor.fxdesk.zones import find_fvgs,find_obs
from backend.vendor.fxdesk.patterns import more_candles,sr_levels
from backend.vendor.struct.bos_engine import detect_bos
from backend.vendor.struct.choch_engine import detect_choch
from backend.vendor.struct.structure_engine import classify_structure
from backend.vendor.struct.zigzag_engine import detect_swings


def fixture(n=100):
    times=pd.date_range('2024-01-01',periods=n,freq='h',tz='UTC')
    return pd.DataFrame({'open':np.ones(n),'high':np.ones(n)*1.01,'low':np.ones(n)*.99,'close':np.ones(n),'volume':np.ones(n)},index=times)

def context(df):
    inputs=[{'time':int(t.timestamp()),**r.to_dict()} for t,r in df.iterrows()]
    snap=make_snapshot(inputs,None,'EUR/USD','1h',inputs[-1]['time']+3600)
    return AnalysisContext(snap,df,df.iloc[:0],Indicators.calculate(df))

def test_indicator_numeric_fixtures():
    s=pd.Series([1.,2.,3.,4.])
    assert ema(s,3).iloc[:2].isna().all()
    assert ema(s,3).iloc[2:].tolist()==[2.25,3.125]
    df=pd.DataFrame({'high':[11.,14.,13.,16.],'low':[9.,11.,10.,13.],'close':[10.,12.,11.,15.]})
    # TR [2,4,3,5], seed=3, recurrence=(3*2+5)/3.
    assert atr(df,3).iloc[:2].isna().all()
    assert atr(df,3).iloc[2:].tolist()==pytest.approx([3.,11/3])
    assert rsi(pd.Series([1.,2.,1.,3.,2.]),3).iloc[3:].tolist()==pytest.approx([75.,54.54545454545])

@pytest.mark.parametrize('fn',[ema,rsi])
@pytest.mark.parametrize('value',[float('nan'),float('inf')])
def test_missing_numeric_input_rejected(fn,value):
    with pytest.raises(ValueError,match='missing/nonfinite'):fn(pd.Series([1.,value,2.]),2)


def test_flat_and_warmup():
    df=fixture();i=Indicators.calculate(df)
    assert i.fast.iloc[:19].isna().all() and i.slow.iloc[:49].isna().all()
    assert i.rsi.iloc[:14].isna().all() and i.atr.iloc[:13].isna().all()
    assert i.rsi.iloc[-1]==50 and i.fast.iloc[-1]==i.slow.iloc[-1]==1
    out=adapters.scalper(context(df))
    assert out['alignment']['trend']=='NEUTRAL' and not out['alignment']['aligned']
    assert out['volatility']['level']=='normal'
    zero=df.copy();zero.high=zero.low=zero.close
    assert adapters.scalper(context(zero))['volatility']['level']=='flat'


def test_shared_snapshot_and_indicator_values():
    result=analyze(demo('EUR/USD'),'EUR/USD','1h',1000)
    sid=result['contract']['snapshot']['id']
    assert {r['snapshot_id'] for r in result['module_runs']}=={sid}
    assert {r['module'] for r in result['module_runs']}=={'indicators','struct','fxdesk','scalper','forexdashboard','integration','sentiment','lifecycle'}
    assert result['alignment']['ema_fast']==result['indicators']['ema20'][-1]['value']
    assert result['alignment']['ema_slow']==result['indicators']['ema50'][-1]['value']
    assert any(a['kind']=='volatility' for a in result['contract']['assessments'])

@pytest.mark.parametrize('module',['struct','fxdesk','scalper','forexdashboard'])
def test_failure_named_no_neutral_success(monkeypatch,module):
    def broken(ctx):raise RuntimeError('private failure detail')
    monkeypatch.setattr(adapters,module,broken)
    r=TestClient(app).post('/api/analyze',json={'candles':demo('EUR/USD')[:100]})
    assert r.status_code==500
    assert r.json()['detail']['module']==module and r.json()['detail']['error']=='module_failed'
    assert 'private failure' not in r.text and 'candles' not in r.json()


def test_malformed_module_result_is_failure():
    with pytest.raises(adapters.ModuleFailure,match='fxdesk'):
        run('fxdesk',context(fixture()),lambda c:{})


def test_upstream_adapters_preserve_input():
    ctx=context(frame(demo('EUR/USD')[:500],500));original=ctx.candles.copy(deep=True)
    for name,fn in [('struct',adapters.struct),('fxdesk',adapters.fxdesk),('scalper',adapters.scalper),('forexdashboard',adapters.forexdashboard)]:
        out=run(name,ctx,fn);assert out.snapshot_id==ctx.snapshot.id
        pd.testing.assert_frame_equal(ctx.candles,original)


def test_fvg_and_order_block_geometry_invalidation():
    df=fixture(70)
    df.iloc[65]=[1.0,1.01,.99,.995,1.]
    df.iloc[66]=[.995,1.06,.99,1.055,1.]
    df.iloc[67:]=[1.055,1.07,1.04,1.06,1.]
    i=Indicators.calculate(df)
    fvgs=find_fvgs(df,atr_values=i.atr);obs=find_obs(df,atr_values=i.atr)
    assert any(z['side']==1 and z['bottom']==1.01 and z['top']==1.04 for z in fvgs)
    assert any(z['side']==1 and z['bottom']==.99 and z['top']==1.01 for z in obs)
    df.iloc[-1]=[1.06,1.07,.97,.98,1.]
    assert not find_fvgs(df,atr_values=Indicators.calculate(df).atr)
    assert not find_obs(df,atr_values=Indicators.calculate(df).atr)


def test_patterns_and_support_fixture():
    df=fixture(80)
    # A three candle bullish run with sufficiently large bodies.
    df.iloc[-3:]=[[1.,1.04,.99,1.03,1.],[1.03,1.07,1.02,1.06,1.],[1.06,1.10,1.05,1.09,1.]]
    assert 'Three White Soldiers' in [p[0] for p in more_candles(df,float(atr(df).iloc[-1]))]
    wave=fixture(100);v=1+np.sin(np.arange(100)*np.pi/10)*.03
    wave['open']=wave['close']=v;wave['high']=v+.005;wave['low']=v-.005
    levels=sr_levels(wave,atr_value=float(atr(wave).iloc[-1]))
    assert any(abs(x['price']-1.035)<1e-8 and x['touches']>=2 for x in levels)
    assert any(abs(x['price']-.965)<1e-8 and x['touches']>=2 for x in levels)
    swings=detect_swings(wave.assign(time=wave.index.tz_localize(None)),fractal_n=3)
    assert swings and all(b['index']>a['index'] for a,b in zip(swings,swings[1:]))


def test_structure_labels_and_break_fixtures():
    swings=[{'kind':kind,'price':price,'index':i,'time':1704067200+i*3600} for i,(kind,price) in enumerate([('high',1.1),('low',.9),('high',1.2),('low',1.),('high',1.15),('low',.8)])]
    assert [x['label'] for x in classify_structure(swings)]==['HH','HL','LH','LL']
    df=fixture(30);df['time']=df.index.tz_localize(None)
    df.loc[df.index[20]:,'close']=1.2;df.loc[df.index[20]:,'high']=1.21
    labels=[{'label':'LH','price':1.1,'index':10}]
    bos=detect_bos(df,swings,labels,'bullish',fractal_n=3,atr_value=.02)
    choch=detect_choch(df,swings,labels,'bearish',fractal_n=3)
    assert len(bos)==len(choch)==1
    assert bos[0]['time']==choch[0]['time']==int(df.index[20].timestamp())
    assert bos[0]['direction']==choch[0]['direction']=='bullish'
    assert not detect_bos(df,swings,labels,'bearish',fractal_n=3,atr_value=.02)


def test_missing_schedule_observed_bar_policy():
    df=fixture();df=df.drop(df.index[50]);ctx=context(df)
    assert 'missing_scheduled_bars' in ctx.snapshot.quality_flags
    assert len(ctx.indicators.fast)==99 and ctx.indicators.rsi.iloc[-1]==50

@pytest.mark.parametrize('latest,level',[(2.,'high'),(.1,'low'),(1.,'normal')])
def test_selected_volatility_thresholds(latest,level):
    from dataclasses import replace
    ctx=context(fixture());a=ctx.indicators.atr.copy();a.iloc[-20:]=1.;a.iloc[-1]=latest
    ctx=replace(ctx,indicators=replace(ctx.indicators,atr=a))
    assert adapters.scalper(ctx)['volatility']['level']==level


def test_supply_demand_geometry_and_pivots():
    ctx=context(frame(demo('EUR/USD')[:500],500))
    result=adapters.struct(ctx)
    assert result['zones']
    for z in result['zones']:
        assert z['top']>=z['bottom']>0
        assert z['start_time']<=z['end_time']
        assert z['start_time'] in {int(t.timestamp()) for t in ctx.candles.index}
    from dataclasses import replace
    daily=fixture(1);daily.loc[daily.index[0],['high','low','close']]=[1.2,1.,1.1]
    p=adapters.forexdashboard(replace(ctx,daily=daily))['pivots']
    assert p['PP']==pytest.approx(1.1) and p['R1']==pytest.approx(1.2) and p['S1']==pytest.approx(1.)


def test_dataset_api_failure_identifies_module(tmp_path,monkeypatch):
    from backend.dataset_api import store
    from backend.datasets import DatasetStore
    db=DatasetStore(tmp_path);app.dependency_overrides[store]=lambda:db
    try:
        client=TestClient(app);meta=client.post('/api/datasets/demo').json()
        def broken(ctx):raise ValueError('detector failed internally')
        monkeypatch.setattr(adapters,'fxdesk',broken)
        r=client.post('/api/datasets/analyze',json={'dataset_id':meta['id'],'cutoff':100})
        assert r.status_code==500 and r.json()['detail']['module']=='fxdesk'
    finally:app.dependency_overrides.pop(store,None)


def test_shared_atr_is_injected_without_fallback(monkeypatch):
    import backend.vendor.fxdesk.zones as zones
    import backend.vendor.fxdesk.patterns as patterns
    import backend.vendor.struct.bos_engine as bos
    def forbidden(*args,**kwargs):raise AssertionError('Duplicate ATR computation')
    monkeypatch.setattr(zones,'atr',forbidden);monkeypatch.setattr(patterns,'atr',forbidden);monkeypatch.setattr(bos,'compute_atr14',forbidden)
    r=analyze(demo('EUR/USD'),'EUR/USD','1h',500)
    assert r['contract']['assessments']
