"""Local history endpoints. Dataset IDs replace repeated whole-history requests."""
import csv
import os
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import Field
from starlette.concurrency import run_in_threadpool
from .datasets import DatasetStore, MAX_BYTES, MAX_ROWS, EventJournalError
from .lifecycle import VERSION as EVENT_VERSION
from .calendars import CalendarId, CALENDARS, aggregate_frame
from .contracts import Contract, Symbol, DataSource
from .requests import BookSnapshotInput
from .sentiment import ArchiveStore,ArchiveProvider
from .analysis import analyze, demo, frame
from .adapters import ModuleFailure
from .contract_adapter import ContractBoundaryError

router=APIRouter(prefix='/api/datasets')
def store():
    return DatasetStore(os.environ.get('CONFLUENCE_DATA_DIR',str(Path(__file__).resolve().parents[1]/'.data')))

def checked(fn,*args,**kwargs):
    try:return fn(*args,**kwargs)
    except EventJournalError as exc:raise HTTPException(500,{'error':'event_journal_conflict','message':'Saved historical events differ from replay; no history was overwritten.'}) from exc
    except KeyError as exc:raise HTTPException(404,'Dataset not found') from exc
    except ModuleFailure as exc:raise HTTPException(500,{'error':'module_failed','module':exc.module,'message':str(exc)}) from exc
    except ContractBoundaryError as exc:raise HTTPException(500,'Analysis adapter output failed contract validation') from exc
    except (ValueError,csv.Error) as exc:raise HTTPException(422,str(exc)) from exc

@router.get('/calendars')
def calendars():return CALENDARS

@router.get('')
def datasets(symbol:Symbol|None=None,limit:int=Query(100,ge=1,le=100),offset:int=Query(0,ge=0),db:DatasetStore=Depends(store)):
    return {'datasets':db.list(symbol,limit,offset),'limit':limit,'offset':offset}

@router.post('/demo')
def synthetic(symbol:Symbol='EUR/USD',db:DatasetStore=Depends(store)):
    return db.save(demo(symbol),symbol=symbol,base_timeframe='1h',calendar='utc-weekdays-v1',source_kind='synthetic',source_label='Synthetic demo — not market prices',volume_type='unknown')

@router.post('/import')
async def upload(request:Request,symbol:Symbol,base_timeframe:Literal['1m','1h'],calendar:CalendarId,input_timezone:str=Query('UTC',min_length=1,max_length=100),source_label:str=Query(...,min_length=1,max_length=200),timestamp_unit:Literal['seconds','milliseconds']='seconds',volume_type:Literal['unknown','tick_count','base_units','quote_units']='unknown',db:DatasetStore=Depends(store)):
    if not source_label.strip():raise HTTPException(422,'Source label cannot be blank')
    data=bytearray()
    async for chunk in request.stream():
        if len(data)+len(chunk)>MAX_BYTES:raise HTTPException(413,'CSV exceeds 32 MiB')
        data.extend(chunk)
    return await run_in_threadpool(checked,db.import_csv,bytes(data),symbol=symbol,base_timeframe=base_timeframe,calendar=calendar,input_timezone=input_timezone,source_label=source_label,timestamp_unit=timestamp_unit,volume_type=volume_type)

class DatasetAnalysisRequest(Contract):
    dataset_id:str=Field(pattern=r'^[a-f0-9]{64}$')
    interval:Literal['1h','4h','d1']='1h'
    cutoff:int=Field(strict=True,ge=1,le=MAX_ROWS)
    snapshot:BookSnapshotInput|None=None
    archive_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')

