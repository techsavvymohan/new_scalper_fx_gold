
## 9. References

[1] Pasted Content 1 (SATS Indicator Details) - Provided by User
[2] Pasted Content 2 (SATS Mini UI Details) - Provided by User

# Product Requirements Document: XAUUSD Scalping Bot

**Author**: Manus AI
**Date**: June 18, 2026
**Version**: 1.1

## 1. Introduction

This Product Requirements Document (PRD) outlines the specifications for developing an automated scalping trading bot for XAUUSD CFD. The bot will operate on the MetaTrader 5 (MT5) platform, leveraging a Python-based automation framework. Its core trading logic will be derived from the "Self-Aware Trend System (SATS)" indicator, a sophisticated adaptive SuperTrend framework. The primary objective is to execute high-frequency, short-duration trades (scalping) with precise entry and exit conditions, focusing on capturing small price movements while strictly adhering to risk management principles.

## 2. Product Overview

The XAUUSD Scalping Bot is an algorithmic trading system designed to automate trade execution on the MT5 platform for the XAUUSD (Gold vs. US Dollar) CFD instrument. It will utilize the advanced trend detection and risk management capabilities of the SATS indicator, translated from Pine Script to Python. The bot will monitor multiple low timeframes (M1, M5, M15) to identify scalping opportunities, manage positions, and record trade data for future analysis and backtesting. The system is engineered for speed and efficiency, ensuring minimal latency in order placement and modification.

## 3. Functional Requirements

### 3.1. Trading Platform Integration

*   **FR-TP-001**: The bot shall connect to the MetaTrader 5 (MT5) trading platform using the `MetaTrader5` Python library.
*   **FR-TP-002**: The bot shall be able to retrieve real-time market data (OHLCV, Bid/Ask prices) for XAUUSD CFD from MT5.
*   **FR-TP-003**: The bot shall be able to place market orders (buy/sell), pending orders, and modify/close existing orders on MT5.
*   **FR-TP-004**: The bot shall handle connection stability and automatically attempt to reconnect to MT5 upon disconnection.

### 3.2. SATS Indicator Logic Implementation

The core of the bot's strategy is the precise replication of the SATS indicator's logic in Python. This includes all modules and parameters as detailed in the provided content [1] [2].

#### 3.2.1. Core Indicator Architecture

*   **FR-SATS-001**: Implement the calculation of Average True Range (ATR) with a length of 13.
*   **FR-SATS-002**: Implement the calculation of the Efficiency Ratio (ER) with an Efficiency Window of 20.
*   **FR-SATS-003**: Implement the Trend Quality Index (TQI) calculation, incorporating Efficiency (35%), Volatility (20%), Structure (25%), and Momentum Persistence (20%) weights.
*   **FR-SATS-004**: Implement Adaptive SuperTrend Bands based on the calculated ATR and TQI.
*   **FR-SATS-005**: Implement signal generation logic based on SuperTrend band flips and TQI conditions.

#### 3.2.2. Main Trend Engine

*   **FR-SATS-006**: Utilize an ATR Length of 13 for SuperTrend bands, Stop Loss calculation, and volatility measurement.
*   **FR-SATS-007**: Calculate the Base Band Width as `Price ± (ATR × 2)`, with dynamic modifications based on adaptive engine outputs.

#### 3.2.3. Adaptive Engine

*   **FR-SATS-008**: Enable Volatility-Adaptive Bands (equivalent to `Enable Vol-Adaptive Bands = TRUE`).
*   **FR-SATS-009**: Implement adaptation logic using an Efficiency Window of 20, Adaptation Strength of 0.5, and an ATR Baseline of 100. This involves comparing Current ATR vs. 100-bar Average ATR and using the Kaufman Efficiency Ratio to determine market regime (trending, ranging, noisy) and adjust band width accordingly.

#### 3.2.4. Trend Quality Engine

*   **FR-SATS-010**: Enable the Trend Quality Engine (equivalent to `Enable Trend Quality Engine = TRUE`).
*   **FR-SATS-011**: Apply a Quality Influence of 0.4 (40% adaptive) to determine how much TQI affects the SuperTrend bands.
*   **FR-SATS-012**: Implement a Quality Curve Power of 1.5 for non-linear scaling of band width, ensuring smoother adaptation.

