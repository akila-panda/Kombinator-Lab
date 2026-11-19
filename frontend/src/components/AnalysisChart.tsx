import React,{useEffect,useRef,useState} from 'react';
import {createChart,CandlestickSeries,LineSeries,ColorType} from 'lightweight-charts';
import type {IChartApi,ISeriesApi,Time,AutoscaleInfo} from 'lightweight-charts';
export type Finding={id:string;title:string;module:string;kind:string;occurred_at:number;prices:number[];explanation:string;evidence_ids:string[];status:string;source_version:string;calculation_version:string;timing_note:string};
export type Overlay={id:string;finding_id:string;pane:'price'|'rsi';kind:'marker'|'level'|'line'|'zone';points:{time:number;price:number}[];zone?:{start_time:number;end_time:number;bottom:number;top:number}|null};
export type Evidence={id:string;occurred_at:number;available_at:number;explanation:string};
export type ContractView={findings:Finding[];overlays:Overlay[];evidence:Evidence[];instrument:{price_precision:number};snapshot:{id:string}};
export const categories={bias_reference:'Bias levels',structure:'Structure',supply_demand:'Supply / demand',support_resistance:'S/R',structure_break:'BOS / CHoCH',fair_value_gap:'FVG',order_block:'Order blocks',rsi_divergence:'Divergence'};
export type Visibility=Record<string,boolean>;
type Input={candles:{time:number;open:number;high:number;low:number;close:number}[];contract:ContractView;indicators:{ema20:{time:number;value:number}[];ema50:{time:number;value:number}[];rsi:{time:number;value:number}[]}};
export function AnalysisChart({data,selected,visible,emaVisible,onSelect}:{data:Input;selected:Finding|null;visible:Visibility;emaVisible:boolean;onSelect:(f:Finding)=>void}){
 const host=useRef<HTMLDivElement>(null),api=useRef<IChartApi|null>(null),price=useRef<ISeriesApi<'Candlestick'>|null>(null),rsi=useRef<ISeriesApi<'Line'>|null>(null),emas=useRef<ISeriesApi<'Line'>[]>([]);
 const [tick,setTick]=useState(0);const [range,setRange]=useState('');
 useEffect(()=>{if(!host.current)return;const chart=createChart(host.current,{autoSize:true,layout:{background:{type:ColorType.Solid,color:'#0a0e17'},textColor:'#8fa4b9',panes:{separatorColor:'#304454',separatorHoverColor:'#4c7d7a'}},grid:{vertLines:{color:'#15202d'},horzLines:{color:'#15202d'}},timeScale:{timeVisible:true},rightPriceScale:{minimumWidth:75}});api.current=chart;
 const candles=chart.addSeries(CandlestickSeries,{upColor:'#69cbb0',downColor:'#e17783',borderVisible:false,wickUpColor:'#69cbb0',wickDownColor:'#e17783',priceFormat:{type:'price',precision:data.contract.instrument.price_precision,minMove:10**-data.contract.instrument.price_precision}});price.current=candles;
 candles.setData(data.candles.map(c=>({...c,time:c.time as Time})));
 emas.current=['#e0c375','#98aaf9'].map(color=>chart.addSeries(LineSeries,{color,lineWidth:1,priceLineVisible:false,lastValueVisible:false}));
 const indicator=chart.addSeries(LineSeries,{color:'#b59bff',lineWidth:2,priceLineVisible:false},1);rsi.current=indicator;
 const values=new Map(data.indicators.rsi.map(p=>[p.time,p.value]));indicator.setData(data.candles.map(c=>values.has(c.time)?{time:c.time as Time,value:values.get(c.time)!}:{time:c.time as Time}));
 for(const value of [30,70])indicator.createPriceLine({price:value,color:'#5e5574',lineWidth:1,lineStyle:2,axisLabelVisible:true,title:''});
 chart.panes()[1].setHeight(150);chart.timeScale().fitContent();
 let frame=0;const redraw=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{setTick(n=>n+1);const r=chart.timeScale().getVisibleRange();if(r)setRange(`${r.from} / ${r.to}`)})};
 chart.timeScale().subscribeVisibleLogicalRangeChange(redraw);chart.subscribeCrosshairMove(redraw);
 const element=host.current;const observer=new ResizeObserver(redraw);observer.observe(element);element.addEventListener('wheel',redraw);element.addEventListener('pointermove',redraw);redraw();
 return()=>{cancelAnimationFrame(frame);observer.disconnect();element.removeEventListener('wheel',redraw);element.removeEventListener('pointermove',redraw);chart.remove();api.current=null;price.current=null;rsi.current=null};
 },[data]);
 useEffect(()=>{emas.current.forEach((s,i)=>s.setData(emaVisible?(i?data.indicators.ema50:data.indicators.ema20).map(p=>({...p,time:p.time as Time})):[]))},[data,emaVisible]);
 useEffect(()=>{price.current?.applyOptions({autoscaleInfoProvider:(base:()=>AutoscaleInfo|null)=>{const info=base();if(!info?.priceRange||!selected)return info;return {...info,priceRange:{minValue:Math.min(info.priceRange.minValue,...selected.prices),maxValue:Math.max(info.priceRange.maxValue,...selected.prices)}}}});if(!selected||!api.current)return;if((selected.kind==='support_resistance'||selected.kind==='bias_reference')){api.current.timeScale().fitContent();setTick(n=>n+1);return}const shapes=data.contract.overlays.filter(o=>o.finding_id===selected.id);const times=shapes.flatMap(o=>o.zone?[o.zone.start_time,o.zone.end_time]:o.points.map(p=>p.time));if(!times.length)return;
 const rows=data.candles;const nearest=(t:number)=>{const n=rows.findIndex(c=>c.time>=t);return n<0?rows.length-1:n};
 api.current.timeScale().setVisibleLogicalRange({from:Math.max(0,nearest(Math.min(...times))-8),to:Math.min(rows.length+2,nearest(Math.max(...times))+8)});setTick(n=>n+1);
 },[selected,data]);
 const chart=api.current;const width=host.current?.clientWidth||0;const priceHeight=chart?.panes()[0]?.getHeight()||0;const paneHeight=chart?.panes()[1]?.getHeight()||0;
 const x=(time:number)=>{if(!chart)return null;const nearest=data.candles.reduce((best,c)=>Math.abs(c.time-time)<Math.abs(best-time)?c.time:best,data.candles[0].time);return chart.timeScale().timeToCoordinate(nearest as Time)};
 const shapes=data.contract.overlays.filter(o=>{const f=data.contract.findings.find(f=>f.id===o.finding_id);return f&&visible[f.kind]&&!(o.kind==='marker'&&data.contract.overlays.some(z=>z.finding_id===o.finding_id&&z.kind==='zone'))});
 return <div className="canonical-chart-wrap"><div className="chart-key"><span>PRICE · backend geometry</span><span>RSI 14 · shared time scale</span><button onClick={()=>api.current?.timeScale().fitContent()}>Fit history</button></div><div className="canonical-chart" ref={host} data-testid="synchronized-chart" data-visible-range={range}/><svg className="canonical-overlays" width={width} height={priceHeight+paneHeight} aria-label="Backend finding overlays" data-render={tick}><defs><clipPath id="price-clip"><rect width={Math.max(0,width-75)} height={priceHeight}/></clipPath><clipPath id="rsi-clip"><rect y={priceHeight} width={Math.max(0,width-75)} height={paneHeight}/></clipPath></defs>{shapes.map(o=>{
 const f=data.contract.findings.find(f=>f.id===o.finding_id)!;const active=f.id===selected?.id;const color=active?'#fff4a8':o.pane==='rsi'?'#b59bff':f.kind==='fair_value_gap'?'#ad97ff':f.kind==='order_block'?'#f3ad71':f.kind==='support_resistance'?'#e2c56c':'#6dd8bd';
 const y=(v:number)=>{const n=(o.pane==='rsi'?rsi.current:price.current)?.priceToCoordinate(v);return n==null?null:n+(o.pane==='rsi'?priceHeight:0)};
 let geometry:React.ReactNode=null;
 if(o.zone){const a=x(o.zone.start_time),b=x(o.zone.end_time),top=y(o.zone.top),bottom=y(o.zone.bottom);if(a!=null&&b!=null&&top!=null&&bottom!=null)geometry=<rect x={Math.min(a,b)} y={Math.min(top,bottom)} width={Math.max(3,Math.abs(b-a))} height={Math.max(3,Math.abs(bottom-top))} fill={color} fillOpacity={active?.25:.09} stroke={color} strokeWidth={active?3:1}/>}
 else if(o.points.length){const a=x(o.points[0].time),b=y(o.points[0].price);if(a!=null&&b!=null){if(o.kind==='line'){const c=x(o.points[1].time),d=y(o.points[1].price);if(c!=null&&d!=null)geometry=<><line x1={a} y1={b} x2={c} y2={d} stroke={color} strokeWidth={active?4:2}/><circle cx={a} cy={b} r={4} fill={color}/><circle cx={c} cy={d} r={4} fill={color}/></>}
 else if(o.kind==='level')geometry=<line x1={0} y1={b} x2={width-75} y2={b} stroke={color} strokeWidth={active?3:1} strokeDasharray="5 4"/>;
 else geometry=<circle cx={a} cy={b} r={active?7:4} fill={color}/>}}
 return geometry&&<g key={o.id} data-overlay-id={o.id} data-finding-id={f.id} data-pane={o.pane} role="button" tabIndex={0} aria-label={`${f.title} · ${o.pane}`} clipPath={`url(#${o.pane}-clip)`} style={{pointerEvents:'all',cursor:'pointer'}} onClick={()=>onSelect(f)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(f)}}}><title>{f.module}: {f.title} · {f.evidence_ids.length} evidence references</title>{geometry}</g>
 })}</svg></div>
}
