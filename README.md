# 🔱 XAUUSD SATS Scalping Bot

[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![MetaTrader 5](https://img.shields.io/badge/MetaTrader-5-darkblue.svg)](https://www.mql5.com/)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/OS-Windows-lightgrey.svg)]()

An automated, high-frequency scalping trading robot for **XAUUSD (Gold) CFD** operating on the MetaTrader 5 (MT5) platform. Powered by the **Self-Aware Trend System (SATS)** adaptive indicator and enhanced with **Breakout Probability** filters for high-precision entry execution.

---

## ⚡ Key Features

*   **Triple Timeframe Confluence (M15 → M5 → M1)**: Uses M15 for macro-trend bias, M5 for structural confluence, and M1 for instant, precise entry timing.
*   **SATS Indicator Engine**: Translated directly from Pine Script, utilizing Kaufman's Efficiency Ratio (ER) and volatility-adaptive SuperTrend bands.
*   **Breakout Probability Filter**: Dynamically analyzes historical candles to determine the exact probability of next-candle breakouts before executing entries.
*   **Advanced Risk Controls**:
    *   Dynamic position sizing based on account equity and ATR volatility.
    *   Max SL capped at 4 ATR and automatic partial closing at TP1 (0.5R).
    *   Daily maximum loss limits and consecutive-losses circuit breaker.
*   **Auto-Reconnection**: Resilient MT5 connection polling that automatically handles network disconnections and path resolution.

---

## 📂 Project Structure

```text
xauusd_scalping_bot/
├── config/
│   └── config.py               # Main bot configurations
├── data/
│   └── trade_log.csv           # Historical trade logging database
├── scratch/
│   ├── execute_test_trade.py   # Live testing order execution
│   └── validate_integration.py # Sanity imports & dependencies test
├── src/
│   ├── breakout_probability.py # Breakout probability analyzer
│   ├── data_logger.py          # CSV logs management
│   ├── main.py                 # Bot daemon main loop
│   ├── mt5_connector.py        # MT5 platform bridge & path resolver
│   ├── risk_filters.py         # Capital protection & volatility filters
│   ├── risk_management.py      # Sizing & server-side SL/TP calculations
│   └── strategy_execution.py   # Confluence logic & position monitoring
├── tests/
│   ├── test_breakout_probability.py
│   └── test_gaps.py
├── .env                        # Local credentials (ignored by git)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Setup and Installation

### 1. Prerequisite
*   Windows OS (MT5 requirement)
*   Python 3.8+
*   MetaTrader 5 Desktop Terminal installed

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/techsavvymohan/new_scalper_fx_gold.git
cd new_scalper_fx_gold
pip install -r requirements.txt
```

### 3. Create Environment File
Create a `.env` file at the root of the project to securely save your MT5 details:
```env
MT5_LOGIN=your_login_id
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server_name
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

---

## 💻 VPS Setup & Hosting Guide

To achieve maximum profitability, hosting this scalping robot on a Virtual Private Server (VPS) is **highly recommended**.

### Why VPS is Critical for this Bot:
*   **Sub-10ms Latency**: Placing a VPS in the same server hub as your broker (e.g., London LD4 or New York NY4) reduces execution times, saving you from negative slippage on fast M1 XAUUSD moves.
*   **99.9% Uptime**: Eliminates risks of power cuts, local internet disconnections, or OS updates rebooting your system mid-trade.

### VPS Recommendations:
*   **OS**: Windows Server 2019/2022 (minimum 2 vCPUs and 4GB RAM).
*   **Providers**: Beeks Financial Cloud, ForexVPS, or Vultr/UltraVPS.

### Daemon Setup (Keep-Alive Script):
To ensure the bot restarts automatically in case of crashes, set up a simple batch runner (`run_bot.bat`) on your VPS:
```cmd
@echo off
:loop
python src/main.py
echo Bot crashed. Restarting in 5 seconds...
timeout /t 5
goto loop
```
Create a Windows Task Scheduler task to trigger this script **on system startup** so it stays active.

---

## 📈 Profit Maximization Recommendations

To squeeze the highest yield out of the SATS Scalper on live accounts:

1.  **Reduce Slippage via Raw Spreads**: Use an **ECN / Raw Spread account** (such as IC Markets, Pepperstone, or XM Zero). Since the bot trades on M1 with tight take-profits, high standard spreads will erode your returns.
2.  **Optimize Sessions Filter**: Enable the session filter (`SESSION_FILTER_ENABLED = True` in `config.py`) to restrict trading to the **London/NY Overlap (12:00 PM – 4:00 PM UTC)**. Volatility is cleanest here, whereas Asian session range-bound markets can cause false breakouts.
3.  **Adjust Breakout Probability for regimes**:
    *   In trending regimes, keep the breakout threshold at `60%` (`BREAKOUT_MIN_PROBABILITY_THRESHOLD = 0.60`).
    *   In highly volatile regimes (e.g., high news periods), increase it to `65%` to only accept the highest-probability executions.
4.  **Enforce Strict Calendar Pauses**: Ensure you do not trade 15 minutes before or after high-impact scheduled events (NFP, CPI, FOMC rate decisions). High-spread expansion during news can hit stops prematurely.

---

## 🛡️ Disclaimer

Trading financial instruments, especially leveraged CFDs like XAUUSD, involves high risk. This software is provided for educational and automation purposes only. Past performance does not guarantee future results. Test thoroughly on a demo account before risking real capital.
