"""Single orchestration layer over selected components from all four projects."""
from __future__ import annotations
import math
from .calendars import aggregate_frame, SECONDS
import numpy as np
import pandas as pd
from .contract_adapter import envelope, ContractBoundaryError
from . import adapters
from .bias import evaluate as evaluate_bias
from .lifecycle import replay, summary, VERSION as EVENT_VERSION
from .adapters import AnalysisContext, run
from .indicators import Indicators, ema
from .contract_adapter import make_snapshot
from .vendor.fxdesk.indicators import pivot_idx
from .vendor.forexdashboard import SnapshotStrategy

INTERVALS = {'1h': ('1h',3600), '4h': ('4h',14400), 'd1': ('1D',86400)}
SYMBOLS = {'EUR/USD':1.08,'GBP/USD':1.27,'USD/JPY':150.0}

def clean(value):
    if isinstance(value, dict): return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [clean(x) for x in value]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (float,np.floating)): return float(value) if math.isfinite(value) else None
    if isinstance(value, np.bool_): return bool(value)
    return value

def demo(symbol):
    rng=np.random.default_rng(42)
    times=pd.date_range('2024-01-01',periods=15000,freq='h',tz='UTC')
    times=times[times.dayofweek<5][:10000]
    base=SYMBOLS[symbol]; n=len(times)
    changes=rng.normal(0,0.00027,n)+0.00008*np.sin(np.arange(n)/70)
    closes=base*np.exp(np.cumsum(changes)); opens=np.r_[base,closes[:-1]]
    wick=base*rng.uniform(.00005,.0004,n)
    return [{'time':int(t.timestamp()),'open':float(o),'high':float(max(o,c)+w),'low':float(min(o,c)-w),'close':float(c),'volume':int(v)} for t,o,c,w,v in zip(times,opens,closes,wick,rng.integers(20,500,n))]

def frame(candles, cutoff):
    df=pd.DataFrame(candles[:cutoff])
    df.index=pd.to_datetime(df.pop('time'),unit='s',utc=True)
    return df

