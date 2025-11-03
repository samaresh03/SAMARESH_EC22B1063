# Quant Trading Dashboard

A comprehensive quantitative trading analytics platform that ingests real-time market data from Binance, performs advanced statistical analysis, and provides interactive visualizations for pair trading and statistical arbitrage strategies.

## Features

### Core Functionality
- **Real-time Data Ingestion**: WebSocket connection to Binance for live tick data streaming
- **Multi-timeframe Analysis**: Support for 1s, 1m, 5m, 15m, 1h, 4h, 1d timeframes
- **Pair Trading Analytics**: 
  - OLS and Robust (Huber/Theil-Sen) regression
  - Z-score calculation for mean reversion signals
  - Cointegration testing (Johansen test)
  - Rolling correlation analysis
- **Technical Indicators**: RSI, MACD, Bollinger Bands, VWAP, Moving Averages
- **Statistical Tests**: Augmented Dickey-Fuller (ADF) for stationarity
- **Interactive Visualizations**: Candlestick charts, spread analysis, correlation heatmaps
- **Data Export**: CSV export of processed data and analytics
- **Custom Alerts**: Define and monitor price-based alerts
- **OHLC Data Upload**: Import historical data for backtesting

### Advanced Features
- **Dynamic Hedge Estimation**: Calculate optimal hedge ratios via regression
- **Liquidity Analysis**: Volume-weighted metrics and liquidity filters
- **Mean Reversion Backtesting**: Simple z-score based strategy testing
- **Rolling Beta Calculation**: Track systematic risk over time
- **Multi-symbol Dashboard**: Analyze multiple products simultaneously

## Architecture

### Technology Stack

**Backend:**
- **Framework**: FastAPI (async Python web framework)
- **Database**: SQLite (with SQLAlchemy ORM)
- **Real-time**: WebSockets for live data streaming
- **Data Processing**: Pandas, NumPy, Statsmodels, Scikit-learn

**Frontend:**
- **Framework**: Streamlit (rapid prototyping dashboard)
- **Visualization**: Plotly (interactive charts)
- **HTTP Client**: Requests