#### 3.2.5. Asymmetric Bands

*   **FR-SATS-013**: Enable Asymmetric Bands (equivalent to `TRUE`) with a Strength of 0.5. This means the Upper Band and Lower Band will be calculated independently, with the trailing stop being tighter in the direction of the trend and wider on the opposite side.

#### 3.2.6. Efficiency Weighted ATR

*   **FR-SATS-014**: Enable Efficiency Weighted ATR (equivalent to `TRUE`), calculating it as `ATR × EfficiencyRatio` to reduce noise in ranging markets.

#### 3.2.7. Character Flip Detection

*   **FR-SATS-015**: Enable Character Flip Detection (equivalent to `TRUE`).
*   **FR-SATS-016**: Implement early trend flip logic: if TQI was > 0.55 and then falls < 0.25 within 5 bars (Min Age = 5, High TQI = 0.55, Low TQI = 0.25), the trend should flip before a price cross of the band.

#### 3.2.8. TQI Weight Distribution

*   **FR-SATS-017**: Ensure the TQI calculation accurately reflects the specified weights: 35% Efficiency, 20% Volatility, 25% Structure, and 20% Momentum Persistence.

#### 3.2.9. Structure Detection

*   **FR-SATS-018**: Implement Structure Detection using a Structure Window of 20 bars to analyze highs/lows and determine trending or ranging market conditions.

#### 3.2.10. Momentum Persistence

*   **FR-SATS-019**: Implement Momentum Persistence calculation over 10 bars to assess the continuation of trend direction.

#### 3.2.11. Signal Scoring Engine

*   **FR-SATS-020**: While primarily for display in the original indicator, the bot shall utilize the Structure Score (Pivot Strength = 3), RSI Score (Length = 14, OB = 70, OS = 30, Memory = 20 bars), and Volume Score (Volume Window = 20) as additional filters or confirmation for trade signals.

#### 3.2.12. Risk Engine

*   **FR-SATS-021 (clarification)**: Stop Loss and Take Profit orders shall be placed as server-side orders on MT5 (not managed client-side in bot memory only), so that protective levels remain active in the event of bot disconnection, crash, or restart.
*   **FR-SATS-022**: Implement a Maximum SL of 4 ATR as a safety cap.

#### 3.2.13. Take Profit System

*   **FR-SATS-023**: Implement a Fixed Take Profit (TP) mode.
*   **FR-SATS-024**: The bot shall target only TP1 (1R) and ignore TP2 (2R) and TP3 (3R).
*   **FR-SATS-025**: The bot shall close 0.5 (50%) of the position at TP1. The remaining 50% of the position should be managed according to the scalping strategy (e.g., trailing stop or immediate closure after partial TP).

#### 3.2.14. Trade Timeout

*   **FR-SATS-026**: Implement a trade timeout mechanism that automatically closes any open trade after 100 bars if it has not reached its TP or SL.

#### 3.2.15. Dynamic TP Engine & Self-Learning Engine

*   **FR-SATS-027**: The Dynamic TP Engine and Self-Learning Engine, although present in the SATS indicator, shall remain disabled in the initial version of the bot to maintain a fixed strategy for scalping. Their logic (TQI Influence = 60%, Volatility = 40% for Dynamic TP; Window = 20 trades, Quality Step = 0.05 for Self-Learning) should be noted for potential future enhancements.

#### 3.2.16. Alert System

*   **FR-SATS-028**: The bot shall integrate with the SATS alert system (via webhook if available, or by directly processing signals) to receive trade entry/exit signals.

### 3.3. Trading Strategy

