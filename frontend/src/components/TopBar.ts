export interface ToggleState {
  zigzag: boolean;
  labels: boolean;
  zones: boolean;
  sr15m: boolean;
  sr1h: boolean;
  sr4h: boolean;
  sessions: boolean;
  bos: boolean;
  ob: boolean;   // NEW — Order Blocks
  fvg: boolean;  // NEW — Fair Value Gaps
  fib: boolean;  // Fibonacci retracement levels from last 4H swing
  fibD1: boolean;  // Fibonacci retracement levels from last D1 swing
  d1Zones: boolean; // D1 supply/demand zones (D1 chart only)
  d1SR: boolean;  // D1 S/R levels (cross-timeframe)
  w1Zones:  boolean;
  w1SR:     boolean;
   // MTF zone overlays — overlay higher-TF zones on any chart timeframe
  zonesW1: boolean;  // Weekly zones — dark purple
  zonesD1: boolean;  // Daily zones  — blue
  zones4h: boolean;  // 4H zones     — green
  zones1h: boolean;  // 1H zones     — yellow
}