**Data Sources:**
- Binance Futures WebSocket API (real-time trades)
- Manual OHLC data upload (historical data)

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Streamlit)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Dashboard UI                                             │   │
│  │ - Symbol Selection & Timeframe Control                   │   │
│  │ - Interactive Price Charts (Plotly)                      │   │
│  │ - Pair Analysis Metrics                                  │   │
│  │ - Technical Indicators                                   │   │
│  │ - Alert Configuration                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ REST API Endpoints                                       │   │
│  │ - /api/v1/ohlcv (Get OHLCV data)                        │   │
│  │ - /api/v1/analytics/* (Analytics endpoints)             │   │
│  │ - /api/v1/export/* (Data export)                        │   │
│  │ - /api/v1/alerts (Alert management)                     │   │
│  │ - /ws/ticks (WebSocket for live data)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Services Layer                                           │   │
│  │ ┌─────────────────┐ ┌──────────────────┐ ┌────────────┐ │   │
│  │ │ WebSocket       │ │ Data Service     │ │ Analytics  │ │   │
│  │ │ Service         │ │ - OHLCV          │ │ Service    │ │   │
│  │ │ - Binance WS    │ │ - Resampling     │ │ - Stats    │ │   │
│  │ │ - Connection    │ │ - Storage        │ │ - Regression│ │   │
│  │ │   Management    │ │ - Retrieval      │ │ - Tests    │ │   │
│  │ └─────────────────┘ └──────────────────┘ └────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Database Layer (SQLAlchemy ORM)                          │   │
│  │ - Trade (raw tick data)                                  │   │
│  │ - OHLCV (resampled data)                                 │   │
│  │ - Analytics (precomputed metrics)                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↕ 
┌─────────────────────────────────────────────────────────────────┐
│                   DATA LAYER (SQLite)                           │
│  trading_data.db                                                │
│  - trades table (raw tick data)                                 │
│  - ohlcv table (resampled OHLCV)                                │
│  - analytics table (computed metrics)                           │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL DATA SOURCES                         │
│  - Binance Futures WebSocket (real-time trades)                 │
│  - Manual OHLC CSV Upload                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- pip or conda
- Git

### Setup Steps

1. **Clone or download the project**:
```bash
cd quant-trading-dashboard
```

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Initialize the database**:
```bash
cd backend
python -c "from app.models import init_db; init_db()"
cd ..
```

## Running the Application

### Option 1: Run Both Backend and Frontend (Recommended)

**Terminal 1 - Start Backend Server**:
```bash
cd backend
python main.py
```
The backend will start on `http://localhost:8000`

**Terminal 2 - Start Frontend Dashboard**:
```bash
cd frontend
streamlit run app.py
```
The frontend will open at `http://localhost:8501`

### Option 2: Using the Provided HTML WebSocket Tool

You can also use the provided `binance_browser_collector_save_test.html` to collect tick data directly in your browser:
1. Open the HTML file in a web browser
2. Enter symbols (comma-separated, lowercase): `btcusdt,ethusdt`
3. Click "Start" to begin collecting data
4. Download the NDJSON file when done

## Usage Guide

### Single Symbol Analysis

1. **Select a Symbol**: Choose from the dropdown in the sidebar
2. **Choose Timeframe**: Select your preferred timeframe (1m, 5m, 15m, etc.)
3. **View Metrics**: See real-time price statistics
4. **Analyze Chart**: Interactive candlestick chart with volume

### Pair Trading Analysis

1. **Select Two Symbols**: Choose two symbols for pair analysis
2. **Set Window Size**: Adjust the rolling window for indicators
3. **View Pair Metrics**:
   - **Z-Score**: Mean reversion signal (-2 to +2 range)
   - **Correlation**: Rolling correlation between assets
   - **Cointegration**: Statistical relationship test
   - **Regression**: OLS beta and alpha values

### Interpreting Metrics

#### Z-Score
- **> 2**: Overbought (potential short signal)
- **< -2**: Oversold (potential long signal)
- **0**: Mean (neutral)

#### Correlation
- **1.0**: Perfect positive correlation
- **0.0**: No correlation
- **-1.0**: Perfect negative correlation

#### Cointegration
- **p-value < 0.05**: Pair is cointegrated (mean-reverting)
- **p-value > 0.05**: Pair is not cointegrated

#### OLS Regression
- **Beta**: Sensitivity of Y to X (hedge ratio)
- **Alpha**: Intercept (mispricing)
- **R-squared**: Goodness of fit

## Analytics Explained

### Price Statistics
- **Current/Open/High/Low**: Price levels
- **Mean/Std**: Average and volatility
- **Sharpe Ratio**: Risk-adjusted returns (annualized)

### Regression Analysis

**OLS (Ordinary Least Squares)**:
- Linear regression: Y = α + β*X + ε
- Assumes normal distribution of residuals
- Sensitive to outliers

**Robust Regression (Huber/Theil-Sen)**:
- Less sensitive to outliers
- Better for real market data with anomalies
- Huber: Smooth transition between OLS and absolute deviation
- Theil-Sen: Median-based slope estimator

### Spread Calculation
- **Ratio Spread**: Y/X (price ratio)
- **OLS Residuals**: Y - (α + β*X) (statistical arbitrage spread)

### Z-Score
- Standardized measure: (X - mean) / std
- Rolling window calculation
- Identifies extreme deviations from mean

### Cointegration Test
- Tests if two non-stationary series move together
- Indicates long-term equilibrium relationship
- Critical for pair trading strategies

### ADF Test (Augmented Dickey-Fuller)
- Tests for stationarity
- p-value < 0.05: Series is stationary
- Important for mean reversion strategies

### Rolling Correlation
- Measures time-varying relationship between assets
- Window-based calculation
- Identifies regime changes

## API Endpoints

### OHLCV Data
```
GET /api/v1/ohlcv
Parameters:
  - symbol: str (e.g., 'btcusdt')
  - timeframe: str (e.g., '1m', '5m')
  - start_time: datetime (optional)
  - end_time: datetime (optional)
  - limit: int (default: 1000)
```

### Price Statistics
```
GET /api/v1/analytics/price-stats
Parameters:
  - symbol: str
  - timeframe: str
  - window: int (default: 20)
```

### Pair Metrics
```
GET /api/v1/analytics/pair-metrics
Parameters:
  - symbol1: str
  - symbol2: str
  - timeframe: str
  - window: int (default: 20)
```

### Data Export
```
GET /api/v1/export/csv
Parameters:
  - symbol: str
  - timeframe: str
  - start_time: datetime (optional)
  - end_time: datetime (optional)
Returns: CSV file download
```

### WebSocket (Real-time Ticks)
```
WebSocket /api/v1/ws/ticks
Receives: Trade events in real-time
```

## Data Models

### Trade
Raw tick data from Binance:
- `id`: Unique trade ID
- `symbol`: Trading pair
- `price`: Trade price
- `quantity`: Trade quantity
- `timestamp`: Trade time
- `created_at`: Record creation time

### OHLCV
Resampled OHLC data:
- `id`: Unique record ID
- `symbol`: Trading pair
- `timestamp`: Candle start time
- `timeframe`: Candle duration
- `open`, `high`, `low`, `close`: Price levels
- `volume`: Total quantity traded
- `trade_count`: Number of trades

### Analytics
Precomputed metrics:
- `id`: Unique record ID
- `symbols`: Asset(s) involved
- `metric`: Metric type (zscore, correlation, etc.)
- `value`: Computed value
- `timestamp`: Data point time
- `metadata`: Additional context (JSON)

## Configuration

Edit `backend/app/config.py` to customize:

```python
# Database
DATABASE_URL = "sqlite:///data/trading_data.db"

# Binance WebSocket
BINANCE_WS_URL = "wss://fstream.binance.com/ws/"
DEFAULT_SYMBOLS = ["btcusdt", "ethusdt"]

# Analytics
ANALYTICS_CONFIG = {
    "default_timeframe": "1m",
    "supported_timeframes": ["1s", "1m", "5m", "15m", "1h", "4h", "1d"],
    "zscore_window": 20,
    "correlation_window": 30,
    "adf_max_lag": 5,
}
```

## Troubleshooting

### WebSocket Connection Issues
- Check internet connection
- Verify Binance API is accessible
- Check firewall settings

### Database Errors
- Ensure `data/` directory exists
- Delete `trading_data.db` and reinitialize if corrupted
- Check file permissions

### No Data Displayed
- Wait for data to be collected (takes time)
- Verify symbols are correct (lowercase)
- Check backend logs for errors

### Performance Issues
- Reduce the number of symbols
- Use longer timeframes
- Limit the data range in queries

## Advanced Usage

### Custom Backtesting

```python
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.data_service import DataService

data_service = DataService()
analytics_service = AnalyticsService(data_service)

# Get data
df = data_service.get_ohlcv('btcusdt', timeframe='1h')

# Calculate metrics
zscore = analytics_service.calculate_zscore(df['close'], window=20)

# Simple mean reversion strategy
signals = (zscore > 2).astype(int) - (zscore < -2).astype(int)
```

### Uploading Historical Data

```python
import pandas as pd
from backend.app.models import OHLCV, SessionLocal

df = pd.read_csv('historical_data.csv')
db = SessionLocal()

for _, row in df.iterrows():
    ohlcv = OHLCV(
        id=f"{row['symbol']}_{row['timestamp']}_{row['timeframe']}",
        symbol=row['symbol'],
        timestamp=pd.to_datetime(row['timestamp']),
        timeframe=row['timeframe'],
        open=row['open'],
        high=row['high'],
        low=row['low'],
        close=row['close'],
        volume=row['volume'],
        trade_count=row.get('trade_count', 0)
    )
    db.add(ohlcv)

db.commit()
db.close()
```

## Performance Considerations

- **Data Storage**: SQLite suitable for < 1GB data; use PostgreSQL for larger datasets
- **Real-time Updates**: WebSocket updates every 500ms-1s
- **Analytics Computation**: Cached for 5-minute intervals
- **Frontend Refresh**: Updates every 2-5 seconds depending on timeframe

## Limitations

- **Data Retention**: Limited to available disk space (SQLite)
- **Symbols**: Limited to Binance Futures pairs
- **Timeframes**: Minimum 1-second resampling
- **Historical Data**: Limited by Binance API rate limits
- **Concurrent Users**: Single-instance deployment; use load balancer for scaling

## Future Enhancements

- [ ] PostgreSQL support for production
- [ ] Real-time alert notifications (email, SMS, webhook)
- [ ] Machine learning models for prediction
- [ ] Multi-exchange support
- [ ] Advanced portfolio analytics
- [ ] Risk management tools
- [ ] Backtesting engine with performance metrics
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] REST API authentication



## License

MIT License - See LICENSE file for details


