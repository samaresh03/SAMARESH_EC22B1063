from sqlalchemy import Column, String, Float, DateTime, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pytz
from .config import DATABASE_URL

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Trade(Base):
    """Model for storing raw trade data"""
    __tablename__ = "trades"
    
    id = Column(String, primary_key=True, index=True)  # Unique trade ID from exchange
    symbol = Column(String, index=True)  # Trading pair (e.g., 'btcusdt')
    price = Column(Float)  # Trade price
    quantity = Column(Float)  # Trade quantity
    timestamp = Column(DateTime(timezone=True), index=True)  # Trade timestamp from exchange
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # When record was created

    def __repr__(self):
        return f"<Trade(symbol={self.symbol}, price={self.price}, qty={self.quantity}, time={self.timestamp})>"

class OHLCV(Base):
    """Model for storing OHLCV (Open-High-Low-Close-Volume) data"""
    __tablename__ = "ohlcv"
    
    id = Column(String, primary_key=True, index=True)  # Format: {symbol}_{timestamp}_{timeframe}
    symbol = Column(String, index=True)  # Trading pair
    timestamp = Column(DateTime(timezone=True), index=True)  # Start of the time window
    timeframe = Column(String)  # e.g., '1m', '5m', '1h'
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    trade_count = Column(Float)  # Number of trades in this interval
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Analytics(Base):
    """Model for storing precomputed analytics"""
    __tablename__ = "analytics"
    
    id = Column(String, primary_key=True, index=True)  # Format: {symbols}_{metric}_{timestamp}
    symbols = Column(String, index=True)  # Single symbol or comma-separated for pairs
    metric = Column(String)  # e.g., 'zscore', 'correlation', 'spread'
    value = Column(Float)  # Computed metric value
    timestamp = Column(DateTime(timezone=True), index=True)  # Timestamp of the data point
    metadata_ = Column(String)  # JSON string with additional context
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Initialize the database
    init_db()
    print("Database tables created successfully.")