*   **FR-STR-001**: The bot shall operate as a scalper, focusing on short-term price movements and quick exits.
*   **FR-STR-002 (revised)**: The bot shall monitor XAUUSD CFD on two timeframes: M15 and M5. M15 serves as the trend filter; M5 serves as the primary signal generator and entry trigger. M1 is explicitly out of scope for V1 (see Section 6, Future Enhancements addendum).
*   **FR-STR-003**: Entry signals will be generated when the SATS indicator signals a trend flip (long or short) and all relevant confirmation conditions (e.g., from Signal Scoring Engine) are met.
*   **FR-STR-004**: Exit signals will be generated upon reaching TP1 (0.5 part), Stop Loss, or Trade Timeout.
*   **FR-STR-005**: The bot shall compute the SATS trend direction (SuperTrend band state) independently on M15 and on M5.
*   **FR-STR-006**: A long entry shall only be evaluated when the M15 SATS trend direction is bullish; a short entry shall only be evaluated when the M15 SATS trend direction is bearish. If M15 and M5 trend direction disagree, no trade shall be taken.
*   **FR-STR-007**: All entry signals (FR-SATS-005), SL/TP calculations (FR-SATS-021 to FR-SATS-025), and trade timeout logic (FR-SATS-026) shall be evaluated on the M5 series. M15 contributes directional bias only and does not independently generate entries, exits, or stop/target levels.
*   **FR-STR-008**: Each trade record (per FR-DS-002) shall log the M15 trend state at signal time, in addition to the M5 indicator values, so that filter effectiveness can be audited separately from signal quality.

### 3.4. Capital Management & Lot Sizing

*   **FR-CM-001**: The bot shall dynamically calculate lot sizes based on the available capital and a predefined risk per trade percentage (e.g., 0.5% or 1% of capital per trade).
*   **FR-CM-002**: The bot shall support various capital sizes, including 500, 1000, 2000, 5000, 10000, and 100000 USD, adjusting lot sizes proportionally.
*   **FR-CM-003**: The bot shall ensure that the calculated lot size adheres to MT5's minimum and maximum lot size requirements for XAUUSD CFD.

### 3.5. Data Storage & Backtesting

*   **FR-DS-001**: The bot shall store all executed trades in a structured format (e.g., CSV, JSON, or a database) suitable for later backtesting and performance analysis.
*   **FR-DS-002**: Each trade record shall include, but not be limited to: entry time, exit time, entry price, exit price, stop loss price, take profit price, lot size, direction (buy/sell), profit/loss (in pips and currency), duration, timeframe, and relevant SATS indicator values at entry/exit.
*   **FR-DS-003**: The data format shall be easily parsable by common data analysis tools (e.g., Pandas in Python).

### 3.6. Cost & Execution Realism

*   **FR-COST-001**: The bot's backtesting module shall model realistic spread, commission, and slippage for XAUUSD CFD, using the connected broker's actual historical spread data where available, or a conservative fixed estimate otherwise.
*   **FR-COST-002**: Backtests shall be run under at least two cost scenarios: (a) normal/average spread, and (b) 2-3x average spread to simulate volatile-session conditions. Strategy viability shall be assessed under both.
*   **FR-COST-003**: Live and demo trade records shall capture realized slippage (intended fill price vs. actual fill price) for ongoing comparison against backtest assumptions.

### 3.7. Strategy Validation Requirements

*   **FR-VAL-001**: Before any live deployment, the bot's signal logic shall undergo an ablation test: each SATS sub-module (Adaptive Engine, Trend Quality Engine, Asymmetric Bands, Efficiency-Weighted ATR, Character Flip Detection) shall be independently disabled and the resulting performance compared to the full stack, to confirm each module contributes measurable out-of-sample edge.
*   **FR-VAL-002**: Core parameters (ATR Length, Efficiency Window, SL Buffer, TQI flip thresholds) shall be stress-tested with ±20% perturbations. Performance shall not degrade sharply under these perturbations; sharp degradation indicates overfitting and disqualifies the parameter set from live use.
*   **FR-VAL-003**: Backtesting shall use walk-forward validation across multiple market regimes (at minimum: one trending period and one ranging/choppy period from available history), with expectancy, profit factor, max drawdown, and Sortino ratio reported separately per regime.
*   **FR-VAL-004**: The bot shall complete a minimum extended forward-test (demo account) period, trading live market data without real capital, before any funded deployment. Minimum duration and trade count thresholds shall be defined in the configuration module (NFR-MAINT-002).
*   **FR-VAL-005**: Initial live deployment shall use minimum position sizing and scale up only after forward-test performance is confirmed consistent with validated backtest expectancy.

### 3.8. Risk Filters & Capital Protection

