from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from .analysis import analyze, demo, SYMBOLS

from .requests import AnalysisRequest
from .lifecycle import Event
from .contracts import AnalysisEnvelope, CanonicalCandle, INSTRUMENTS, SCHEMA_VERSION
from .adapters import ModuleFailure
from .contract_adapter import ContractBoundaryError

app=FastAPI(title='Combined analysis',version='0.3.0')
@app.get('/api/health')
def health():return {'status':'ok','mode':'local historical integration'}
@app.get('/api/demo')
def get_demo(symbol: str='EUR/USD'):
    if symbol not in SYMBOLS:raise HTTPException(422,'Unsupported symbol')
    return {'source':'synthetic demo — not market prices','candles':demo(symbol)}
@app.get('/api/contracts')
def contracts():
    return {'schema_version':SCHEMA_VERSION, 'instruments':[x.model_dump(mode='json') for x in INSTRUMENTS.values()],
            'candle':CanonicalCandle.model_json_schema(), 'analysis':AnalysisEnvelope.model_json_schema(),
            'request':AnalysisRequest.model_json_schema(),'historical_event':Event.model_json_schema()}

@app.post('/api/analyze')
def run(body: AnalysisRequest):
    from .sentiment import ArchiveProvider,archive_store
    try:selected=ArchiveProvider(archive_store(),body.archive_id).select(body.symbol,body.candles[(body.cutoff or len(body.candles))-1].time+3600) if body.archive_id else None
    except KeyError as exc:raise HTTPException(404,'Sentiment archive not found') from exc
    try:return analyze([c.legacy() for c in body.candles],body.symbol,body.interval,body.cutoff or len(body.candles),selected.snapshot if selected else body.snapshot.model_dump(exclude_none=True) if body.snapshot else None,body.data_source,sentiment_source_id=selected.source_id if selected else 'imported-oanda-book',selection_reason=selected.reason if selected else None)
    except ModuleFailure as exc:raise HTTPException(500,{'error':'module_failed','module':exc.module,'message':str(exc)}) from exc
    except ContractBoundaryError as exc:raise HTTPException(500,'Analysis adapter output failed contract validation') from exc
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

from .dataset_api import router
app.include_router(router)
from .sentiment import router as sentiment_router
app.include_router(sentiment_router)

from .replay_api import router as replay_router
app.include_router(replay_router)

from .order_api import router as order_router
app.include_router(order_router)

from .sessions import router as session_router
app.include_router(session_router)

static=Path(__file__).resolve().parents[1]/'frontend/dist'
if static.is_dir():app.mount('/',StaticFiles(directory=static,html=True),name='dashboard')
