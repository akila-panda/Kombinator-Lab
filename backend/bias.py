"""Deterministic completed-bar scenarios; no probability or execution signal."""
from .indicators import ema, rsi

VERSION = 'p08-bias-v1'


def resolve(structure, momentum, reference, zone):
    if 'unavailable' in (structure, momentum, reference):
        return 'unavailable'
    if 'mixed' in (structure, momentum, reference, zone):
        return 'mixed'
    votes = {s for s in (structure, momentum, reference, zone) if s in ('bullish', 'bearish')}
    if len(votes) == 2:
        return 'mixed'
    if structure == momentum and structure in votes:
        return structure
    return 'neutral' if not votes else 'mixed'


def evaluate(df, horizon, symbol, source_id, as_of, sentiment):
    # aggregate_frame supplies actual calendar close_time, including DST/session boundaries.
    df = df[df.close_time <= as_of].copy()
    evidence = [{'id':f'bias:{VERSION}:{source_id}:{symbol}:{horizon}:{int(t.timestamp())}',
                 'occurred_at':int(t.timestamp()),'available_at':int(r.close_time),
                 'explanation':f'{horizon} complete OHLC: {r.open}, {r.high}, {r.low}, {r.close}; input to {VERSION}.'}
                for t,r in df.iterrows()]
    out = dict(direction='unavailable',version=VERSION,horizon=horizon,as_of=as_of,
               evaluated_at=int(df.close_time.iloc[-1]) if len(df) else None,
               reason=f'Requires 50 complete {horizon} candles; available {len(df)}.',
               components=[],levels=[],evidence=evidence,evidence_ids=[e['id'] for e in evidence],
               invalidation='Recompute only after the next complete horizon candle. Missing required evidence makes the scenario unavailable.',
               sentiment_context={'status':sentiment['status'],'reason':sentiment['reason'],'role':'Context only; not a technical vote.'})
    if len(df)<50:
        return out
    close=float(df.close.iloc[-1]);fast=float(ema(df.close,20).iloc[-1]);slow=float(ema(df.close,50).iloc[-1]);strength=float(rsi(df.close).iloc[-1])
    pivots={}
    for field,fn in [('high',max),('low',min)]:
        values=df[field].tolist()
        pivots[field]=[i for i in range(3,len(df)-3) if values[i]==fn(values[i-3:i+4]) and values[i-3:i+4].count(values[i])==1]
    flat=bool((df.high==df.high.iloc[0]).all() and (df.low==df.low.iloc[0]).all() and (df.close==df.close.iloc[0]).all())
    structure='neutral' if flat else 'unavailable'
    structure_reason='Flat history: no strict pivots.' if flat else 'Requires two confirmed highs and two confirmed lows (three bars on each side).'
    zones=[]
    if all(len(v)>=2 for v in pivots.values()):
        h0,h1=pivots['high'][-2:];l0,l1=pivots['low'][-2:]
        rising=df.high.iloc[h1]>df.high.iloc[h0] and df.low.iloc[l1]>df.low.iloc[l0]
        falling=df.high.iloc[h1]<df.high.iloc[h0] and df.low.iloc[l1]<df.low.iloc[l0]
        structure='bullish' if rising else 'bearish' if falling else 'mixed'
        structure_reason=f'Confirmed highs {df.high.iloc[h0]:.5f} → {df.high.iloc[h1]:.5f}; lows {df.low.iloc[l0]:.5f} → {df.low.iloc[l1]:.5f}.'
        for name,i in [('supply',h1),('demand',l1)]:
            r=df.iloc[i];bottom=float(max(r.open,r.close) if name=='supply' else r.low);top=float(r.high if name=='supply' else min(r.open,r.close))
            subsequent=df.close.iloc[i+3:]
            active=not bool((subsequent>top).any() if name=='supply' else (subsequent<bottom).any())
            zones.append(dict(name=name,bottom=bottom,top=top,active=active,confirmed_at=int(df.close_time.iloc[i+3])))
    momentum='bullish' if close>fast>slow and strength>50 else 'bearish' if close<fast<slow and strength<50 else 'neutral' if close==fast==slow and strength==50 else 'mixed'
    prior=df.iloc[-21:-1];support=float(prior.low.min());resistance=float(prior.high.max());mid=(support+resistance)/2
    reference='bullish' if close>mid else 'bearish' if close<mid else 'neutral'
    touches={('bearish' if z['name']=='supply' else 'bullish') for z in zones if z['active'] and z['bottom']<=close<=z['top']}
    zone='mixed' if len(touches)>1 else next(iter(touches)) if touches else 'neutral'
    components=[dict(name='structure',direction=structure,reason=structure_reason),
                dict(name='momentum',direction=momentum,reason=f'Close {close:.5f}; EMA20 {fast:.5f}; EMA50 {slow:.5f}; RSI14 {strength:.2f}.'),
                dict(name='reference',direction=reference,reason=f'Prior 20-bar range {support:.5f}–{resistance:.5f}; midpoint {mid:.5f}.'),
                dict(name='zone',direction=zone,reason='Latest confirmed pivot candle wick/body zones; close beyond outer boundary invalidates. No active touch is no directional vote.',zones=zones)]
    direction=resolve(structure,momentum,reference,zone)
    levels=[dict(name='prior range low',price=support),dict(name='prior range high',price=resistance),dict(name='range midpoint',price=mid)]
    for z in zones:
        if z['active']:
            levels.extend([dict(name=z['name']+' bottom',price=z['bottom']),dict(name=z['name']+' top',price=z['top'])])
    out.update(direction=direction,components=components,levels=levels,
               reason=f'{horizon.title()} {direction}: '+ '; '.join(c['name']+' '+c['direction'] for c in components)+'.',
               invalidation=f'At the next complete {horizon} close, recompute pivots, EMA/RSI, zones and the rolling range. Crossing midpoint {mid:.5f} changes reference direction; a close below {support:.5f} or above {resistance:.5f} breaks the current reference range. Directional bias requires matching structure and momentum with no opposing context.')
    return out