*   **FR-RISK-001**: The bot shall implement a session filter, restricting trading to specified hours (e.g., London/NY session overlap) configurable in the Configuration Module.
*   **FR-RISK-002**: The bot shall integrate an economic calendar check and shall pause new trade entries for a configurable window (default: 15 minutes before/after) around high-impact scheduled news events (e.g., NFP, CPI, FOMC).
*   **FR-RISK-003**: The bot shall implement an ATR-percentile volatility filter to avoid entries during abnormally low (illiquid/choppy) or abnormally high (event-driven spike) volatility conditions, with thresholds configurable.
*   **FR-RISK-004**: The bot shall enforce a daily maximum loss limit (configurable, e.g., as % of capital). Trading shall halt for the remainder of the trading day once this limit is reached.
*   **FR-RISK-005**: The bot shall enforce a maximum consecutive-loss circuit breaker, pausing new entries after N consecutive losing trades (N configurable) pending manual review or a cool-down period.
*   **FR-RISK-006**: The bot shall enforce a weekly/monthly drawdown kill switch that halts all trading and notifies the user if cumulative drawdown exceeds a configurable threshold.

### 3.9. Breakout Probability Indicator

*   **FR-BOP-001**: The bot shall implement a Breakout Probability calculation module to calculate the probability of a new high or low on the next candle based on historical data.
*   **FR-BOP-002**: The breakout probabilities shall be calculated separately depending on the direction of the previous candle (Green: close > open, Red: close < open, Doji: close = open).
*   **FR-BOP-003**: The module shall calculate:
    *   Probability of next high exceeding previous high (`high > prev_high`).
    *   Probability of next low falling below previous low (`low < prev_low`).
    *   Probability of hitting $N$ configured levels above the previous close (with custom percentage step size).
    *   Probability of hitting $N$ configured levels below the previous close.
*   **FR-BOP-004**: The calculated breakout probabilities shall be integrated as an entry filter. The bot shall only trigger a buy entry if the probability of a new high is greater than or equal to `BREAKOUT_MIN_PROBABILITY_THRESHOLD` (e.g., 55%), and a sell entry only if the probability of a new low meets the threshold.

## 4. Non-Functional Requirements

### 4.1. Performance

*   **NFR-PERF-001**: The bot shall exhibit high execution speed, with trade signal processing and order placement latency minimized to ensure scalping effectiveness.
*   **NFR-PERF-002**: The bot shall be optimized to prevent lagging, even when monitoring multiple timeframes and performing complex calculations.

### 4.2. Reliability

*   **NFR-REL-001**: The bot shall implement robust error handling for MT5 connection issues, order placement failures, and data retrieval errors.
*   **NFR-REL-002**: The bot shall include logging mechanisms to record all significant events, errors, and trade activities.
*   **NFR-REL-003**: The bot shall be designed for continuous operation, with mechanisms to recover from unexpected interruptions.

### 4.3. Security

*   **NFR-SEC-001**: The bot shall securely handle MT5 login credentials and API keys, avoiding hardcoding sensitive information.

### 4.4. Maintainability

*   **NFR-MAINT-001**: The codebase shall be modular, well-structured, and extensively commented to facilitate future modifications and debugging.
*   **NFR-MAINT-002**: Configuration parameters (e.g., risk per trade, MT5 account details) shall be externalized (e.g., in a configuration file) for easy adjustment without code changes.

### 4.5. Usability

*   **NFR-USAB-001**: The bot shall provide a simple interface or logging output for monitoring its status, open trades, and performance metrics.

## 5. Technical Architecture (High-Level)

### 5.1. Core Components

*   **MT5 Connector Module**: Handles connection, data retrieval, and order execution with MetaTrader 5.
*   **SATS Logic Module**: Implements all SATS indicator calculations and signal generation in Python.
*   **Strategy Execution Module**: Manages trade entry, exit, and position management based on SATS signals and defined strategy rules.
*   **Risk & Money Management Module**: Calculates lot sizes, manages Stop Loss and Take Profit levels, and enforces overall risk parameters.
*   **Data Logger Module**: Stores trade history and relevant market data for backtesting and analysis.
*   **Configuration Module**: Loads and manages bot settings from an external configuration file.

### 5.2. Data Flow

