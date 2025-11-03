import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional, Tuple
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt", "solusdt", "xrpusdt"]
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
WINDOW_SIZES = [5, 10, 20, 50, 100, 200]

# Set page config
st.set_page_config(
    page_title="Quant Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .stSelectbox, .stSlider, .stNumberInput {
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #0E1117;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #2D3748;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #4299E1;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #A0AEC0;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 1000) -> pd.DataFrame:
    """Fetch OHLCV data from the API"""
    try:
        url = f"{API_BASE_URL}/ohlcv"
        params = {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": limit
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data["data"]:
            return pd.DataFrame()
            
        df = pd.DataFrame(data["data"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        return df
    except Exception as e:
        st.error(f"Error fetching OHLCV data: {e}")
        return pd.DataFrame()

def fetch_price_stats(symbol: str, timeframe: str) -> Optional[Dict]:
    """Fetch price statistics from the API"""
    try:
        url = f"{API_BASE_URL}/analytics/price-stats"
        params = {"symbol": symbol, "timeframe": timeframe}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching price stats: {e}")
        return None

def fetch_pair_metrics(symbol1: str, symbol2: str, timeframe: str, window: int) -> Optional[Dict]:
    """Fetch pair trading metrics from the API"""
    try:
        url = f"{API_BASE_URL}/analytics/pair-metrics"
        params = {
            "symbol1": symbol1,
            "symbol2": symbol2,
            "timeframe": timeframe,
            "window": window
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching pair metrics: {e}")
        return None

def plot_ohlcv(df: pd.DataFrame, symbol: str):
    """Plot OHLCV data with volume"""
    if df.empty:
        return None
        
    fig = make_subplots(
        rows=2, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f"{symbol.upper()} Price", "Volume")
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="OHLC"
        ),
        row=1, col=1
    )
    
    # Volume
    colors = ['green' if row['close'] >= row['open'] else 'red' 
              for _, row in df.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['volume'],
            name="Volume",
            marker_color=colors,
            opacity=0.5
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10),
        template="plotly_dark"
    )
    
    # Update y-axes
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig

def plot_pair_analysis(data: Dict):
    """Plot pair trading analysis"""
    if not data or not data.get("pair_metrics"):
        return None
        
    metrics = data["pair_metrics"]
    timestamps = pd.to_datetime(metrics["timestamps"])
    
    # Create subplots
    fig = make_subplots(
        rows=3, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.4, 0.3, 0.3],
        subplot_titles=(
            f"{data['symbol1'].upper()} vs {data['symbol2'].upper()} Price Ratio",
            "Z-Score of Spread",
            "Rolling Correlation"
        )
    )
    
    # Price ratio
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=metrics["spread"],
            name="Price Ratio",
            line=dict(color="#4299E1")
        ),
        row=1, col=1
    )
    
    # Z-score
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=metrics["zscore"],
            name="Z-Score",
            line=dict(color="#48BB78")
        ),
        row=2, col=1
    )
    
    # Add mean reversion bands
    fig.add_hline(
        y=2, 
        line_dash="dash", 
        line_color="red",
        row=2, 
        col=1,
        annotation_text="Overbought",
        annotation_position="top right"
    )
    fig.add_hline(
        y=-2, 
        line_dash="dash", 
        line_color="green",
        row=2, 
        col=1,
        annotation_text="Oversold",
        annotation_position="bottom right"
    )
    
    # Rolling correlation
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=metrics["rolling_correlation"],
            name="Rolling Correlation",
            line=dict(color="#9F7AEA")
        ),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=1000,
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10),
        template="plotly_dark",
        hovermode="x unified"
    )
    
    # Update y-axes
    fig.update_yaxes(title_text="Price Ratio", row=1, col=1)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1)
    fig.update_yaxes(title_text="Correlation", row=3, col=1)
    
    return fig

