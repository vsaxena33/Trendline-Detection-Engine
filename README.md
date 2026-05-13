# Trendline-Detection-Engine

Real-time market structure detection engine using WebSocket streaming, live candlestick generation, and dynamic support/resistance trendline zones.

This project connects to the FYERS WebSocket API, receives live market ticks, builds OHLCV candles in real time, and automatically detects active support and resistance zones using the `trendln` library.

---

# Features

- Real-time WebSocket market data streaming
- Live OHLCV candlestick generation
- Dynamic support trendline detection
- Dynamic resistance trendline detection
- Active trendline validation
- Automatic trendline invalidation on breakout
- Real-time candlestick visualization
- Trendline zone generation instead of thin lines
- Support for live market structure analysis
- Rolling candle window for efficient memory usage

---

# How the System Works

```text
Live WebSocket Tick
        ↓
Update Current Candle
        ↓
New Candle Forms
        ↓
Detect Swing Highs / Swing Lows
        ↓
Generate Trendlines
        ↓
Validate Active Support/Resistance Zones
        ↓
Update Real-Time Chart
```

---

# Example Output

## Real-Time Support & Resistance Zones

- Green Zones → Support Regions
- Red Zones → Resistance Regions

(Add screenshots here)

```markdown
!(screenshots/chart.png)
```

---

# Technologies Used

- Python
- FYERS API
- WebSockets
- pandas
- numpy
- matplotlib
- mplfinance
- trendln

---

# Project Structure

```text
Realtime-Support-Resistance-Engine/
│
├── main.py
├── trendlineData.py
├── supportResistance.py
├── plot.py
├── newCandlestick.py
├── historicalData.py
├── requirements.txt
├── README.md
├── screenshots/
│   └── chart.png
├── credentials.py
├── autoLogin.py
└── configuration.py
```

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/Realtime-Support-Resistance-Engine.git

cd Realtime-Support-Resistance-Engine
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Required Libraries

```bash
pip install fyers-apiv3
pip install pandas
pip install numpy
pip install matplotlib
pip install mplfinance
pip install trendln
pip install pytz
```

---

# Setup FYERS Credentials

Create:

```text
credentials.py
```

Inside it:

```python
client_id = "YOUR_CLIENT_ID"
```

Also create:

```text
access_token.txt
```

Paste your FYERS access token inside it.

---

# Running the Project

```bash
python main.py
```

---

# Important Concepts Used

## OHLCV Candles

Each candle contains:

- Open price
- High price
- Low price
- Close price
- Volume

---

## Support Zones

Support zones are areas where price tends to stop falling and buyers become active.

These zones are generated using swing lows and trendline fitting.

---

## Resistance Zones

Resistance zones are areas where price tends to stop rising and sellers become active.

These zones are generated using swing highs and trendline fitting.

---

## Active Trendlines

A trendline remains active only while price respects the support/resistance zone.

If price strongly breaks the zone, the trendline is invalidated automatically.

---

# Future Improvements

- Multi-symbol support
- Breakout signal generation
- ATR-based dynamic zones
- Strategy backtesting
- Feature engineering for ML models
- Database storage
- Real-time alerts
- Streamlit dashboard
- Async WebSocket processing

---

# Educational Purpose

This project demonstrates important concepts used in:

- Algorithmic Trading
- Quantitative Finance
- Technical Analysis
- Real-Time Systems
- Event-Driven Programming
- Market Structure Analysis

---

# Author

Vaibhav Saxena

---

# License

This project is licensed under the MIT License.