1.  **Market Data Retrieval**: Real-time XAUUSD data (M1, M5, M15) is fetched from MT5.
2.  **SATS Calculation**: The SATS Logic Module processes market data to calculate indicator values and generate signals.
3.  **Signal Evaluation**: The Strategy Execution Module evaluates SATS signals against predefined trading rules.
4.  **Order Management**: Upon valid signal, the Risk & Money Management Module calculates lot size and sets SL/TP. The MT5 Connector Module then places/modifies orders.
5.  **Trade Monitoring**: Open trades are continuously monitored for SL/TP hits or trade timeout.
6.  **Data Logging**: All trade events and relevant data points are recorded by the Data Logger Module.

## 6. Future Enhancements (Out of Scope for V1)

*   **Dynamic TP Engine Activation**: Integrate and test the SATS Dynamic TP Engine for adaptive take-profit levels.
*   **Self-Learning Module**: Explore the activation and fine-tuning of the SATS Self-Learning Module for adaptive parameter adjustment.
*   **Multi-Asset Support**: Extend the bot to trade other CFD instruments or currency pairs.
*   **Advanced Reporting**: Develop a comprehensive reporting dashboard for detailed performance analysis.
*   **Web Interface**: Create a web-based interface for bot monitoring and control.
*   **M1 Entry-Timing Layer**: After the M5/M15 baseline is validated (per Section 3.7 above), evaluate adding M1 as an entry-timing refinement layer within confirmed M5 signal windows. Implement only if controlled A/B comparison (same M15 filter, same M5 signals, with/without M1 timing) shows statistically meaningful improvement in expectancy net of added latency and computational cost.
*   **Independent Per-Timeframe Risk Allocation**: If multi-timeframe independent signal generation is explored later (M1/M5/M15 each trading independently), per-timeframe risk budgets must be defined so correlated signals across timeframes don't compound account risk.

### Summary of Architectural Decision

The bot's V1 timeframe architecture is finalized as **hierarchical confluence using M15 (trend filter) and M5 (signal generator, entry, exit, and risk management)**. M1 is deferred to a post-validation enhancement, contingent on measured benefit. This keeps the validated signal surface to two timeframes, reduces computational/latency load, and aligns trade duration with the SATS indicator's bar-based mechanics (structure window, momentum window, trade timeout) at a scale where they retain meaning.

---

## PRD Addendum: M5/M15 Architecture, Validation, and Risk Controls

**Document**: Product Requirements Document: XAUUSD Scalping Bot
**Addendum Version**: 1.1
**Purpose**: Finalize timeframe architecture as M5 (primary signal) + M15 (trend filter), and close validation/risk gaps identified during requirements review.

---

### A. Revisions to Section 3.3 (Trading Strategy)

**Replace FR-STR-002** with:

*   **FR-STR-002 (revised)**: The bot shall monitor XAUUSD CFD on two timeframes: M15 and M5. M15 serves as the trend filter; M5 serves as the primary signal generator and entry trigger. M1 is explicitly out of scope for V1 (see Section F, Future Enhancements addendum).

**Add new requirements:**

*   **FR-STR-005**: The bot shall compute the SATS trend direction (SuperTrend band state) independently on M15 and on M5.
*   **FR-STR-006**: A long entry shall only be evaluated when the M15 SATS trend direction is bullish; a short entry shall only be evaluated when the M15 SATS trend direction is bearish. If M15 and M5 trend direction disagree, no trade shall be taken.
*   **FR-STR-007**: All entry signals (FR-SATS-005), SL/TP calculations (FR-SATS-021 to FR-SATS-025), and trade timeout logic (FR-SATS-026) shall be evaluated on the M5 series. M15 contributes directional bias only and does not independently generate entries, exits, or stop/target levels.
*   **FR-STR-008**: Each trade record (per FR-DS-002) shall log the M15 trend state at signal time, in addition to the M5 indicator values, so that filter effectiveness can be audited separately from signal quality.

---

### B. New Section: Cost & Execution Realism

*   **FR-COST-001**: The bot's backtesting module shall model realistic spread, commission, and slippage for XAUUSD CFD, using the connected broker's actual historical spread data where available, or a conservative fixed estimate otherwise.
*   **FR-COST-002**: Backtests shall be run under at least two cost scenarios: (a) normal/average spread, and (b) 2-3x average spread to simulate volatile-session conditions. Strategy viability shall be assessed under both.
*   **FR-COST-003**: Live and demo trade records shall capture realized slippage (intended fill price vs. actual fill price) for ongoing comparison against backtest assumptions.

