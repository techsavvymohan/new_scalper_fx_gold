# XAUUSD Scalping Bot

This project implements an automated scalping trading bot for XAUUSD CFD on the MetaTrader 5 (MT5) platform. The bot's core trading logic is derived from the "Self-Aware Trend System (SATS)" indicator, translated from Pine Script to Python.

## Features

- **MT5 Integration**: Connects to MetaTrader 5 for real-time data and order execution.
- **SATS Indicator**: Python implementation of the Self-Aware Trend System for signal generation.
- **Scalping Strategy**: Focuses on short-term price movements with precise entry and exit conditions.
- **Risk Management**: Dynamic lot sizing, Stop Loss, Take Profit, and various risk filters.
- **Data Logging**: Stores trade history for backtesting and performance analysis.
- **Configurable**: Externalized configuration for easy parameter adjustments.

## Project Structure

```
xauusd_scalping_bot/
├── config/
│   └── config.py
├── data/
├── src/
│   ├── __init__.py
│   ├── mt5_connector.py
│   ├── sats_logic.py
│   ├── strategy_execution.py
│   ├── risk_management.py
│   ├── data_logger.py
│   └── main.py
├── README.md
└── requirements.txt
```

## Setup and Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd xauusd_scalping_bot
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure MT5 and Bot Settings**:
    Edit `config/config.py` with your MT5 login details, server, path, and desired bot parameters.

## Usage

To run the bot, execute `python src/main.py`.

## Disclaimer

Trading foreign exchange on margin carries a high level of risk, and may not be suitable for all investors. The high degree of leverage can work against you as well as for you. Before deciding to invest in foreign exchange you should carefully consider your investment objectives, level of experience, and risk appetite. The possibility exists that you could sustain a loss of some or all of your initial investment and therefore you should not invest money that you cannot afford to lose. You should be aware of all the risks associated with foreign exchange trading, and seek advice from an independent financial advisor if you have any doubts.
