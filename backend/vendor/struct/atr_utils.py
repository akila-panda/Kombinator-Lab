"""P04 compatibility wrapper over canonical Wilder ATR (replaces rolling mean)."""
import math
from ...indicators import atr

def compute_atr14(df):
    value=atr(df).iloc[-1] if len(df) else float('nan')
    if not math.isfinite(value):raise ValueError('ATR requires 14 complete observations')
    return float(value)
