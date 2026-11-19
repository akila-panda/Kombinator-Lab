"""Offline extraction from ForexDashboard (MIT, Hamoon Soleimani).
Uses an injected snapshot reader in place of live account access.
"""
from typing import Dict, Any, Tuple
import logging
def calculate_pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    """Calculates classic daily pivot points and support/resistance levels."""
    # Input validation
    if not all(isinstance(x, (int, float)) and x > 0 for x in [high, low, close]):
        logging.warning(f"Invalid input for pivot calculation: H={high}, L={low}, C={close}")
        return {}
    if low > high: # Basic sanity check
        logging.warning(f"Low price ({low}) > High price ({high}) in pivot calculation.")
        return {}

    try:
        pivot = (high + low + close) / 3.0
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        return {'R3': r3, 'R2': r2, 'R1': r1, 'PP': pivot, 'S1': s1, 'S2': s2, 'S3': s3}
    except Exception as e:
        logging.error(f"Error calculating pivot points: {e}")
        return {}

class SnapshotStrategy:
    def __init__(self, reader):
        self.oanda_handler = reader
        self.pb_contrarian_high = 0.65
        self.pb_contrarian_low = 0.35
    def analyze_orderbook(self, instrument: str, pip_range: float) -> Tuple[float, Dict[str, Any]]:
        """Analyzes OANDA order book, returns score [-1, 1] and details."""
        score, details = 0.0, {"error": None, "pip_range": pip_range, "status": "init", "raw_data": None}
        try:
            orderbook_data = self.oanda_handler.fetch_orderbook(instrument)
            details["raw_data"] = orderbook_data
            if not orderbook_data or 'buckets' not in orderbook_data:
                details["error"] = "Failed to fetch/parse OB data"; details["status"] = "fetch_error"; return score, details

            current_price = orderbook_data.get('price') # Should be float now
            if current_price is None or current_price <= 0:
                price_info = self.oanda_handler.fetch_current_price(instrument)
                if price_info and price_info.get('mid', 0) > 0:
                     current_price = price_info['mid']
                     logging.warning(f"Using separately fetched price {current_price:.5f} for OB analysis of {instrument}.")
                else:
                    details["error"] = "Invalid current price in OB data"; details["status"] = "price_error"; return score, details

            prices, short_pcts, long_pcts = self.oanda_handler.parse_buckets(orderbook_data['buckets'])
            if not prices:
                details["error"] = "No valid buckets parsed from OB data"; details["status"] = "parse_error"; return score, details

            f_prices, f_shorts, f_longs = self.oanda_handler.filter_buckets_by_pips(prices, short_pcts, long_pcts, current_price, instrument, pip_range)
            if not f_prices:
                precision = self.oanda_handler.get_display_precision(instrument)
                details["error"] = f"No OB data within ±{pip_range:.0f} pips of {current_price:.{precision}f}";
                details["status"] = "filter_error"; return score, details

            total_long_pct = sum(f_longs); total_short_pct = sum(f_shorts)
            details.update({"filtered_long_pct": total_long_pct, "filtered_short_pct": total_short_pct, "filtered_buckets": len(f_prices)})

            total_orders_pct = total_long_pct + total_short_pct
            if total_orders_pct > 1e-6: # Avoid division by zero
                net_pct = (total_long_pct - total_short_pct) / total_orders_pct
                score = max(-1.0, min(1.0, net_pct)) # Clamp score
                details["net_pct"] = net_pct; details["status"] = "success"
            else:
                details["error"] = "Negligible orders found within range."; details["status"] = "no_orders_in_range"

        except Exception as e:
            details["error"] = f"OB Analysis Error: {e}"; details["status"] = "exception"
            logging.error(f"OB Analysis Error for {instrument}: {e}", exc_info=False)

        return score, details

    def analyze_positionbook(self, instrument: str) -> Tuple[float, Dict[str, Any]]:
        """Analyzes OANDA position book (contrarian view), returns score [-1, 1] and details."""
        score, details = 0.0, {"error": None, "status": "init", "raw_data": None}
        try:
            posbook_data = self.oanda_handler.fetch_positionbook(instrument)
            details["raw_data"] = posbook_data
            if not posbook_data or 'buckets' not in posbook_data:
                details["error"] = "Failed to fetch/parse PB data"; details["status"] = "fetch_error"; return score, details

            prices, short_counts_pct, long_counts_pct = self.oanda_handler.parse_buckets(posbook_data['buckets'])
            if not prices:
                details["error"] = "No valid buckets parsed from PB data"; details["status"] = "parse_error"; return score, details

            # Calculate overall long/short ratio from *all* buckets
            total_long_pct = sum(long_counts_pct); total_short_pct = sum(short_counts_pct)
            details.update({"overall_long_pct": total_long_pct, "overall_short_pct": total_short_pct})

            total_positions_pct = total_long_pct + total_short_pct
            if total_positions_pct > 1e-6: # Avoid division by zero
                long_ratio = total_long_pct / total_positions_pct
                details["long_ratio"] = long_ratio

                high_thresh = self.pb_contrarian_high; low_thresh = self.pb_contrarian_low
                if long_ratio >= high_thresh:
                    if high_thresh >= 1.0: score = -1.0 if long_ratio >= 1.0 else 0.0
                    else: score = -min(1.0, (long_ratio - high_thresh) / (1.0 - high_thresh))
                elif long_ratio <= low_thresh:
                    if low_thresh <= 0.0: score = 1.0 if long_ratio <= 0.0 else 0.0
                    else: score = min(1.0, (low_thresh - long_ratio) / low_thresh)
                else: score = 0.0

                score = max(-1.0, min(1.0, score)); details["status"] = "success"
            else:
                details["error"] = "Negligible total positions found in PB data."; details["status"] = "no_positions"

        except Exception as e:
            details["error"] = f"PB Analysis Error: {e}"; details["status"] = "exception"
            logging.error(f"PB Analysis Error for {instrument}: {e}", exc_info=False)

        return score, details
