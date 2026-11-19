"""P02 compatibility envelope. Does not invent missing historical confirmation."""
from .calendars import quality_report, SECONDS, expected_slots
import hashlib
import json
from pathlib import Path
from functools import lru_cache
import pandas as pd
from .contracts import (AnalysisEnvelope, Assessment, CanonicalCandle, DataSource,
    Evidence, Finding, INSTRUMENTS, LEGACY_SOURCE, MarketSnapshot, Overlay,
    SentimentObservation, SentimentResult, DURATIONS)

class ContractBoundaryError(RuntimeError):
    pass

@lru_cache
def versions():
    rows=json.loads((Path(__file__).resolve().parents[1]/'docs/source-snapshots.json').read_text())['archives']
    hashes={x['archive']:x['sha256'] for x in rows}
    return {'struct':'zip:'+hashes['Sturct-ai-main.zip'], 'fxdesk':'zip:'+hashes['FX-Signal-Desk-main.zip'],
            'scalper':'zip:'+hashes['forex-scalper-agent-v2-main.zip'], 'forexdashboard':'zip:'+hashes['ForexDashboard-main.zip'],
            'integration':'local-integration-0.1.0'}

def stamp(value):return int(pd.Timestamp(value).timestamp())

def make_snapshot(inputs,source,symbol,interval,asof,base_timeframe="1h",calendar="fixed-utc-v1"):
    source=DataSource.model_validate(source) if source is not None else LEGACY_SOURCE.model_copy()
    tf=interval
    normalized_inputs=[{'time':int(c['time']),**{k:float(c[k]) for k in ('open','high','low','close')},'volume':float(c.get('volume') or 0)} for c in inputs]
    signature={'symbol':symbol,'timeframe':tf,'source':source.model_dump(),'inputs':normalized_inputs,'base_timeframe':base_timeframe,'calendar':calendar}
    sid='snapshot:'+hashlib.sha256(json.dumps(signature,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    flags=[]
    if source.kind=='synthetic':flags.append('synthetic')
    if not source.provenance_verified:flags.append('unverified_source')
    quality=quality_report(inputs,base_timeframe,calendar)
    if quality['missing_bars']:flags.append('missing_scheduled_bars')
    if quality['scheduled_closed_slots']:flags.append('scheduled_closures')
    return MarketSnapshot(id=sid,symbol=symbol,timeframe=tf,base_timeframe=base_timeframe,calendar=calendar,as_of=asof,input_start=inputs[0]['time'],input_end=inputs[-1]['time']+SECONDS[base_timeframe],input_count=len(inputs),source=source,quality_flags=flags)

def envelope(raw, inputs, source, df, daily, imported_book=None,base_timeframe="1h",calendar="fixed-utc-v1",snapshot=None):
    snapshot=snapshot or make_snapshot(inputs,source,raw['symbol'],raw['interval'],stamp(raw['as_of']),base_timeframe,calendar)
    source=snapshot.source;symbol=snapshot.symbol;tf=snapshot.timeframe;asof=snapshot.as_of
    sid=snapshot.id;flags=snapshot.quality_flags;duration=DURATIONS[tf]
    candles=[];evidence=[];findings=[];overlays=[];assessments=[]
    for i,r in enumerate(raw['candles']):
        t=r['time'];cid=f'{source.id}:{symbol}:{tf}:{t}'
        quality=[x for x in flags if x in ('synthetic','unverified_source')]
        if i and t>candles[-1].close_time:
            gap_start=candles[-1].close_time
            missing=expected_slots(gap_start,t,SECONDS[base_timeframe],calendar)
            if missing:quality.append('missing_scheduled_bars_before')
            if (t-gap_start)//SECONDS[base_timeframe]>missing:quality.append('scheduled_closure_before')
        if source.volume_type=='unknown':quality.append('volume_unknown')
        volume=None if source.volume_type=='unknown' else float(df.volume.iloc[i])
        close_time=int(df.close_time.iloc[i]) if 'close_time' in df else t+duration
        c=CanonicalCandle(id=cid,symbol=symbol,timeframe=tf,calendar=calendar,source_id=source.id,open_time=t,close_time=close_time,observed_at=close_time,state='completed',open=r['open'],high=r['high'],low=r['low'],close=r['close'],volume=volume,volume_type=source.volume_type,quality_flags=quality)
        candles.append(c)
        evidence.append(Evidence(id='e:'+cid,symbol=symbol,kind='candle',source_id=source.id,occurred_at=t,available_at=close_time,candle_id=cid,explanation='Completed input candle; availability assumes supplied closed-candle history, not provider delivery latency.'))
    refs={c.open_time:e.id for c,e in zip(candles,evidence)}
    ver=versions()
    def add_finding(key,module,kind,title,time,prices,explanation,direction=None,extra_refs=None,confirmed=None,zone=None,points=None):
        if time not in refs:raise ValueError(f'Adapter finding {key} references an absent candle')
        fid=f'{sid}:{module}:{key}'
        finding=Finding(id=fid,snapshot_id=sid,symbol=symbol,timeframe=tf,module=module,source_version=ver[module],calculation_version='p05-snapshot-v1',kind=kind,title=title,direction=direction,prices=prices,occurred_at=time,confirmed_at=confirmed,status='confirmed' if confirmed is not None else 'provisional',evidence_ids=list(dict.fromkeys([refs[time]]+(extra_refs or []))),explanation=explanation,invalidation_condition='Not tracked by the compatibility adapter; use the separate p05-causal-v1 event journal for historical lifecycle.',timing_note='Detector confirmation time; no immutable event history yet.' if confirmed is not None else 'Origin time is not confirmed availability. Upstream snapshot may revise; This retrospective overlay is excluded from the causal event stream.')
        findings.append(finding)
        geometry={'zone':zone,'kind':'zone'} if zone else {'points':points or [{'time':time,'price':prices[0]}],'kind':'line' if points and len(points)==2 else 'marker'}
        overlays.append(Overlay(id='o:'+fid,finding_id=fid,**geometry))
    for item in raw['findings']:
        module={'STRUCT.ai':'struct','FX Signal Desk':'fxdesk','Integration replacement':'integration'}[item['source']]
        extra=[];confirmed=None;points=None;prices=[item['price']];direction=None
        if item['id'].startswith('divergence-'):
            d=raw['divergences'][int(item['id'].split('-')[-1])]
            confirmation=d['confirmed_at'];direction=d['direction'];prices=[d['prior_price'],d['price']]
            confirmation_open=confirmation-duration
            extra=[refs[d['prior_time']],refs[confirmation_open]]
            points=[{'time':d['prior_time'],'price':d['prior_price']},{'time':d['time'],'price':d['price']}]
        if item['id'].startswith('zone-'):
            z=raw['fx_zones'][int(item['id'].split('-')[-1])]
            direction='bullish' if z['side']==1 else 'bearish'
        add_finding(item['id'],module,'rsi_divergence' if module=='integration' else 'structure' if item['id'].startswith('structure-') else 'structure_break' if item['id'].startswith('break-') else 'fair_value_gap' if item['id'].startswith('zone-') and z['kind']=='FVG' else 'order_block' if item['id'].startswith('zone-') else 'snapshot_finding',item['title'],item['time'],prices,item['explanation'],direction,extra,confirmed,points=points)
    for i,d in enumerate(raw['divergences']):
        fid=f'{sid}:integration:divergence-{i}'
        overlays.append(Overlay(id='o:rsi:'+fid,finding_id=fid,pane='rsi',kind='line',points=[{'time':d['prior_time'],'price':d['rsi_from']},{'time':d['time'],'price':d['rsi_to']}]))
    for i,level in enumerate(raw['sr_levels']):
        t=raw['candles'][-1]['time'];key=f'sr-{i}'
        add_finding(key,'fxdesk','support_resistance',f"{level['kind'].title()} · {level['price']:.5f}",t,[level['price']],f"Backend S/R cluster with {level['touches']} touches. Snapshot level, not a causal historical event.")
        overlays[-1].kind='level'
        findings[-1].evidence_ids=[e.id for e in evidence if e.kind=='candle']
    for i,z in enumerate(raw['zones']):
        time=z['start_time']
        add_finding(f'supply-demand-{i}','struct','supply_demand',f"{z.get('kind','zone')} zone",time,[z['bottom'],z['top']],'Supply/demand geometry from the current snapshot; not an immutable event.',zone={'start_time':time,'end_time':min(z['end_time'],asof),'bottom':z['bottom'],'top':z['top']})
    for i,z in enumerate(raw['fx_zones']):
        # Replace compatibility marker with backend geometry for the existing evidence finding.
        matching=f'{sid}:fxdesk:zone-{i}'
        overlays.append(Overlay(id=f'o:region:{matching}',finding_id=matching,kind='zone',zone={'start_time':stamp(z['t0']),'end_time':asof,'bottom':z['bottom'],'top':z['top']}))
    def assess(module,kind,metrics,explanation,ev=None,status='available',direction=None):
        assessments.append(Assessment(module=module,kind=kind,source_version=ver[module],calculation_version='p05-snapshot-v1',status=status,direction=direction,metrics=metrics,evidence_ids=ev if ev is not None else ([e.id for e in evidence if e.kind=='candle'] if status=='available' else []),explanation=explanation))
    assess('struct','structure',{},'Current snapshot structure; not historical event validation.',direction=raw['trend']['trend'])
    assess('struct','momentum',{k:float(raw['momentum'][k]) for k in ['body_ratio','impulse_ratio']},'Candle body/range metrics; not probabilities.')
    alignment=raw['alignment']
    if 'error' in alignment:raise ValueError('Scalper adapter failed: '+alignment['error'])
    assess('scalper','ema_alignment',{k:float(alignment[k]) for k in ['ema_fast','ema_slow','momentum_pct']},'Selected-timeframe EMA20/EMA50 and close change; not independent sentiment.',direction=alignment['trend'].lower())
    volatility=raw.get('volatility')
    if volatility:
        assess('scalper','volatility', {k:volatility[k] for k in ['atr','atr_average20','ratio']},volatility['level']+': '+volatility['reason'])
    rsi=raw['indicators']['rsi_current']
    assess('fxdesk','rsi',{'rsi':rsi} if rsi is not None else {},'Wilder RSI14 with 14 changes of warmup.',status='available' if rsi is not None else 'insufficient_history')
    # Support/resistance and candle patterns retain exact versioned numeric inputs via candle refs.
    assess('fxdesk','support_resistance',{f'level_{i}':x['price'] for i,x in enumerate(raw['sr_levels'])},'Snapshot S/R levels; empty metrics means none detected.')
    assess('fxdesk','candle_patterns',{'count':float(len(raw['patterns']))},'Latest selected candle patterns: '+(', '.join(p[0] for p in raw['patterns']) or 'none detected'))
    if len(daily):
        day=stamp(daily.index[-1]);eid=f'daily-pivot-input:{symbol}:{day}'
        evidence.append(Evidence(id=eid,symbol=symbol,kind='calculation',source_id=source.id,occurred_at=day,available_at=int(daily.close_time.iloc[-1]) if 'close_time' in daily else day+86400,explanation=f"Complete session daily OHLC used by pivot calculation: high={daily.high.iloc[-1]}, low={daily.low.iloc[-1]}, close={daily.close.iloc[-1]}."))
        assess('forexdashboard','daily_pivots',raw['pivots'],'Classic pivots from last completed session daily candle.',ev=[eid])
    else:assess('forexdashboard','daily_pivots',{},'No complete daily candle.',status='insufficient_history')
    for key in ('daily_bias','weekly_bias'):
        b=raw.get(key)
        if not b:continue
        for e in b['evidence']:
            evidence.append(Evidence(**e,symbol=symbol,kind='calculation',source_id=source.id))
        available=b['direction']!='unavailable'
        assessments.append(Assessment(module='integration',kind=key,source_version=ver['integration'],calculation_version=b['version'],status='available' if available else 'insufficient_history',direction=b['direction'] if available else None,evidence_ids=b['evidence_ids'] if available else [],explanation=b['reason']+' '+b['invalidation']))
        b['finding_ids']=[]
        for i,level in enumerate(b['levels']):
            add_finding(f"{key}-level-{i}",'integration','bias_reference',f"{b['horizon'].title()} {level['name']} · {level['price']:.5f}",raw['candles'][-1]['time'],[level['price']],b['reason']+' '+b['invalidation'])
            f=findings[-1];f.evidence_ids=b['evidence_ids'];f.calculation_version=b['version'];f.invalidation_condition=b['invalidation'];f.timing_note=f"Computed from completed {b['horizon']} candles available by {b['evaluated_at']}; recomputed per replay prefix."
            overlays[-1].kind='level';b['finding_ids'].append(f.id)
    sentiment_source=DataSource(id=raw['sentiment'].get('source_id','imported-oanda-book'),kind='user_upload',description='User-asserted OANDA snapshot; provenance unverified')
    observations=[]
    for key,p in raw['sentiment'].get('parts',{}).items():
        available=p.get('score') is not None
        book=(imported_book or {}).get(key) or {}
        observed=stamp(book['time']) if book.get('time') else None
        retrieved=stamp(book['retrieved_at']) if book.get('retrieved_at') else None
        ev=[]
        if available:
            eid=f'book:{key}:{observed}'
            evidence.append(Evidence(id=eid,symbol=symbol,kind='observation',source_id=sentiment_source.id,occurred_at=observed,available_at=retrieved or observed,explanation='Imported book observation; historical delivery not verified if retrieval time is absent.'))
            ev=[eid]
        observations.append(SentimentObservation(kind='position_book' if key=='positionBook' else 'order_book',status='available' if available else 'unavailable',source=sentiment_source,observed_at=observed,retrieved_at=retrieved,availability_basis='retrieval_time' if retrieved is not None else 'observation_time_only',score=p.get('score'),evidence_ids=ev,reason=p.get('reason') or ('Upstream book-scoring heuristic.' if available else p.get('status','unavailable'))))
    sentiment=SentimentResult(status=raw['sentiment']['status'],observations=observations,reason=raw['sentiment']['reason'])
    return AnalysisEnvelope(instrument=INSTRUMENTS[symbol],snapshot=snapshot,candles=candles,evidence=evidence,findings=findings,overlays=overlays,assessments=assessments,sentiment=sentiment).model_dump(mode='json')
