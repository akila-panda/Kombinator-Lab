import copy
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.analysis import demo, analyze, aggregate, frame, sentiment, divergences
from backend.vendor.fxdesk.indicators import rsi

@pytest.fixture(scope='module')
def candles():return demo('EUR/USD')

@pytest.mark.parametrize('interval',['1h','4h','d1'])
def test_all_modules_share_one_response(candles,interval):
    r=analyze(candles,'EUR/USD',interval,len(candles))
    assert len(r['modules'])==4
    assert len(r['candles'])>=60
    assert r['alignment']['ema_fast']>0
    assert r['pivots']['R1']>r['pivots']['S1']
    assert r['sentiment']['status']=='unavailable'
    assert r['indicators']['rsi']
    assert r['findings']

def test_replay_excludes_future_candles(candles):
    cutoff=3000
    a=analyze(candles,'EUR/USD','4h',cutoff)
    b=analyze(candles[:cutoff],'EUR/USD','4h',cutoff)
    altered=copy.deepcopy(candles)
    for c in altered[cutoff:]:
        for key in ['open','high','low','close']:c[key]*=3
    assert a==b==analyze(altered,'EUR/USD','4h',cutoff)

@pytest.mark.parametrize('values,expected',[(np.arange(1.,41.),100.),(np.arange(40.,0.,-1),0.),(np.ones(40),50.)])
def test_rsi_boundaries(values,expected):
    assert rsi(pd.Series(values)).iloc[-1]==expected

def test_rsi_warmup():assert rsi(pd.Series(np.arange(1.,11.))).isna().all()

def test_no_partial_or_missing_aggregate():
    candles=[{'time':1704067200+3600*i,'open':1.,'high':1.1,'low':.9,'close':1.,'volume':1} for i in range(7)]
    df=frame(candles,len(candles));asof=df.index[-1]+pd.Timedelta(hours=1)
    assert len(aggregate(df,'4h',asof))==1
    assert aggregate(df.drop(df.index[1]),'4h',asof).empty

def snapshot(time):
    return {'instrument':'EUR_USD','positionBook':{'time':time,'retrieved_at':time,'buckets':[{'price':'1.08','longCountPercent':'80','shortCountPercent':'20'}]},'orderBook':{'time':time,'retrieved_at':time,'price':'1.08','buckets':[{'price':'1.08','longCountPercent':'60','shortCountPercent':'40'}]}}

def test_forexdashboard_scoring():
    now=pd.Timestamp('2025-01-02T00:00:00Z');r=sentiment(snapshot('2025-01-01T23:00:00Z'),'EUR/USD',now)
    assert r['status']=='available'
    assert r['parts']['positionBook']['score']==pytest.approx(-.15/.35)
    assert r['parts']['orderBook']['score']==pytest.approx(.2)

@pytest.mark.parametrize('time',['2025-01-02T01:00:00Z','2024-12-30T00:00:00Z'])
def test_sentiment_cannot_leak_future_or_stale_snapshot(time):
    assert sentiment(snapshot(time),'EUR/USD',pd.Timestamp('2025-01-02T00:00:00Z'))['status']=='unavailable'

def test_book_wrong_instrument():
    assert sentiment(snapshot('2025-01-01T23:00:00Z'),'GBP/USD',pd.Timestamp('2025-01-02T00:00:00Z'))['status']=='unavailable'

def test_divergence_requires_right_hand_confirmation():
    low=np.array([11.,10.,9.,10.,11.,10.,8.,9.,10.,11.])
    df=pd.DataFrame({'low':low,'high':low+2},index=pd.date_range('2025-01-01',periods=10,freq='h',tz='UTC'))
    values=pd.Series([50.,40.,20.,40.,50.,40.,30.,40.,50.,60.],index=df.index)
    result=divergences(df,values,n=1)
    assert any(x['direction']=='bullish' and x['time']==int(df.index[6].timestamp()) for x in result)
    assert not divergences(df.iloc[:7],values.iloc[:7],n=1)
    event=next(x for x in result if x['direction']=='bullish')
    assert event['confirmed_at']==int((df.index[7]+pd.Timedelta(hours=1)).timestamp())

def test_http_round_trip_and_input_validation(candles):
    client=TestClient(app)
    assert client.get('/api/health').status_code==200
    body={'candles':candles[:200],'symbol':'EUR/USD','interval':'1h'}
    response=client.post('/api/analyze',json=body)
    assert response.status_code==200,response.text
    assert response.json()['modules'][2]['state']=='connected'
    body['candles']=candles[:100]+candles[:100]
    assert client.post('/api/analyze',json=body).status_code==422
    body['candles']=copy.deepcopy(candles[:100]);body['candles'][0]['high']=.001
    assert client.post('/api/analyze',json=body).status_code==422

def test_invalid_snapshot_returns_validation_error(candles):
    client=TestClient(app)
    body={'candles':candles[:200],'snapshot':{'positionBook':{'time':'wrong','buckets':[]}}}
    assert client.post('/api/analyze',json=body).status_code==422