---

### C. New Section: Strategy Validation Requirements

*   **FR-VAL-001**: Before any live deployment, the bot's signal logic shall undergo an ablation test: each SATS sub-module (Adaptive Engine, Trend Quality Engine, Asymmetric Bands, Efficiency-Weighted ATR, Character Flip Detection) shall be independently disabled and the resulting performance compared to the full stack, to confirm each module contributes measurable out-of-sample edge.
*   **FR-VAL-002**: Core parameters (ATR Length, Efficiency Window, SL Buffer, TQI flip thresholds) shall be stress-tested with ±20% perturbations. Performance shall not degrade sharply under these perturbations; sharp degradation indicates overfitting and disqualifies the parameter set from live use.
*   **FR-VAL-003**: Backtesting shall use walk-forward validation across multiple market regimes (at minimum: one trending period and one ranging/choppy period from available history), with expectancy, profit factor, max drawdown, and Sortino ratio reported separately per regime.
*   **FR-VAL-004**: The bot shall complete a minimum extended forward-test (demo account) period, trading live market data without real capital, before any funded deployment. Minimum duration and trade count thresholds shall be defined in the configuration module (NFR-MAINT-002).
*   **FR-VAL-005**: Initial live deployment shall use minimum position sizing and scale up only after forward-test performance is confirmed consistent with validated backtest expectancy.

---

### D. New Section: Risk Filters & Capital Protection

*   **FR-RISK-001**: The bot shall implement a session filter, restricting trading to specified hours (e.g., London/NY session overlap) configurable in the Configuration Module.
*   **FR-RISK-002**: The bot shall integrate an economic calendar check and shall pause new trade entries for a configurable window (default: 15 minutes before/after) around high-impact scheduled news events (e.g., NFP, CPI, FOMC).
*   **FR-RISK-003**: The bot shall implement an ATR-percentile volatility filter to avoid entries during abnormally low (illiquid/choppy) or abnormally high (event-driven spike) volatility conditions, with thresholds configurable.
*   **FR-RISK-004**: The bot shall enforce a daily maximum loss limit (configurable, e.g., as % of capital). Trading shall halt for the remainder of the trading day once this limit is reached.
*   **FR-RISK-005**: The bot shall enforce a maximum consecutive-loss circuit breaker, pausing new entries after N consecutive losing trades (N configurable) pending manual review or a cool-down period.
*   **FR-RISK-006**: The bot shall enforce a weekly/monthly drawdown kill switch that halts all trading and notifies the user if cumulative drawdown exceeds a configurable threshold.

---

### E. Revision to Section 3.2.12 (Risk Engine) — Execution Detail

*   **FR-SATS-021 (clarification)**: Stop Loss and Take Profit orders shall be placed as server-side orders on MT5 (not managed client-side in bot memory only), so that protective levels remain active in the event of bot disconnection, crash, or restart.

---

### F. Updated Future Enhancements (Section 6)

Add to the existing list:

*   **M1 Entry-Timing Layer**: After the M5/M15 baseline is validated (per Section C above), evaluate adding M1 as an entry-timing refinement layer within confirmed M5 signal windows. Implement only if controlled A/B comparison (same M15 filter, same M5 signals, with/without M1 timing) shows statistically meaningful improvement in expectancy net of added latency and computational cost.
*   **Independent Per-Timeframe Risk Allocation**: If multi-timeframe independent signal generation is explored later (M1/M5/M15 each trading independently), per-timeframe risk budgets must be defined so correlated signals across timeframes don't compound account risk.

---

### Summary of Architectural Decision

The bot's V1 timeframe architecture is finalized as **hierarchical confluence using M15 (trend filter) and M5 (signal generator, entry, exit, and risk management)**. M1 is deferred to a post-validation enhancement, contingent on measured benefit. This keeps the validated signal surface to two timeframes, reduces computational/latency load, and aligns trade duration with the SATS indicator's bar-based mechanics (structure window, momentum window, trade timeout) at a scale where they retain meaning.