@router.post('/analyze')
def analysis(body:DatasetAnalysisRequest,db:DatasetStore=Depends(store)):
    meta,rows=checked(db.prefix,body.dataset_id,body.cutoff)
    if body.snapshot and body.snapshot.instrument!=meta['symbol'].replace('/','_'):raise HTTPException(422,'Book instrument differs from dataset')
    if body.snapshot and body.archive_id:raise HTTPException(422,'Choose snapshot or archive, not both')
    try:selected=ArchiveProvider(ArchiveStore(db.directory),body.archive_id).select(meta['symbol'],rows[-1]['time']+{'1h':3600,'1m':60}[meta['base_timeframe']]) if body.archive_id else None
    except KeyError as exc:raise HTTPException(404,'Sentiment archive not found') from exc
    source=DataSource(id=meta['id'],kind=meta['source_kind'],description=meta['source_label'],volume_type=meta['volume_type'])
    result=checked(analyze,rows,meta['symbol'],body.interval,len(rows),selected.snapshot if selected else body.snapshot.model_dump(exclude_none=True) if body.snapshot else None,source,meta['base_timeframe'],meta['calendar'],lambda events,clock:db.record_events(meta['id'],body.interval,EVENT_VERSION,events,clock),selected.source_id if selected else 'imported-oanda-book',selected.reason if selected else None)
    result['dataset_id']=meta['id']
    return result

@router.get('/{dataset_id}')
def metadata(dataset_id:str,db:DatasetStore=Depends(store)):return checked(db.get,dataset_id)

@router.get('/{dataset_id}/candles')
def candles(dataset_id:str,start:int|None=Query(None,ge=0,le=4102444800),end:int|None=Query(None,ge=0,le=4102444800),as_of:int|None=Query(None,ge=0,le=4102444800),limit:int=Query(1000,ge=1,le=10000),warmup:int=Query(0,ge=0,le=10000),db:DatasetStore=Depends(store)):
    return checked(db.range,dataset_id,start,end,as_of,limit,warmup)

@router.get('/{dataset_id}/aggregate')
def aggregated(dataset_id:str,interval:Literal['1m','5m','15m','1h','4h','d1','w1'],as_of:int=Query(...,ge=0,le=4102444800),start:int|None=Query(None,ge=0,le=4102444800),end:int|None=Query(None,ge=0,le=4102444800),limit:int=Query(1000,ge=1,le=10000),warmup:int=Query(0,ge=0,le=10000),db:DatasetStore=Depends(store)):
    # Complete source prefix before filtering target bars: range edges never create false partials.
    meta=checked(db.get,dataset_id)
    begin=meta['start'] if start is None else start;finish=meta['end'] if end is None else end
    if begin>=finish:raise HTTPException(422,'Range start must precede end')
    if as_of<=meta['start']:
        rows=[]
    else:rows=db.range(dataset_id,None,None,as_of,MAX_ROWS,0)['candles']
    import pandas as pd
    df=frame(rows,len(rows)) if rows else pd.DataFrame(columns=['open','high','low','close','volume'],index=pd.DatetimeIndex([],tz='UTC'))
    result=checked(aggregate_frame,df,interval,pd.Timestamp(as_of,unit='s',tz='UTC'),meta['base_timeframe'],meta['calendar'])
    records=[{'time':int(t.timestamp()),**{k:float(r[k]) if k!='close_time' else int(r[k]) for k in result.columns},'state':'completed'} for t,r in result.iterrows()]
    for r in records:
        if meta['volume_type']=='unknown':r['volume']=None
    prior=[r for r in records if r['time']<begin][-warmup:] if warmup else []
    visible=[r for r in records if begin<=r['time']<finish]
    return {'dataset_id':dataset_id,'calendar':meta['calendar'],'interval':interval,'as_of':as_of,'candles':visible[:limit],'warmup':prior,'warmup_requested':warmup,'warmup_returned':len(prior),'warmup_sufficient':len(prior)==warmup,'next_start':visible[limit]['time'] if len(visible)>limit else None,'truncated':len(visible)>limit,'aggregation':result.attrs['aggregation']}

@router.get('/{dataset_id}/events')
def event_history(dataset_id:str,interval:Literal['1h','4h','d1']='1h',as_of:int|None=Query(None,ge=0,le=4102444800),after:int=Query(-1,ge=-1),limit:int=Query(100,ge=1,le=1000),db:DatasetStore=Depends(store)):
    return checked(db.events,dataset_id,interval,EVENT_VERSION,as_of,after,limit)
