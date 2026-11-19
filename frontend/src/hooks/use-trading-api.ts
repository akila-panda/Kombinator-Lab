export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface SwingPoint {
  index: number;
  time: number;
  price: number;
  kind: "high" | "low";
}

export interface ZigZagLine {
  from_time: number;
  from_price: number;
  to_time: number;
  to_price: number;
}

export interface StructureLabel {
  time: number;
  price: number;
  label: "HH" | "HL" | "LH" | "LL" | "EQH" | "EQL";
  kind: "high" | "low";
  index: number;
}

export interface TrendData {
  trend: "bullish" | "bearish" | "neutral";
  confidence: number;
  last_labels: string[];
}

export interface BosEvent {
  time: number;
  price: number;
  direction: "bullish" | "bearish";
  label: string;
  level_broken: number;
}

export interface ChochEvent {
  time: number;
  price: number;
  direction: "bullish" | "bearish";
  label: string;
  broken_label: string;
}

export interface TrendlineSegment {
  valid: boolean;
  slope: number;
  intercept: number;
  from_time: number;
  from_price: number;
  to_time: number;
  to_price: number;
  touches: number;
  invalidated: boolean;
}

export interface TrendlinesData {
  bullish: TrendlineSegment | null;   // single object now, not array
  bearish: TrendlineSegment | null;
}

export interface Zone {
  top: number;
  bottom: number;
  center: number;
  touches: number;
  strength: number;       // kept for backward compat (0–5)
  timeframe: string;
  start_time: number;
  end_time: number;
  broken?: boolean;
  // Phase 2 additions:
  status?: "fresh" | "tested_once" | "tested_multiple" | "broken";
  confidence?: number;    // 0–100
  departure_pips?: number;
  quality?: number;       // 0–100
}

export interface TradingAnalysisResponse {
  symbol: string;
  interval: string;
  candles: Candle[];
  swings: SwingPoint[];
  zigzag_lines: ZigZagLine[];
  structure_labels: StructureLabel[];
  trend: TrendData;
  bos: BosEvent[];
  choch: ChochEvent[];
  trendlines: TrendlinesData;
  zones: Zone[];
  current_price?: number | null;
}

export interface SRLevel {
  price: number;
  kind: "support" | "resistance";
  timeframe: "15m" | "1h" | "4h"| "d1"| "w1";
  touches: number;
  score?: number;
}

export interface BosChochLevel {
  type: "BOS" | "CHOCH";
  direction: "bullish" | "bearish";
  price: number;
  time: number;
  label: string;
}

export interface BosChochResponse {
  symbol: string;
  timeframe: string;
  levels: BosChochLevel[];
}

export interface SessionBox {
  session: "asian" | "london" | "ny";
  start_time: number;
  end_time: number;
  high: number;
  low: number;
}

export interface ConfluenceHit {
  price:            number;
  kind:             "support" | "resistance";
  aligned:          boolean;
  sr_timeframe:     string;
  sr_score:         number;
  zone_timeframe:   string;
  zone_quality:     number;
  zone_top:         number;
  zone_bottom:      number;
  zone_kind:        "supply" | "demand";
  zone_status:      string;
  confluence_score: number;
  has_ob:           boolean;
  has_fvg:          boolean;
}
