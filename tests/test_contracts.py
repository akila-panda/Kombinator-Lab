import copy
import math
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from backend.main import app
from backend.analysis import analyze, demo
from backend.contracts import (AnalysisEnvelope, Assessment, CanonicalCandle, Evidence,
    Finding, Instrument, INSTRUMENTS, MarketSnapshot, Overlay, SentimentObservation)
from backend.requests import AnalysisRequest

@pytest.fixture(scope='module')
def raw():return demo('EUR/USD')[:2000]

@pytest.fixture(scope='module')
def payload(raw):return analyze(raw,'EUR/USD','4h',len(raw))['contract']

def minute():
    return dict(id='m1',symbol='EUR/USD',timeframe='1m',source_id='test',open_time=1704067200,
                close_time=1704067260,observed_at=1704067260,state='completed',
                open=1.0,high=1.1,low=.9,close=1.01)

def test_minute_contract_supports_completed_and_forming():
    m=minute();assert CanonicalCandle(**m).volume is None
    m.update(state='forming',observed_at=m['open_time']+30)
    assert CanonicalCandle(**m).state=='forming'

@pytest.mark.parametrize('changes',[
    {'timeframe':'1h'}, {'open_time':1704067201}, {'close_time':1704067259},
    {'high':.8}, {'low':1.05}, {'close':float('nan')}, {'volume':float('inf')},
    {'observed_at':1704067199}, {'observed_at':1704067220},
    {'state':'forming'}, {'open_time':True}, {'close_time':'1704067260'},
    {'volume_type':'tick_count'}, {'unexpected':'ignored?'}])
def test_invalid_candles_fail(changes):
    with pytest.raises(ValidationError):CanonicalCandle(**(minute()|changes))

def test_instrument_rules():
    jpy=INSTRUMENTS['USD/JPY'];assert str(jpy.pip_size)=='0.01' and jpy.price_precision==3
    original=INSTRUMENTS['EUR/USD'].model_dump()
    for update in [{'quote_currency':'JPY'},{'tick_size':'.001'},{'pip_size':'.000015'}]:
        with pytest.raises(ValidationError):Instrument(**(original|update))

def test_envelope_from_four_modules(payload):
    model=AnalysisEnvelope.model_validate(payload)
    assert {a.module for a in model.assessments}>={'struct','fxdesk','scalper','forexdashboard'}
    assert model.snapshot.quality_flags
    assert all(c.volume is None for c in model.candles)
    assert any(f.status=='provisional' for f in model.findings)
    assert all(f.confirmed_at is None for f in model.findings if f.status=='provisional')
    assert any(o.kind=='zone' for o in model.overlays)
    assert AnalysisEnvelope.model_validate_json(model.model_dump_json())==model

@pytest.mark.parametrize('bad', ['instrument','symbol','evidence','duplicate','future','finding_clock','finding_context','candle_range','overlay'])
def test_invalid_envelope_references(payload,bad):
    p=copy.deepcopy(payload)
    if bad=='instrument':p['instrument']=INSTRUMENTS['GBP/USD'].model_dump(mode='json')
    if bad=='symbol':p['candles'][0]['symbol']='GBP/USD'
    if bad=='evidence':p['findings'][0]['evidence_ids']=['missing']
    if bad=='duplicate':p['candles'].append(p['candles'][0])
    if bad=='future':p['evidence'][0]['available_at']=p['snapshot']['as_of']+1
    if bad=='finding_clock':p['findings'][0]['occurred_at']=p['snapshot']['as_of']+1
    if bad=='finding_context':p['findings'][0]['snapshot_id']='another-snapshot'
    if bad=='candle_range':p['snapshot']['input_end']=p['candles'][-1]['open_time']
    if bad=='overlay':p['overlays'][0]['finding_id']='missing'
    with pytest.raises(ValidationError):AnalysisEnvelope.model_validate(p)

def test_finding_cannot_confirm_before_evidence(payload):
    p=copy.deepcopy(payload);f=p['findings'][0]
    f.update(status='confirmed',confirmed_at=f['occurred_at'])
    with pytest.raises(ValidationError):AnalysisEnvelope.model_validate(p)

def test_lifecycle_validation(payload):
    f=copy.deepcopy(payload['findings'][0])
    for patch in [{'evidence_ids':[]},{'confirmed_at':f['occurred_at']}, {'status':'invalidated'},
                  {'status':'confirmed','confirmed_at':f['occurred_at']-1}, {'expired_at':f['occurred_at']}]:
        with pytest.raises(ValidationError):Finding(**(f|patch))

def test_unavailable_is_not_zero_or_neutral():
    base=dict(module='scalper',kind='regime',source_version='zip:test',calculation_version='1',status='insufficient_history',explanation='Need 50 candles; supplied 20')
    assert Assessment(**base).metrics=={}
    for patch in [{'metrics':{'score':0.0}},{'direction':'neutral'},{'evidence_ids':['e:1']}]:
        with pytest.raises(ValidationError):Assessment(**(base|patch))
    with pytest.raises(ValidationError):Assessment(**(base|{'status':'available'}))

def test_geometry():
    with pytest.raises(ValidationError):Overlay(id='o',finding_id='f',kind='line',points=[{'time':10,'price':1.0}])
    with pytest.raises(ValidationError):Overlay(id='o',finding_id='f',kind='zone',zone={'start_time':1,'end_time':2,'top':1.0,'bottom':1.1})

def book(time='2024-01-03T23:00:00Z'):
    return {'instrument':'EUR_USD','positionBook':{'time':time,'buckets':[{'price':'1.08','shortCountPercent':'20','longCountPercent':'80'}]}}

