import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/trading_data.db")

# Binance WebSocket configuration
BINANCE_WS_URL = "wss://fstream.binance.com/ws/"
DEFAULT_SYMBOLS = ["btcusdt", "ethusdt"]

# API configuration
API_PREFIX = "/api"
API_V1_PREFIX = f"{API_PREFIX}/v1"

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": DATA_DIR / "app.log",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Analytics configuration
ANALYTICS_CONFIG = {
    "default_timeframe": "1m",
    "supported_timeframes": ["1s", "1m", "5m", "15m", "1h", "4h", "1d"],
    "zscore_window": 20,
    "correlation_window": 30,
    "adf_max_lag": 5,
}
