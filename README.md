# 📊 Best Execution & Slippage Analyzer

> **Institutional-grade liquidity analysis and trade simulation dashboard.**  
> Simulate large crypto orders across multiple exchanges to calculate realized slippage and compare against OTC desk quotes.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![CCXT](https://img.shields.io/badge/Data-CCXT-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 🧐 Problem
Institutions moving large size (e.g., $1M - $10M) cannot verify if their OTC fills are competitive without analyzing real-time order book depth. Public exchange "mid-price" is misleading for large orders due to **slippage**.

## 💡 Solution
This tool connects to live Level-2 Order Books (via CCXT) and "walks the book" to simulate the execution of a specific trade size. It calculates the **Weighted Average Price (VWAP)** of the trade and compares the total "drag" (Slippage + Fees) against a quoted OTC premium.

## ✨ Key Features

-   **🕷️ Smart Order Book Walker**: Does not just look at the top price. It consumes liquidity layer-by-layer to calculate the *real* cost of execution.
-   **⚡ Multi-Exchange Aggregation**: Runs concurrent simulations across Binance, Kraken, Coinbase, and KuCoin to find the best execution venue.
-   **📉 Slippage Curve**: Visualizes how slippage (%) increases exponentially as trade size increases.
-   **🌊 Liquidity Depth Charts**: Interactive visualizations of Buy vs. Sell walls.
-   **🕒 Historical Time-of-Day Analysis**: Analyzes 30-day hourly volatility to recommend the optimal time of day (UTC) to trade.

## 🚀 Quick Start

We use `uv` for ultra-fast dependency management, but standard pip works too. An automated script is provided.

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/otc-slippage-analyzer.git
cd otc-slippage-analyzer
```

### 2. Run the Auto-Start Script
This script will automatically create a virtual environment, install dependencies, and launch the app.
```bash
python3 start.py
```

### Manual Setup option
If you prefer standard pip:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run src/frontend/app.py
```

## 🖥️ Usage

1.  **Select Asset**: Choose BTC/USDT, ETH/USDT, etc.
2.  **Trade Parameters**: Input your intended trade size (e.g., $5,000,000) and specific Exchanges to compare.
3.  **OTC Settings**: Input the fee/premium your OTC desk is charging (e.g., 50bps).
4.  **Analyze**: The dashboard will simulate the trade on all selected exchanges in parallel.
5.  **Result**:
    -   **"Winner"**: It will flag if you should execute on-screen or take the OTC quote.
    -   **Savings**: Calculates the net USD saved by choosing the optimal path.

## 🏗️ Tech Stack

-   **Backend**: Python, CCXT (Unified Exchange API), Pandas.
-   **Frontend**: Streamlit.
-   **Visualization**: Plotly Interactive Charts.
-   **Concurrency**: `concurrent.futures` for parallel API requests.

## ⚠️ Disclaimer
This software is for educational and analytical purposes only. It is not financial advice. Past performance (historical volatility) does not guarantee future results. Real execution costs may vary due to network latency and high-frequency trading activity.


