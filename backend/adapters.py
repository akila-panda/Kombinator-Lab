"""One typed snapshot context per run; selected upstream algorithms remain offline."""
from dataclasses import dataclass
from typing import Callable
import math
import pandas as pd
from .contracts import MarketSnapshot
from .indicators import Indicators
from .vendor.struct.zigzag_engine import detect_swings, swings_to_zigzag_lines
from .vendor.struct.structure_engine import classify_structure
from .vendor.struct.trend_engine import detect_trend
from .vendor.struct.zones_engine import detect_zones
from .vendor.struct.bos_engine import detect_bos
from .vendor.struct.choch_engine import detect_choch
from .vendor.struct.momentum_engine import compute_momentum
from .vendor.fxdesk.zones import find_fvgs, find_obs
from .vendor.fxdesk.patterns import sr_levels, more_candles
from .vendor.forexdashboard import calculate_pivot_points
from .vendor.scalper import TechnicalAlignment

class ModuleFailure(RuntimeError):
    def __init__(self,module,cause):
        self.module=module
        super().__init__(f'{module} analysis failed')
        self.__cause__=cause

@dataclass(frozen=True)
class AnalysisContext:
    snapshot:MarketSnapshot
    candles:pd.DataFrame
    daily:pd.DataFrame
    indicators:Indicators | None

@dataclass(frozen=True)
class ModuleOutput:
    module:str
    snapshot_id:str
    payload:dict

    def metadata(self):return {'module':self.module,'snapshot_id':self.snapshot_id,'status':'succeeded','calculation_version':'p04-adapters-v1'}

def run(module,ctx,fn:Callable):
    try:
        result=fn(ctx)
        if not isinstance(result,dict):raise TypeError('Adapter must return a dictionary')
        required={'struct':{'swings','structure_labels','trend','zones','bos','choch','momentum','zigzag_lines'},'fxdesk':{'fx_zones','levels','patterns'},'scalper':{'alignment','volatility'},'forexdashboard':{'pivots'},'integration':{'divergences'},'indicators':{'bundle'},'sentiment':{'status','reason'}}
        if not required.get(module,set())<=result.keys():raise ValueError('Incomplete module output')
        def finite(x):
            if isinstance(x,dict):
                for v in x.values():finite(v)
            elif isinstance(x,(list,tuple)):
                for v in x:finite(v)
            elif isinstance(x,float) and not math.isfinite(x):raise ValueError('Nonfinite module result')
        finite(result)
        return ModuleOutput(module,ctx.snapshot.id,result)
    except Exception as exc:raise ModuleFailure(module,exc) from exc

def struct(ctx):
    df=ctx.candles.copy();df['time']=df.index.tz_localize(None)
    tf=ctx.snapshot.timeframe;seconds={'1h':3600,'4h':14400,'d1':86400}[tf]
    swings=detect_swings(df,fractal_n=3,timeframe=tf)
    labels=classify_structure(swings);trend=detect_trend(labels)
    a=float(ctx.indicators.atr.iloc[-1])
    return {'swings':swings,'structure_labels':labels,'trend':trend,
        'zones':detect_zones(swings,tf,float(df.close.iloc[-1]),df=df,symbol=ctx.snapshot.symbol),
        'bos':detect_bos(df,swings,labels,trend['trend'],lookback_hours=500*seconds//3600,fractal_n=3,atr_value=a),
        'choch':detect_choch(df,swings,labels,trend['trend'],lookback_hours=500*seconds//3600,fractal_n=3),
        'momentum':compute_momentum(df,a),'zigzag_lines':swings_to_zigzag_lines(swings)}

def fxdesk(ctx):
    df=ctx.candles;a=float(ctx.indicators.atr.iloc[-1])
    return {'fx_zones':find_fvgs(df,atr_values=ctx.indicators.atr)+find_obs(df,atr_values=ctx.indicators.atr),
        'levels':sr_levels(df,atr_value=a),'patterns':more_candles(df,a)}

def scalper(ctx):
    df=ctx.candles;i=ctx.indicators
    alignment=TechnicalAlignment().check_h1_alignment(df,'BUY',i.fast,i.slow)
    if 'error' in alignment:raise ValueError(alignment['error'])
    # Selected volatility branch from analysis/regime_detector.py. No ADX/ML/confidence claim.
    current=float(i.atr.iloc[-1]);average=float(i.atr.iloc[-20:].mean())
    regime={'status':'available','level':'high' if current>average*1.5 else 'low' if current<average*.6 else 'normal',
            'atr':current,'atr_average20':average,'ratio':current/average if average>0 else 0.,
            'reason':'ATR14 versus its last 20 observations; thresholds 1.5 / 0.6; not a probability.'}
    if average==0:regime.update(level='flat',reason='Zero true range throughout the ATR reference window.')
    return {'alignment':alignment,'volatility':regime}

def forexdashboard(ctx):
    d=ctx.daily
    return {'pivots':calculate_pivot_points(float(d.high.iloc[-1]),float(d.low.iloc[-1]),float(d.close.iloc[-1])) if len(d) else {}}
