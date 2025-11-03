# Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Internet connection (for Binance WebSocket)

### Step 1: Install Dependencies (2 minutes)

```bash
# Navigate to project directory
cd quant-trading-dashboard

# Install all required packages
pip install -r requirements.txt
```

### Step 2: Initialize Database (1 minute)

```bash
# Create and initialize the database
cd backend
python -c "from app.models import init_db; init_db()"
cd ..
```

### Step 3: Start the Application (1 minute)

```bash
# Run the unified application starter
python app.py
```

This will:
- Start the FastAPI backend on http://localhost:8000
- Start the Streamlit frontend on http://localhost:8501
- Initialize WebSocket connection to Binance
- Begin collecting real-time trade data

### Step 4: Access the Dashboard (1 minute)

Open your browser and navigate to:
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/api/docs

## First Steps

### 1. View Real-Time Data
1. Open the dashboard at http://localhost:8501
2. Select a symbol from the sidebar (e.g., "btcusdt")
3. Choose a timeframe (e.g., "5m")
4. Wait for data to load (takes 30-60 seconds)
5. View the interactive price chart

### 2. Analyze a Pair
1. Select two symbols from the sidebar
2. View the pair analysis metrics:
   - **Z-Score**: Mean reversion signal
   - **Correlation**: Relationship between assets
   - **Cointegration**: Statistical relationship
3. Interpret the signals for trading opportunities

### 3. Create an Alert
1. Go to the API documentation: http://localhost:8000/api/docs
2. Find the "POST /api/v1/alerts" endpoint
3. Click "Try it out"
4. Fill in the parameters:
   - symbol: "btcusdt"
   - condition: "price_above"
   - threshold: 50000
5. Click "Execute"
6. The alert will be created and monitored

### 4. Upload Historical Data
1. Prepare a CSV file with columns: timestamp, symbol, timeframe, open, high, low, close, volume
2. Go to http://localhost:8000/api/docs
3. Find "POST /api/v1/upload/ohlcv"
4. Upload your CSV file
5. Data will be imported and available for analysis

## Common Tasks

### View API Documentation
```
http://localhost:8000/api/docs
```

### Export Data as CSV
1. Open dashboard
2. Select symbol and timeframe
3. Click "Export" button
4. CSV file will download

### Check Backend Logs
```bash
tail -f backend/data/app.log
```

### Stop the Application
```bash
# Press Ctrl+C in the terminal
# This will gracefully shut down both backend and frontend
```

## Troubleshooting

### No Data Appears
- **Wait longer**: Data collection takes 30-60 seconds
- **Check internet**: Verify Binance WebSocket is accessible
- **Check logs**: Look for errors in the console output

### Backend Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process using the port
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Frontend Won't Start
```bash
# Check if port 8501 is in use
lsof -i :8501  # macOS/Linux
netstat -ano | findstr :8501  # Windows

# Try running on a different port
streamlit run frontend/app.py --server.port 8502
```

### Database Errors
```bash
# Reinitialize the database
cd backend
rm data/trading_data.db
python -c "from app.models import init_db; init_db()"
cd ..
```

## Next Steps

### Explore Advanced Features
1. **Backtesting**: Implement a simple mean-reversion strategy
2. **Custom Alerts**: Create alerts based on technical indicators
3. **Data Analysis**: Export data and analyze in Jupyter notebooks
4. **Multiple Symbols**: Monitor multiple trading pairs simultaneously

### Customize the Application
1. **Add More Symbols**: Edit `DEFAULT_SYMBOLS` in `backend/app/config.py`
2. **Change Timeframes**: Modify `supported_timeframes` in config
3. **Adjust Indicators**: Edit window sizes and parameters
4. **Custom Analytics**: Add new metrics in `analytics_service.py`

### Deploy to Production
1. **Use PostgreSQL**: Replace SQLite with PostgreSQL
2. **Add Authentication**: Implement JWT-based auth
3. **Use Docker**: Containerize the application
4. **Deploy to Cloud**: Use AWS, GCP, or Azure
5. **Add Monitoring**: Set up logging and alerting

## API Quick Reference

### Get OHLCV Data
```bash
curl "http://localhost:8000/api/v1/ohlcv?symbol=btcusdt&timeframe=1m&limit=100"
```

### Get Price Statistics
```bash
curl "http://localhost:8000/api/v1/analytics/price-stats?symbol=btcusdt&timeframe=1m"
```

### Get Pair Metrics
```bash
curl "http://localhost:8000/api/v1/analytics/pair-metrics?symbol1=btcusdt&symbol2=ethusdt&timeframe=1m&window=20"
```

### Create an Alert
```bash
curl -X POST "http://localhost:8000/api/v1/alerts?symbol=btcusdt&condition=price_above&threshold=50000"
```

### Get All Alerts
```bash
curl "http://localhost:8000/api/v1/alerts"
```

### Export Data
```bash
curl "http://localhost:8000/api/v1/export/csv?symbol=btcusdt&timeframe=1m" -o btcusdt_data.csv
```

## Performance Tips

### For Faster Data Loading
1. Use longer timeframes (5m, 15m instead of 1m)
2. Limit the number of symbols
3. Use shorter date ranges
4. Increase the database query limit

### For Better Responsiveness
1. Close unused browser tabs
2. Reduce the number of concurrent charts
3. Use a faster internet connection
4. Run on a machine with more RAM

### For Accurate Analytics
1. Wait for sufficient data (at least 100 candles)
2. Use consistent timeframes
3. Verify calculations with external tools
4. Check for data gaps or anomalies

## Getting Help

### Documentation
- **README.md**: Comprehensive documentation
- **ARCHITECTURE.md**: System architecture details
- **API_USAGE.md**: AI usage transparency

### API Documentation
- Interactive Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Logs
- Backend logs: `backend/data/app.log`
- Console output: Check terminal where app.py was run

### Common Issues
See the **Troubleshooting** section in README.md

## Next: Advanced Usage

Once you're comfortable with the basics, explore:
1. Custom analytics in `analytics_service.py`
2. Alert callbacks and webhooks
3. Backtesting framework
4. Machine learning models
5. Multi-exchange support

Happy trading! 📊