@pytest.mark.parametrize('mutation',['symbol','timeframe','minute','forming','bool','book_symbol','naive','percentage','empty','false_provenance','missing_volume'])
def test_request_rejects_ambiguous_inputs(raw,mutation):
    body={'candles':copy.deepcopy(raw[:100])}
    if mutation=='symbol':body['candles'][0]['symbol']='GBP/USD'
    if mutation=='timeframe':body['candles'][0]['timeframe']='4h'
    if mutation=='minute':body['base_timeframe']='1m'
    if mutation=='forming':body['candles'][0]['state']='forming'
    if mutation=='bool':body['candles'][0]['time']=True
    if mutation in ('book_symbol','naive','percentage','empty'):
        body['snapshot']=book()
        if mutation=='book_symbol':body['snapshot']['instrument']='GBP_USD'
        if mutation=='naive':body['snapshot']['positionBook']['time']='2024-01-03T23:00:00'
        if mutation=='percentage':body['snapshot']['positionBook']['buckets'][0]['longCountPercent']='101'
        if mutation=='empty':body['snapshot']['positionBook']['buckets']=[]
    if mutation in ('false_provenance','missing_volume'):
        body['data_source']={'id':'upload','kind':'user_upload','description':'CSV'}
        if mutation=='false_provenance':body['data_source']['provenance_verified']=True
        else:
            body['data_source']['volume_type']='tick_count'
            del body['candles'][0]['volume']
    with pytest.raises(ValidationError):AnalysisRequest.model_validate(body)

def test_explicit_offset_is_normalized(raw):
    body=AnalysisRequest(candles=raw[:100],snapshot=book('2024-01-04T04:30:00+05:30'))
    assert body.snapshot.positionBook.time=='2024-01-03T23:00:00+00:00'

def test_api_compatibility_and_schema(raw):
    client=TestClient(app)
    info=client.get('/api/contracts').json()
    assert info['schema_version']=='1.4.0' and len(info['instruments'])==3
    assert '1m' in info['candle']['properties']['timeframe']['enum']
    response=client.post('/api/analyze',json={'candles':raw[:100]})
    assert response.status_code==200,response.text
    result=response.json()
    assert {'candles','findings','indicators','contract'}<=result.keys()
    assert AnalysisEnvelope.model_validate(result['contract'])

def test_sentiment_actual_adapter_with_retrieval_boundary(raw):
    candles=raw[:100];asof=candles[-1]['time']+3600
    from datetime import datetime, timezone
    iso=lambda seconds:datetime.fromtimestamp(seconds,timezone.utc).isoformat()
    snapshot=book(iso(asof-3600))
    snapshot['positionBook']['retrieved_at']=iso(asof-1800)
    good=analyze(candles,'EUR/USD','1h',100,snapshot)['contract']
    assert good['sentiment']['status']=='available'
    observation=good['sentiment']['observations'][0]
    assert observation['availability_basis']=='retrieval_time'
    assert observation['score']<0
    snapshot['positionBook']['retrieved_at']=iso(asof+1)
    rejected=analyze(candles,'EUR/USD','1h',100,snapshot)['contract']
    assert rejected['sentiment']['status']=='unavailable'
    assert rejected['sentiment']['observations'][0]['score'] is None

def test_internal_bad_adapter_is_not_a_client_error(raw,monkeypatch):
    import backend.analysis as engine
    def invalid(*args,**kwargs):raise ValueError('missing evidence')
    monkeypatch.setattr(engine,'envelope',invalid)
    response=TestClient(app).post('/api/analyze',json={'candles':raw[:100]})
    assert response.status_code==500
    assert response.json()['detail']=='Analysis adapter output failed contract validation'

def test_published_schema_examples_match_models():
    from pathlib import Path
    import json
    root=Path(__file__).resolve().parents[1]/'docs/contracts'
    for file,model in [('analysis-envelope.schema.json',AnalysisEnvelope),('candle.schema.json',CanonicalCandle),('analysis-request.schema.json',AnalysisRequest)]:
        assert json.loads((root/file).read_text())==model.model_json_schema()
    examples=json.loads((root/'examples.json').read_text())
    assert CanonicalCandle.model_validate(examples['completed_minute'])
    assert CanonicalCandle.model_validate(examples['forming_minute'])
    envelope=AnalysisEnvelope.model_validate(examples['analysis_envelope'])
    assert envelope.sentiment.status=='available'
    assert len(envelope.sentiment.observations)==2

def test_available_sentiment_cannot_reference_unrelated_evidence():
    from pathlib import Path
    import json
    p=json.loads((Path(__file__).resolve().parents[1]/'docs/contracts/examples.json').read_text())['analysis_envelope']
    p['sentiment']['observations'][0]['evidence_ids']=[p['evidence'][0]['id']]
    with pytest.raises(ValidationError):AnalysisEnvelope.model_validate(p)

def test_book_price_boolean_rejected(raw):
    snapshot=book();snapshot['positionBook']['price']=True
    with pytest.raises(ValidationError):AnalysisRequest(candles=raw[:100],snapshot=snapshot)

def test_last_accepted_open_leaves_room_for_candle_close(raw):
    body={'candles':copy.deepcopy(raw[:100])}
    body['candles'][-1]['time']=4102444800
    assert TestClient(app).post('/api/analyze',json=body).status_code==422

def test_equivalent_numeric_inputs_share_snapshot_id(raw):
    original=raw[:100]
    parsed=[c.legacy() for c in AnalysisRequest(candles=original).candles]
    a=analyze(original,'EUR/USD','1h',100)['contract']['snapshot']['id']
    b=analyze(parsed,'EUR/USD','1h',100)['contract']['snapshot']['id']
    assert a==b