def display_metrics(stats: Dict, symbol: str):
    """Display price metrics in a grid"""
    if not stats or not stats.get("stats"):
        return
        
    metrics = stats["stats"]
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"{metrics.get('current', 0):.2f}")
        st.metric("24h High", f"{metrics.get('high', 0):.2f}")
        
    with col2:
        st.metric("24h Low", f"{metrics.get('low', 0):.2f}")
        st.metric("24h Volume", f"{metrics.get('volume', 0):.2f}")
        
    with col3:
        st.metric("24h Change", f"{metrics.get('change_24h', 0):.2%}")
        st.metric("24h Volatility", f"{metrics.get('volatility_24h', 0):.2%}")
        
    with col4:
        st.metric("RSI (14)", f"{metrics.get('rsi', 0):.2f}")
        st.metric("ATR (14)", f"{metrics.get('atr', 0):.2f}")

# Main app
def main():
    st.title("📊 Quant Trading Dashboard")
    
    # Sidebar
    st.sidebar.title("Settings")
    
    # Symbol selection
    selected_symbols = st.sidebar.multiselect(
        "Select Symbols",
        options=DEFAULT_SYMBOLS,
        default=DEFAULT_SYMBOLS[:2],
        max_selections=2
    )
    
    # Timeframe selection
    selected_timeframe = st.sidebar.selectbox(
        "Select Timeframe",
        options=TIMEFRAMES,
        index=1  # Default to 5m
    )
    
    # Window size for indicators
    window_size = st.sidebar.select_slider(
        "Window Size for Indicators",
        options=WINDOW_SIZES,
        value=20
    )
    
    # Check if we have at least one symbol selected
    if not selected_symbols:
        st.warning("Please select at least one symbol from the sidebar.")
        return
    
    # Single symbol view
    if len(selected_symbols) == 1:
        symbol = selected_symbols[0]
        
        # Fetch data
        with st.spinner(f"Loading {symbol.upper()} data..."):
            df = fetch_ohlcv(symbol, selected_timeframe)
            stats = fetch_price_stats(symbol, selected_timeframe)
        
        # Display metrics
        st.subheader(f"{symbol.upper()} Metrics")
        display_metrics(stats, symbol)
        
        # Display chart
        st.subheader(f"{symbol.upper()} Price Chart")
        fig = plot_ohlcv(df, symbol)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for the selected symbol and timeframe.")
    
    # Pair trading view
    elif len(selected_symbols) == 2:
        symbol1, symbol2 = selected_symbols
        
        # Fetch data
        with st.spinner(f"Analyzing {symbol1.upper()}/{symbol2.upper()} pair..."):
            df1 = fetch_ohlcv(symbol1, selected_timeframe)
            df2 = fetch_ohlcv(symbol2, selected_timeframe)
            pair_metrics = fetch_pair_metrics(symbol1, symbol2, selected_timeframe, window_size)
        
        # Display pair analysis
        st.subheader(f"{symbol1.upper()}/{symbol2.upper()} Pair Analysis")
        
        # Show correlation and cointegration results
        if pair_metrics and "pair_metrics" in pair_metrics:
            pm = pair_metrics["pair_metrics"]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current Z-Score", 
                         f"{pm.get('zscore', [0])[-1]:.2f}",
                         delta=None,
                         delta_color="normal")
            
            with col2:
                corr = pm.get('rolling_correlation', [0])[-1] if 'rolling_correlation' in pm else 0
                st.metric(
                    "Current Correlation",
                    f"{corr:.2f}",
                    delta=None,
                    delta_color="normal"
                )
                
            with col3:
                if 'cointegration' in pm and pm['cointegration'].get('is_cointegrated', False):
                    st.success("Cointegrated Pair")
                else:
                    st.warning("Not Cointegrated")
        
        # Display charts
        tab1, tab2 = st.tabs(["Pair Analysis", "Individual Charts"])
        
        with tab1:
            fig = plot_pair_analysis(pair_metrics)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Could not generate pair analysis. Please check the data.")
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"{symbol1.upper()} Price")
                fig1 = plot_ohlcv(df1, symbol1)
                if fig1:
                    st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                st.subheader(f"{symbol2.upper()} Price")
                fig2 = plot_ohlcv(df2, symbol2)
                if fig2:
                    st.plotly_chart(fig2, use_container_width=True)
    
    # Add some space at the bottom
    st.markdown("---")
    st.caption("Quant Trading Dashboard v0.1.0 | Data provided by Binance")

if __name__ == "__main__":
    main()
