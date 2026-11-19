"""Explicit aggregation calendars; no holiday or provider maintenance assumptions."""
from datetime import datetime, timedelta, timezone, time
from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo
import pandas as pd

CalendarId = Literal['fixed-utc-v1','utc-weekdays-v1','fx-ny-17-v1']
SECONDS={'1m':60,'5m':300,'15m':900,'1h':3600,'4h':14400,'d1':86400,'w1':604800}
UTC=timezone.utc
NY=ZoneInfo('America/New_York')
CALENDARS={
 'fixed-utc-v1':{'timezone':'UTC','daily_open_hour':0,'week':'Monday–Monday','closures':'none'},
 'utc-weekdays-v1':{'timezone':'UTC','daily_open_hour':0,'week':'Monday–Saturday','closures':'Saturday/Sunday; intended for synthetic fixtures'},
 'fx-ny-17-v1':{'timezone':'America/New_York','daily_open_hour':17,'week':'Sunday 17:00–Friday 17:00 local','closures':'weekend only; holidays/maintenance not modelled'},
}

def is_open(timestamp,calendar):
    if calendar=='fixed-utc-v1':return True
    if calendar=='utc-weekdays-v1':return datetime.fromtimestamp(timestamp,UTC).weekday()<5
    if calendar!='fx-ny-17-v1':raise ValueError('Unknown calendar')
    d=datetime.fromtimestamp(timestamp,NY);w=d.weekday()
    return w<4 or (w==4 and d.hour<17) or (w==6 and d.hour>=17)

@lru_cache(maxsize=32768)
def _bounds(hour,tf,calendar):
    step=SECONDS[tf]
    if calendar not in CALENDARS:raise ValueError('Unknown calendar')
    if tf not in ('d1','w1','4h') or calendar!='fx-ny-17-v1':
        origin=345600 if tf=='w1' else 0
        start=(hour-origin)//step*step+origin
        end=start+step
        if tf=='w1' and calendar=='utc-weekdays-v1':end=start+5*86400
        return start,end
    local=datetime.fromtimestamp(hour,NY)
    if tf=='w1':
        date=local.date()-timedelta(days=(local.weekday()+1)%7)
        start_dt=datetime.combine(date,time(17),NY)
        if local<start_dt:start_dt-=timedelta(days=7)
        return int(start_dt.timestamp()),int((start_dt+timedelta(days=5)).timestamp())
    date=local.date() if local.hour>=17 else local.date()-timedelta(days=1)
    anchor=datetime.combine(date,time(17),NY)
    if tf=='d1':return int(anchor.timestamp()),int((anchor+timedelta(days=1)).timestamp())
    start=int(anchor.timestamp())+(hour-int(anchor.timestamp()))//step*step
    return start,start+step

def bar_bounds(timestamp,tf,calendar='fixed-utc-v1'):
    # Grouping at hourly resolution shares cached daily/session calculations across minute bars.
    return _bounds(timestamp//3600*3600 if SECONDS[tf]>=3600 else timestamp,tf,calendar)

def expected_slots(start,end,step,calendar):
    """Count scheduled base slots in [start,end), without expanding long minute gaps."""
    if end<=start:return 0
    def count(a,b):return max(0,(b+step-1)//step-(a+step-1)//step)
    if calendar=='fixed-utc-v1':return count(start,end)
    zone=NY if calendar=='fx-ny-17-v1' else UTC
    first=datetime.fromtimestamp(start,zone).date()-timedelta(days=1)
    last=datetime.fromtimestamp(end,zone).date()
    total=0
    while first<=last:
        weekday=first.weekday()
        active=weekday in (6,0,1,2,3) if calendar=='fx-ny-17-v1' else weekday<5
        if active:
            a=datetime.combine(first,time(17 if calendar=='fx-ny-17-v1' else 0),zone)
            b=a+timedelta(days=1)
            total+=count(max(start,int(a.timestamp())),min(end,int(b.timestamp())))
        first+=timedelta(days=1)
    return total

def quality_report(rows,base_timeframe,calendar):
    step=SECONDS[base_timeframe];missing=closed=0;gaps=[];closures=[]
    for a,b in zip(rows,rows[1:]):
        start=a['time']+step;end=b['time']
        if end<=start:continue
        expected=expected_slots(start,end,step,calendar)
        missing+=expected;scheduled=(end-start)//step-expected;closed+=scheduled
        if expected and len(gaps)<100:gaps.append({'from':start,'to':end,'missing_bars':expected})
        if scheduled and len(closures)<100:closures.append({'from':start,'to':end,'closed_slots':scheduled})
    return {'missing_bars':missing,'scheduled_closed_slots':closed,'missing_intervals':gaps,'closure_intervals':closures,'interval_details_limit':100,'edge_coverage':'Only internal gaps are assessed; no coverage outside first/last rows is assumed.'}

def aggregate_frame(df,interval,asof,base_timeframe='1h',calendar='fixed-utc-v1'):
    step=SECONDS[base_timeframe]
    if SECONDS[interval]<step:raise ValueError('Requested timeframe is finer than dataset granularity')
    end_clock=int(pd.Timestamp(asof).timestamp())
    groups={}
    for i,t in enumerate(df.index):
        ts=int(t.timestamp())
        if ts+step>end_clock:continue
        if not is_open(ts,calendar):raise ValueError('Input contains candles outside the declared calendar')
        start,end=bar_bounds(ts,interval,calendar)
        groups.setdefault((start,end),[]).append(i)
    excluded={'unfinished':0,'missing_input':0}
    # Aggregate all buckets together; avoid one DataFrame allocation per minute/hour.
    keys={i:(start,end) for (start,end),indices in groups.items() for i in indices}
    if keys:
        selected=df.iloc[list(keys)].copy()
        selected['_start']=[keys[i][0] for i in keys]
        selected['_end']=[keys[i][1] for i in keys]
        grouped=selected.groupby('_start',sort=True)
        result=grouped.agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),volume=('volume','sum'),close_time=('_end','first'),count=('close','count'))
        expected=[expected_slots(int(start),int(end),step,calendar) for start,end in zip(result.index,result.close_time)]
        complete=result.close_time<=end_clock
        populated=(result['count'].to_numpy()==expected)&(result['count']>0)
        excluded['unfinished']=int((~complete).sum())
        excluded['missing_input']=int((complete&~populated).sum())
        result=result[complete&populated].drop(columns='count')
        result.index=pd.to_datetime(result.index,unit='s',utc=True)
        result.index.name=None
    else:
        result=pd.DataFrame(columns=['open','high','low','close','volume','close_time'],index=pd.DatetimeIndex([],tz='UTC'))
    result.attrs['aggregation']={'calendar':calendar,'base_timeframe':base_timeframe,'interval':interval,'excluded_groups':excluded,'as_of':end_clock}
    return result
