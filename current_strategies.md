# 📊 Active Trading Strategies Summary

This document lists the trading strategies currently configured and executing on the **XAUUSD SATS Scalping Bot**.

---

## 1. Primary Strategy: SATS M5 Scalping with M15 Macro Confluence

### Core Logic
The bot executes high-frequency breakouts and trend-following entries on the **M5** chart, gated by macro trend filters on the **M15** chart.

### Signal Indicators
*   **SATS Kaufman Adaptive Bands (M5)**:
    *   Calculates dynamic bounds using Kaufman's Efficiency Ratio (ER) and the Trend Quality Index (TQI).
    *   Tightens bands on the trailing side of the trend to protect gains (asymmetric trailing compression).
    *   **Trigger**: A candlestick closing outside of the SATS Kaufman Adaptive Bands generates an entry signal (BUY on upper band breakout, SELL on lower band breakout).
*   **Trend Quality Index (TQI)**:
    *   Requires `TQI >= 0.60` on both execution (M5) and filter (M15) timeframes to validate the strength and health of the directional move.
*   **Kaufman Efficiency Ratio (ER)**:
    *   Requires `ER >= 0.50` on the macro filter (M15) timeframe to avoid noise-heavy ranging conditions.
*   **ATR Volatility Ratio**:
    *   Requires `ATR13 / ATR100 >= 1.0` on the macro filter (M15) timeframe to ensure there is active volume/volatility before entering.

---

## 2. Statistical Filter: Breakout Probability Analyzer

*   **Logic**: Parses the color sequences of historical candles (green/red) over the lookback window.
*   **Requirement**: Estimates the statistical probability of the next candle making a new high (for BUYs) or new low (for SELLs).
*   **Threshold**: Entry execution requires `Breakout Probability >= 60%` (`BREAKOUT_MIN_PROBABILITY_THRESHOLD = 0.60`) to filter out weak or exhaustive breakout attempts.

---

## 3. Context Engines (Logging & Signal Gating)

### A. Volatility & Trend Regime Engine
*   **Indicator**: Composite 3-z-score model of ATR ratio, Efficiency Ratio, and Trend Quality Index.
*   **Regimes**: Classifies markets into `TRENDING`, `RANGING`, `DEAD`, or `EXPLOSIVE`.
*   **Status**: Logged with every trade for regime optimization.

### B. Session Engine
*   **Logic**: Segregates market volatility by trading session:
    *   `ASIA` (22:00 – 08:00 UTC)
    *   `LONDON` (08:00 – 13:00 UTC)
    *   `OVERLAP` (13:00 – 16:00 UTC) - *Highest volatility overlap*
    *   `NEW_YORK` (16:00 – 22:00 UTC)
*   **Status**: Logged with every trade; allows disabling specific sessions if required.

---

## 4. Risk Engine V2 (Capital Protection)

*   **Risk Per Trade**: Capped at `0.5%` of current account balance (`RISK_PER_TRADE_PERCENT = 0.005`).
*   **Position Sizing**: Dynamically calculated per trade using the account balance, asset tick value, and SL distance.
*   **Stop Loss (SL)**: Set dynamically at `1.2 * ATR13` (capped at 4 ATR or 50 pips).
*   **Take Profit (TP)**: Set to `1.5 * SL_Distance` (1.5R target, capped at 30 pips).
*   **Breakeven Stop (SL to Entry)**: Activated on MT5 server as soon as trade hits `+1.0R` (TP1 level), securing a risk-free trade.
*   **Partial Close (TP1)**: Closes `50%` of the position volume automatically at `+1.0R`.
*   **Daily Drawdown Filter**: Circuit breaker blocks new trading if daily realized/unrealized loss exceeds `2.0%` of balance.
*   **Consecutive Losses Filter**:
    *   Cooldowned for `30 minutes` after 3 consecutive losses.
    *   Cooldowned for `60 minutes` after 5 consecutive losses.
