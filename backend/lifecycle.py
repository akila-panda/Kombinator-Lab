"""Chronological closed-bar event engine. Never rescans past signals with today's trend/ATR."""
from __future__ import annotations
import hashlib
import json
from typing import Literal
from pydantic import Field, model_validator
from .contracts import Contract, Timestamp, Price, Symbol, Timeframe
from .calendars import CalendarId
from .indicators import Indicators

VERSION='p05-causal-v1'
RIGHT=3
LIFETIME=160

class CandleEvidence(Contract):
    open_time:Timestamp
    close_time:Timestamp
    open:Price
    high:Price
    low:Price
    close:Price

    @model_validator(mode='after')
    def bounds(self):
        if self.open_time>=self.close_time or self.high<max(self.open,self.low,self.close) or self.low>min(self.open,self.close):raise ValueError('Invalid event candle evidence')
        return self

class Event(Contract):
    id:str
    finding_id:str
    source_id:str
    symbol:Symbol
    timeframe:Timeframe
    calendar:CalendarId
    kind:Literal['occurrence','confirmation','invalidation','expiration','revision']
    finding_kind:Literal['pivot_high','pivot_low','bos','choch','fvg','order_block','rsi_divergence']
    occurred_at:Timestamp
    available_at:Timestamp
    status:Literal['provisional','confirmed','invalidated','expired']
    direction:Literal['bullish','bearish','neutral']
    prices:list[float]=Field(min_length=1)
    evidence:list[CandleEvidence]=Field(min_length=1)
    structure_label:Literal['HH','HL','LH','LL','EQH','EQL']|None=None
    reason:str
    related_finding_id:str|None=None
    calculation_version:Literal['p05-causal-v1']=VERSION

    @model_validator(mode='after')
    def timing(self):
        import math
        if self.available_at<self.occurred_at:raise ValueError('Event available before occurrence')
        if any(not math.isfinite(p) or p<=0 for p in self.prices):raise ValueError('Invalid event price')
        for e in self.evidence:
            if e.close_time>self.available_at:raise ValueError('Future or malformed event evidence')
        required={'occurrence':'provisional','confirmation':'confirmed','invalidation':'invalidated','expiration':'expired'}
        if self.kind in required and self.status!=required[self.kind]:raise ValueError('Event kind/status mismatch')
        return self

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def replay(df,*,source_id,symbol,timeframe,calendar):
    """All target bars, ordered oldest first. Full-prefix indicators, not a sliding 500-bar seed."""
    import math
    indicators=Indicators.calculate(df)
    rows=[{'open_time':int(t.timestamp()),'close_time':int(r.close_time),**{k:float(r[k]) for k in ['open','high','low','close']}} for t,r in df.iterrows()]
    series=[VERSION,source_id,symbol,timeframe,calendar]
    events=[];states={};pending=[];active={};previous={'high':None,'low':None};structure={'high':None,'low':None}
    def evidence(indices):return [rows[j].copy() for j in sorted(set(indices))]
    def emit(f,kind,i,reason,indices,related=None):
        status={'occurrence':'provisional','confirmation':'confirmed','invalidation':'invalidated','expiration':'expired','revision':f['status']}[kind]
        e=Event(id='event:'+digest([f['id'],kind,rows[i]['close_time'],related]),finding_id=f['id'],source_id=source_id,symbol=symbol,timeframe=timeframe,calendar=calendar,kind=kind,finding_kind=f['kind'],occurred_at=rows[f['origin']]['open_time'],available_at=rows[i]['close_time'],status=status,direction=f['direction'],prices=f['prices'],structure_label=f.get('label'),evidence=evidence(indices),reason=reason,related_finding_id=related).model_dump(mode='json')
        events.append(e);f['status']=status;f['last_event_id']=e['id'];f['updated_at']=e['available_at']
        if kind=='confirmation':f['confirmed_at']=e['available_at']
        if kind in ('invalidation','expiration'):f[kind+'_at']=e['available_at']
    def create(kind,origin,i,direction,prices,reason,indices,confirmed=True,key=None):
        fid='finding:'+digest([series,kind,rows[origin],key])
        f={'id':fid,'kind':kind,'origin':origin,'born':i,'direction':direction,'prices':prices,'status':'provisional','occurred_at':rows[origin]['open_time'],'confirmed_at':None}
        states[fid]=f
        emit(f,'occurrence',i,reason,indices)
        if confirmed:emit(f,'confirmation',i,reason,indices)
        return f
    for i,r in enumerate(rows):
        # Existing levels/zones are evaluated before newly confirmed pivots become active.
        trend='bullish' if structure=={'high':'HH','low':'HL'} else 'bearish' if structure=={'high':'LH','low':'LL'} else 'neutral'
        a=float(indicators.atr.iloc[i])
        for fid,f in list(active.items()):
            direction=f['direction'];prices=f['prices'];kind=f['kind']
            if kind.startswith('pivot_'):
                level=prices[0];side='bullish' if kind=='pivot_high' else 'bearish'
                buffer=(0. if trend not in ('neutral',side) else max(.01 if symbol.endswith('JPY') else .0001,.05*a)) if math.isfinite(a) else None
                broken=buffer is not None and ((kind=='pivot_high' and r['close']>level+buffer) or (kind=='pivot_low' and r['close']<level-buffer))
                if broken:
                    side='bullish' if kind=='pivot_high' else 'bearish'
                    break_kind='choch' if trend not in ('neutral',side) else 'bos'
                    create(break_kind,i,i,side,[level],f'Close broke a previously confirmed level; trend={trend}; current ATR buffer={buffer}.',[f['origin'],f['confirmation_index'],i],key=fid)
                    emit(f,'invalidation',i,'Confirmed pivot level broken by close.',[f['origin'],i]);del active[fid];continue
            else:
                broken=(direction=='bullish' and r['close']<min(prices)) or (direction=='bearish' and r['close']>max(prices))
                if broken:
                    emit(f,'invalidation',i,'Close crossed the far edge / divergence extreme.',[f['origin'],i]);del active[fid];continue
                if kind in ('fvg','order_block') and not f.get('tested') and r['low']<=max(prices) and r['high']>=min(prices):
                    emit(f,'revision',i,'First later candle touched the zone; original geometry retained.',[f['origin'],i]);f['tested']=True
            if i-f['born']>=LIFETIME:
                emit(f,'expiration',i,'160 completed target bars elapsed since confirmation.',[f['born'],i]);del active[fid]
        for f in pending[:]:
            p=f['origin'];kind=f['kind'];field='high' if kind=='pivot_high' else 'low'
            defeated=r[field]>=rows[p][field] if field=='high' else r[field]<=rows[p][field]
            if defeated:
                emit(f,'invalidation',i,'Right-hand candle defeated strict pivot candidate.',[p,i]);pending.remove(f)
            elif i==p+RIGHT:
                old=previous[field]
                if old:
                    newprice=f['prices'][0];oldprice=old['prices'][0]
                    f['label']=('EQH' if field=='high' else 'EQL') if newprice==oldprice else ('HH' if newprice>oldprice else 'LH') if field=='high' else ('HL' if newprice>oldprice else 'LL')
                    structure[field]=f['label']
                emit(f,'confirmation',i,'Strict 3-left / 3-right pivot confirmed at right candle close.',list(range(p-RIGHT,i+1)))
                f['confirmation_index']=i;f['born']=i;active[f['id']]=f;pending.remove(f)
                old=previous[field]
                if old:
                    prior=old['origin'];oldprice=old['prices'][0];newprice=f['prices'][0]
                    emit(old,'revision',i,'New confirmed same-side pivot becomes structure reference; earlier event retained.',[prior,p,i],related=f['id'])
                    x=float(indicators.rsi.iloc[prior]);y=float(indicators.rsi.iloc[p])
                    diverges=(newprice>oldprice and y<x) if field=='high' else (newprice<oldprice and y>x)
                    if 4<=p-prior<=80 and math.isfinite(x) and math.isfinite(y) and diverges:
                        d=create('rsi_divergence',p,i,'bearish' if field=='high' else 'bullish',[newprice],f'Confirmed pivots diverge from full-prefix Wilder RSI: {x} to {y}.',[prior,p,i],key=old['id']);active[d['id']]=d
                previous[field]=f
        if i>=RIGHT:
            for field in ('high','low'):
                values=[rows[j][field] for j in range(i-RIGHT,i)]
                candidate=r[field]>max(values) if field=='high' else r[field]<min(values)
                if candidate:
                    f=create('pivot_'+field,i,i,'bearish' if field=='high' else 'bullish',[r[field]],'Left-side extreme; unavailable as confirmed until three later closes.',list(range(i-RIGHT,i+1)),False);pending.append(f)
        if i>=2:
            prev=rows[i-1];first=rows[i-2];a_prev=float(indicators.atr.iloc[i-1])
            if not math.isfinite(a_prev) or a_prev<=0:continue
            side=1 if r['low']>first['high'] and prev['close']>prev['open'] else -1 if r['high']<first['low'] and prev['close']<prev['open'] else 0
            if side and abs(prev['close']-prev['open'])>=.5*a_prev:
                bounds=[first['high'],r['low']] if side==1 else [r['high'],first['low']]
                if bounds[1]-bounds[0]>=.15*a_prev:
                    f=create('fvg',i-2,i,'bullish' if side==1 else 'bearish',bounds,'Three-candle gap confirmed only at third close.',[i-2,i-1,i]);active[f['id']]=f
            side=1 if r['close']-r['open']>=1.3*a_prev and prev['close']<prev['open'] else -1 if r['open']-r['close']>=1.3*a_prev and prev['close']>prev['open'] else 0
            if side and prev['high']-prev['low']>=.3*a_prev:
                f=create('order_block',i-1,i,'bullish' if side==1 else 'bearish',[prev['low'],prev['high']],'Opposite candle followed by displacement; available at displacement close.',[i-1,i]);active[f['id']]=f
    return events

def project(events,as_of):
    states={}
    for e in events:
        if e['available_at']>as_of:continue
        f=states.setdefault(e['finding_id'],{'id':e['finding_id'],'kind':e['finding_kind'],'occurred_at':e['occurred_at'],'confirmed_at':None,'direction':e['direction'],'prices':e['prices'],'revisions':[]})
        f.update(status=e['status'],updated_at=e['available_at'],last_event_id=e['id'])
        if e.get('structure_label'):f['structure_label']=e['structure_label']
        if e['kind']=='confirmation':f['confirmed_at']=e['available_at']
        if e['kind'] in ('invalidation','expiration'):f[e['kind']+'_at']=e['available_at']
        if e['kind']=='revision':f['revisions'].append(e['id'])
    return list(states.values())

def summary(events,as_of,limit=100):
    visible=[e for e in events if e['available_at']<=as_of];states=project(visible,as_of)
    active=[f for f in states if f['status']=='confirmed']
    return {'calculation_version':VERSION,'as_of':as_of,'event_count':len(visible),'finding_count':len(states),'available_count':len(active),'available_findings':active[-limit:],'recent_events':visible[-limit:],'limit':limit,'truncated':len(active)>limit or len(visible)>limit,'retrospective_overlays_excluded':True}
