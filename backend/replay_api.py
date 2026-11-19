"""Stateless deterministic minute replay. Wall time never advances the server clock."""
from functools import lru_cache
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from typing import Literal
from .contracts import Contract, DataSource
from .datasets import DatasetStore, MAX_ROWS
from .dataset_api import store, checked
from .calendars import aggregate_frame, bar_bounds, expected_slots, is_open
from .analysis import frame, analyze

router=APIRouter(prefix='/api/replay')

class ReplayRequest(Contract):
    dataset_id:str=Field(pattern=r'^[a-f0-9]{64}$')
    clock:int=Field(strict=True,ge=0,le=4102444800)
    action:Literal['seek','minute','candle']='seek'
    timeframe:Literal['15m','1h']='15m'

@lru_cache(maxsize=16)
def completed_analysis(directory,did,close):
    db=DatasetStore(directory);meta=db.get(did)
    rows=db.range(did,None,None,close,MAX_ROWS,0)['candles']
    source=DataSource(id=did,kind=meta['source_kind'],description=meta['source_label'],volume_type=meta['volume_type'])
    return analyze(rows,meta['symbol'],'1h',len(rows),data_source=source,base_timeframe='1m',calendar=meta['calendar'])


def replay_state(db,body):
    meta=db.get(body.dataset_id)
    if meta['base_timeframe']!='1m':raise ValueError('Replay requires a minute dataset; select/import minute history')
    if body.clock%60:raise ValueError('Clock must be aligned to a UTC minute')
    if not meta['start']<=body.clock<=meta['end']:raise ValueError('Requested date is outside this dataset coverage')
    clock=body.clock
    if body.action=='minute':
        with db.connection() as conn:
            row=conn.execute('SELECT MIN(time+60) FROM candles WHERE dataset_id=? AND time+60>?',(meta['id'],clock)).fetchone()
        clock=int(row[0]) if row[0] is not None else meta['end']
    elif body.action=='candle':
        clock=min(bar_bounds(clock,body.timeframe,meta['calendar'])[1],meta['end'])
    rows=db.range(meta['id'],None,None,clock,MAX_ROWS,0)['candles']
    with db.connection() as conn:
        next_row=conn.execute('SELECT MIN(time+60) FROM candles WHERE dataset_id=? AND time+60>?',(meta['id'],clock)).fetchone()
    next_close=next_row[0]
    df=frame(rows,len(rows)) if rows else pd.DataFrame(columns=['open','high','low','close','volume'],index=pd.DatetimeIndex([],tz='UTC'))
    views={};hourly=None
    for tf in ('15m','1h'):
        complete=aggregate_frame(df,tf,pd.Timestamp(clock,unit='s',tz='UTC'),'1m',meta['calendar'])
        if tf=='1h':hourly=complete
        bars=[dict(time=int(t.timestamp()),**{k:float(r[k]) for k in ('open','high','low','close')},state='completed') for t,r in complete.iloc[-400:].iterrows()]
        start,end=bar_bounds(clock,tf,meta['calendar'])
        visible=[r for r in rows if start<=r['time']<end]
        forming=None
        if visible:
            expected=expected_slots(start,min(clock,end),60,meta['calendar'])
            forming=dict(time=start,open=visible[0]['open'],high=max(r['high'] for r in visible),low=min(r['low'] for r in visible),close=visible[-1]['close'],state='forming' if len(visible)==expected else 'forming_with_gaps',revealed_minutes=len(visible),expected_minutes=expected,closes_at=end)
        views[tf]={'clock':clock,'completed':bars,'forming':forming,'excluded':complete.attrs['aggregation']['excluded_groups']}
    analysis=None
    if len(hourly)>=60:
        analysis=completed_analysis(str(db.directory.resolve()),meta['id'],int(hourly.close_time.iloc[-1]))
    return {'dataset_id':meta['id'],'symbol':meta['symbol'],'clock':clock,'previous_clock':body.clock,'advanced_seconds':clock-body.clock,
            'coverage':{'start':meta['start'],'end':meta['end'],'calendar':meta['calendar'],'quality':meta['quality']},
            'state':'ended' if clock>=meta['end'] else 'closed_market' if not is_open(clock,meta['calendar']) else 'data_gap' if next_close and next_close>clock+60 else 'ready',
            'next_minute_close':next_close,'revealed_minutes':len(rows),'views':views,
            'analysis':analysis,'analysis_status':'available' if analysis else 'insufficient_history',
            'warmup':{'required_complete_hours':60,'available_complete_hours':len(hourly)},
            'notice':'Minute-close playback only. No tick path, spread or fills. Missing minutes are not fabricated; incomplete candles are excluded from signals.'}

@router.post('/state')
def state(body:ReplayRequest,db:DatasetStore=Depends(store)):
    return checked(replay_state,db,body)
