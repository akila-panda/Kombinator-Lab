"""Selected EMA/momentum logic from Forex Scalper Agent V2.
Adapted into an offline component; no broker or config imports.
Score is a heuristic, not a probability.
"""
import pandas as pd
from typing import Dict
import logging
logger = logging.getLogger(__name__)
INDICATORS = {"ema_fast": 20, "ema_slow": 50}
class TechnicalAlignment:
    def check_h1_alignment(
        self,
        h1_data: pd.DataFrame,
        signal_direction: str,
        fast_values=None, slow_values=None
    ) -> Dict:
        """
        Check if H1 trend aligns with signal direction.
        Uses EMA crossover and price position relative to EMAs.
        """
        try:
            df = h1_data.copy()

            # Calculate EMAs
            ema_fast = INDICATORS['ema_fast']
            ema_slow = INDICATORS['ema_slow']

            from ..indicators import ema
            df['ema_fast'] = ema(df['close'],ema_fast) if fast_values is None else fast_values
            df['ema_slow'] = ema(df['close'],ema_slow) if slow_values is None else slow_values

            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            # Determine H1 trend
            ema_bullish = latest['ema_fast'] > latest['ema_slow']
            price_above_emas = (
                latest['close'] > latest['ema_fast'] and 
                latest['close'] > latest['ema_slow']
            )
            price_below_emas = (
                latest['close'] < latest['ema_fast'] and 
                latest['close'] < latest['ema_slow']
            )

            # Recent momentum
            momentum = (latest['close'] - prev['close']) / prev['close'] * 100

            # Score calculation
            score = 50  # Neutral baseline

            if signal_direction == 'BUY':
                if ema_bullish:
                    score += 25
                if price_above_emas:
                    score += 15
                if momentum > 0:
                    score += 10
            else:  # SELL
                if latest['ema_fast'] < latest['ema_slow']:
                    score += 25
                if price_below_emas:
                    score += 15
                if momentum < 0:
                    score += 10

            score = min(100, max(0, score))

            trend = 'NEUTRAL' if latest['ema_fast']==latest['ema_slow'] else 'BULLISH' if ema_bullish else 'BEARISH'
            aligned = (
                (signal_direction == 'BUY' and ema_bullish) or
                (signal_direction == 'SELL' and latest['ema_fast'] < latest['ema_slow'])
            )

            return {
                'trend': trend,
                'aligned': aligned,
                'ema_fast': float(latest['ema_fast']),
                'ema_slow': float(latest['ema_slow']),
                'momentum_pct': round(momentum, 4),
                'score': score
            }

        except Exception as e:
            logger.error(f"H1 alignment check error: {e}")
            return {'aligned': False, 'score': 50, 'error': str(e)}