def aggregate(df, interval, asof):
    rule,seconds=INTERVALS[interval]
    if interval=='1h': return df.copy()
    groups=df.resample(rule,closed='left',label='left')
    result=groups.agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'})
    counts=groups['close'].count()
    # A complete group needs each hourly candle, and must have closed by replay time.
    return result[(counts==seconds//3600)&(result.index+pd.Timedelta(seconds=seconds)<=asof)].dropna()

class BookReader:
    def __init__(self,snapshot): self.snapshot=snapshot
    def fetch_positionbook(self,instrument): return self.snapshot.get('positionBook')
    def fetch_orderbook(self,instrument): return self.snapshot.get('orderBook')
    def parse_buckets(self,buckets):
        return ([float(b['price']) for b in buckets],[float(b['shortCountPercent']) for b in buckets],[float(b['longCountPercent']) for b in buckets])
    def filter_buckets_by_pips(self,prices,shorts,longs,current,instrument,pip_range):
        pip=.01 if instrument.endswith('JPY') else .0001
        rows=[r for r in zip(prices,shorts,longs) if abs(r[0]-current)<=pip_range*pip]
        return tuple(map(list,zip(*rows))) if rows else ([],[],[])
    def get_display_precision(self,instrument): return 3 if instrument.endswith('JPY') else 5
    def fetch_current_price(self,instrument): return None

def sentiment(snapshot, symbol, asof,source_id="imported-oanda-book"):
    from .sentiment import FRESHNESS, VERSION
    from .requests import BookSnapshotInput
    unavailable={'status':'unavailable','source_id':source_id,'calculation_version':VERSION,'source':'ForexDashboard / imported OANDA book','reason':'Import a dated OANDA book snapshot to calculate positioning sentiment.'}
    if not snapshot:return unavailable
    snapshot=BookSnapshotInput.model_validate(snapshot).model_dump(exclude_none=True)
    if snapshot.get('instrument')!=symbol.replace('/','_'):return {**unavailable,'reason':'Book instrument does not match selected pair.'}
    engine=SnapshotStrategy(BookReader(snapshot)); parts={}
    for name,method in [('positionBook',engine.analyze_positionbook),('orderBook',lambda s:engine.analyze_orderbook(s,50))]:
        book=snapshot.get(name)
        if not book: continue
        observed=pd.Timestamp(book['time'])
        if observed.tzinfo is None: observed=observed.tz_localize('UTC')
        age=(asof-observed).total_seconds()
        retrieved=pd.Timestamp(book['retrieved_at']) if book.get('retrieved_at') else None
        if retrieved is not None and retrieved.tzinfo is None:retrieved=retrieved.tz_localize('UTC')
        if age<0 or age>FRESHNESS[name] or retrieved is None or retrieved>asof:
            parts[name]={'status':'unavailable','reason':'Book requires an explicit retrieval time at or before replay, observation at or before replay, and age at most 24 hours.'};continue
        book=dict(book)
        if 'price' in book: book['price']=float(book['price'])
        engine.oanda_handler.snapshot[name]=book
        score,details=method(symbol.replace('/','_'))
        parts[name]={'score':score if details['status']=='success' else None,'status':details['status'],'observed_at':observed.isoformat(),'age_seconds':age,'reason':details.get('error'),'long_ratio':details.get('long_ratio')}
    valid=[p['score'] for p in parts.values() if p.get('score') is not None]
    return {'status':'available' if valid else 'unavailable','source':'User-imported OANDA-format book; provenance not independently verified','source_id':source_id,'calculation_version':VERSION,'parts':parts,'reason':'Position book uses the upstream contrarian rule; order book uses net orders within 50 pips. These are separate heuristics.'}

def divergences(df, values, n=3, bar_seconds=3600):
    # New integration detector: chronological confirmed pivots, never sorted by price.
    events=[]
    for field,mode,direction in [('low','min','bullish'),('high','max','bearish')]:
        indices=pivot_idx(df[field].to_numpy(),n,mode)
        for a,b in zip(indices,indices[1:]):
            if b-a<4 or b-a>80 or not np.isfinite(values.iloc[a]) or not np.isfinite(values.iloc[b]):continue
            found=(df[field].iloc[b]<df[field].iloc[a] and values.iloc[b]>values.iloc[a]) if direction=='bullish' else (df[field].iloc[b]>df[field].iloc[a] and values.iloc[b]<values.iloc[a])
            if found:
                events.append({'direction':direction,'time':int(df.index[b].timestamp()),'confirmed_at':int((df.index[b+n]+pd.Timedelta(seconds=bar_seconds)).timestamp()),'price':float(df[field].iloc[b]),'prior_time':int(df.index[a].timestamp()),'prior_price':float(df[field].iloc[a]),'rsi_from':float(values.iloc[a]),'rsi_to':float(values.iloc[b])})
    return sorted(events,key=lambda x:x['time'])[-12:]

def analyze(candles,symbol,interval,cutoff,snapshot=None,data_source=None,base_timeframe="1h",calendar="fixed-utc-v1",event_sink=None,sentiment_source_id="imported-oanda-book",selection_reason=None):
    base=frame(candles,cutoff); asof=base.index[-1]+pd.Timedelta(seconds=SECONDS[base_timeframe])
    df=aggregate_frame(base,interval,asof,base_timeframe,calendar)
    aggregation=df.attrs["aggregation"]
    if len(df)<60: raise ValueError('At least 60 complete candles are required for the selected timeframe.')
    # Bound detectors to the visible analysis history; every module receives the same prefix.
    history=df
    df=df.iloc[-500:]; seconds=INTERVALS[interval][1]
    market=make_snapshot(candles[:cutoff],data_source,symbol,interval,int(asof.timestamp()),base_timeframe,calendar)
    indicator_run=run('indicators',AnalysisContext(market,df,pd.DataFrame(),None),lambda ctx:{'bundle':Indicators.calculate(ctx.candles)})
    indicators=indicator_run.payload['bundle']
    daily=aggregate_frame(base,'d1',asof,base_timeframe,calendar)
    weekly=aggregate_frame(base,'w1',asof,base_timeframe,calendar)
    ctx=AnalysisContext(market,df,daily,indicators)
    outputs=[run(name,ctx,fn) for name,fn in [('struct',adapters.struct),('fxdesk',adapters.fxdesk),('scalper',adapters.scalper),('forexdashboard',adapters.forexdashboard)]]
    merged={k:v for output in outputs for k,v in output.payload.items()}
    swings=merged['swings'];labels=merged['structure_labels'];trend=merged['trend'];zones=merged['zones']
    momentum=merged['momentum'];fxzones=merged['fx_zones'];levels=merged['levels'];alignment=merged['alignment']
    bos=merged['bos'];choch=merged['choch'];pivots=merged['pivots'];patterns=merged['patterns']
    price=float(df.close.iloc[-1]);values=indicators.rsi
    divergence_run=run('integration',ctx,lambda c:{'divergences':divergences(c.candles,c.indicators.rsi,bar_seconds=seconds)})
    divs=divergence_run.payload['divergences']
    book_run=run('sentiment',ctx,lambda c:sentiment(snapshot,symbol,asof,sentiment_source_id))
    records=[{'time':int(t.timestamp()),'open':float(r.open),'high':float(r.high),'low':float(r.low),'close':float(r.close)} for t,r in df.iterrows()]
    findings=[]
    for label in labels[-12:]:
        findings.append({'id':f"structure-{label['time']}",'title':f"{label['label']} · {label['price']:.5f}",'source':'STRUCT.ai','time':label['time'],'price':label['price'],'explanation':f"{label['kind'].title()} pivot at {pd.Timestamp(label['time'],unit='s',tz='UTC').isoformat()}. Needs three later candles; the upstream alternating swing sequence may revise. Snapshot finding, not a frozen historical signal."})
    for event in (bos+choch)[-12:]:
        findings.append({"id":f"break-{event['label']}-{event['time']}-{event['price']}","title":f"{event['label']} · {event['price']:.5f}","source":"STRUCT.ai","time":event["time"],"price":event["price"],"explanation":"Close crossed a structure level. Upstream classification uses the current snapshot trend and may revise; this is not a frozen historical signal."})
    for i,z in enumerate(fxzones):
        findings.append({'id':f'zone-{i}','title':f"{z['kind']} · {z['bottom']:.5f}–{z['top']:.5f}",'source':'FX Signal Desk','time':int(pd.Timestamp(z['t0']).timestamp()),'price':(z['top']+z['bottom'])/2,'explanation':f"{'Bullish' if z['side']==1 else 'Bearish'} zone; currently {z['status']}. Origin time is not its confirmation time. Evaluated using only the current replay prefix."})
    for i,d in enumerate(divs):
        findings.append({'id':f'divergence-{i}','title':f"{d['direction'].title()} RSI divergence",'source':'Integration replacement','time':d['time'],'price':d['price'],'explanation':f"Price {d['prior_price']:.5f} → {d['price']:.5f}; RSI {d['rsi_from']:.1f} → {d['rsi_to']:.1f}. Confirmed after three subsequent candles; this is a pattern, not a trade instruction."})
    result=clean({'symbol':symbol,'interval':interval,'as_of':asof.isoformat(),'input_count':len(base),'candles':records,'swings':swings,'zigzag_lines':merged['zigzag_lines'],'structure_labels':labels,'trend':trend,'zones':zones,'bos':bos,'choch':choch,'trendlines':{'bullish':None,'bearish':None},'current_price':price,'sr_levels':[{'price':x['price'],'kind':'support' if x['price']<price else 'resistance','timeframe':interval,'touches':x['touches']} for x in levels], 'fx_zones':fxzones,'patterns':patterns,'pivots':pivots,'alignment':alignment,'momentum':momentum,'indicators':{'ema20':[{'time':r['time'],'value':float(v)} for r,v in zip(records,indicators.fast) if np.isfinite(v)],'ema50':[{'time':r['time'],'value':float(v)} for r,v in zip(records,indicators.slow) if np.isfinite(v)],'rsi':[{'time':r['time'],'value':float(v)} for r,v in zip(records,values) if np.isfinite(v)],'rsi_current':float(values.iloc[-1])},'divergences':divs,'findings':findings,'sentiment':book_run.payload,'daily_bias':evaluate_bias(daily,'daily',symbol,market.source.id,market.as_of,book_run.payload),'weekly_bias':evaluate_bias(weekly,'weekly',symbol,market.source.id,market.as_of,book_run.payload),'modules':[{'name':'STRUCT.ai','state':'connected','role':'Chart, structure, supply/demand, momentum'},{'name':'FX Signal Desk','state':'connected','role':'S/R, FVGs, order blocks, candle patterns, RSI'},{'name':'Scalper Agent V2','state':'connected','role':'EMA alignment and momentum assessment'},{'name':'ForexDashboard','state':'connected' if snapshot else 'awaiting snapshot','role':'Pivot prices and optional OANDA book scoring'}]})

    event_run=run('lifecycle',ctx,lambda c:{'events':replay(history,source_id=market.source.id,symbol=symbol,timeframe=interval,calendar=calendar)})
    events=event_run.payload['events']
    if selection_reason:
        result['sentiment']['selection_reason']=selection_reason
        if snapshot is None:result['sentiment']['reason']=selection_reason
    result['historical']=summary(events,market.as_of)
    result['retrospective_only']=True
    result['volatility']=merged['volatility']
    try:
        result['contract'] = envelope(result,candles[:cutoff],data_source,df,daily,snapshot,base_timeframe,calendar,market)
        result['aggregation']=aggregation
        result['module_runs']=[o.metadata() for o in [indicator_run,*outputs,divergence_run,book_run,event_run]]
        result['module_runs'][-1]['calculation_version']=EVENT_VERSION
    except (ValueError, KeyError, TypeError) as exc:
        raise ContractBoundaryError(f'Invalid analysis boundary: {exc}') from exc
    if event_sink is not None:event_sink(events,market.as_of)
    return result
