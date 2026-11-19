"""Canonical observed-bar indicators, p04-indicators-v1. No imputation."""
import numpy as np
import pandas as pd
from dataclasses import dataclass

def checked(s,n):
    if not isinstance(n,int) or isinstance(n,bool) or n<1:raise ValueError('Indicator period must be positive integer')
    if not np.isfinite(s.to_numpy(dtype=float)).all():raise ValueError('Indicator input contains missing/nonfinite values')

def ema(s,n):
    checked(s,n)
    return s.ewm(span=n,adjust=False,min_periods=n).mean()

def wilder(s,n):
    checked(s,n)
    out=pd.Series(np.nan,index=s.index,dtype=float)
    if len(s)<n:return out
    value=float(s.iloc[:n].mean());out.iloc[n-1]=value
    for i in range(n,len(s)):
        value=(value*(n-1)+float(s.iloc[i]))/n;out.iloc[i]=value
    return out

def atr(df,n=14):
    for k in ('high','low','close'):checked(df[k],n)
    prev=df.close.shift()
    tr=pd.concat([df.high-df.low,(df.high-prev).abs(),(df.low-prev).abs()],axis=1).max(axis=1)
    return wilder(tr,n)

def rsi(s,n=14):
    checked(s,n)
    delta=s.diff().iloc[1:]
    gains=wilder(delta.clip(lower=0),n);losses=wilder((-delta).clip(lower=0),n)
    result=pd.Series(np.nan,index=s.index,dtype=float)
    for i,(g,l) in enumerate(zip(gains,losses),1):
        if np.isfinite(g) and np.isfinite(l):result.iloc[i]=(50. if g==0 else 100.) if l==0 else 100-100/(1+g/l)
    return result

@dataclass(frozen=True)
class Indicators:
    fast:pd.Series
    slow:pd.Series
    atr:pd.Series
    rsi:pd.Series

    @classmethod
    def calculate(cls,df):return cls(ema(df.close,20),ema(df.close,50),atr(df),rsi(df.close))
