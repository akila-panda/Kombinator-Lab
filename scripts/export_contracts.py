"""Export P02 schemas and synthetic, validated examples; no external data access."""
from pathlib import Path
import json
import sys
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.contracts import AnalysisEnvelope, CanonicalCandle, DataSource, INSTRUMENTS
from backend.requests import AnalysisRequest
from backend.dataset_api import DatasetAnalysisRequest
from backend.lifecycle import Event
from backend.sentiment import ArchiveInput
from backend.analysis import analyze, demo


def export():
    out=Path(__file__).resolve().parents[1]/'docs/contracts'
    out.mkdir(exist_ok=True)
    def save(name,value): (out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    for filename,model in [('analysis-envelope.schema.json',AnalysisEnvelope),('candle.schema.json',CanonicalCandle),('analysis-request.schema.json',AnalysisRequest),('dataset-analysis-request.schema.json',DatasetAnalysisRequest),('historical-event.schema.json',Event),('sentiment-archive.schema.json',ArchiveInput)]:
        save(filename,model.model_json_schema())
    save('instruments.json',[x.model_dump(mode='json') for x in INSTRUMENTS.values()])
    candles=demo('EUR/USD')[:60]
    time=datetime.fromtimestamp(candles[-1]['time'],timezone.utc).isoformat()
    book={'time':time,'retrieved_at':time,'price':'1.08','buckets':[{'price':'1.08','longCountPercent':'80','shortCountPercent':'20'}]}
    request=AnalysisRequest(candles=candles,snapshot={'instrument':'EUR_USD','positionBook':book,'orderBook':book},data_source=DataSource(id='schema-example',kind='synthetic',description='Invented price and book data for contract examples; not market observations'))
    result=analyze([c.legacy() for c in request.candles],request.symbol,request.interval,60,request.snapshot.model_dump(exclude_none=True),request.data_source)['contract']
    minute=CanonicalCandle(id='example-minute',symbol='EUR/USD',timeframe='1m',source_id='schema-example',open_time=1704067200,close_time=1704067260,observed_at=1704067260,state='completed',open=1.08,high=1.081,low=1.079,close=1.0805,quality_flags=['synthetic','volume_unknown'])
    forming=CanonicalCandle.model_validate(minute.model_dump()|{'id':'example-forming','state':'forming','observed_at':1704067230})
    save('examples.json',{'notice':'Entirely synthetic schema examples. Completed minute/hour CSV datasets are supported in P03; forming candles remain contract-only.','completed_minute':minute.model_dump(mode='json'),'forming_minute':forming.model_dump(mode='json'),'analysis_envelope':result})
    print('Exported schemas, instrument registry and validated synthetic examples.')

if __name__=='__main__':export()
