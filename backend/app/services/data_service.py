import logging
import json
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..models import Trade, OHLCV, Analytics, get_db
from ..config import ANALYTICS_CONFIG

logger = logging.getLogger(__name__)

class DataService:
    """Service for handling data operations including storage and retrieval"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or next(get_db())
        
    def get_latest_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get the most recent trades for a symbol"""
        try:
            trades = self.db.query(Trade)\
                .filter(Trade.symbol == symbol)\
                .order_by(Trade.timestamp.desc())\
                .limit(limit)\
                .all()
            return [self._trade_to_dict(t) for t in trades]
        except Exception as e:
            logger.error(f"Error getting latest trades: {e}")
            return []
    
    def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = '1m', 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Get OHLCV data for a symbol and timeframe
        
        Args:
            symbol: Trading pair symbol (e.g., 'btcusdt')
            timeframe: Timeframe string (e.g., '1m', '5m', '1h')
            start_time: Start time for the query
            end_time: End time for the query
            limit: Maximum number of records to return
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            query = self.db.query(OHLCV).filter(OHLCV.symbol == symbol, OHLCV.timeframe == timeframe)
            
            if start_time:
                if not start_time.tzinfo:
                    start_time = pytz.utc.localize(start_time)
                query = query.filter(OHLCV.timestamp >= start_time)
                
            if end_time:
                if not end_time.tzinfo:
                    end_time = pytz.utc.localize(end_time)
                query = query.filter(OHLCV.timestamp <= end_time)
                
            ohlcv_data = query.order_by(OHLCV.timestamp.desc()).limit(limit).all()
            
            if not ohlcv_data:
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': o.timestamp,
                'open': o.open,
                'high': o.high,
                'low': o.low,
                'close': o.close,
                'volume': o.volume,
                'trade_count': o.trade_count
            } for o in ohlcv_data])
            
            return df.sort_values('timestamp')
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data: {e}")
            return pd.DataFrame()
    
    def resample_trades_to_ohlcv(self, symbol: str, timeframe: str = '1m') -> bool:
        """
        Resample raw trades to OHLCV data for a specific timeframe
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string (e.g., '1m', '5m', '1h')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the latest OHLCV timestamp for this symbol and timeframe
            latest_ohlcv = self.db.query(func.max(OHLCV.timestamp))\
                .filter(and_(
                    OHLCV.symbol == symbol,
                    OHLCV.timeframe == timeframe
                )).scalar()
            
            # Get trades since the latest OHLCV record (or all if none exists)
            query = self.db.query(Trade).filter(Trade.symbol == symbol)
            if latest_ohlcv:
                query = query.filter(Trade.timestamp > latest_ohlcv)
            
            trades = query.order_by(Trade.timestamp).all()
            
            if not trades:
                logger.info(f"No new trades to resample for {symbol} {timeframe}")
                return True
                
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame([{
                'timestamp': t.timestamp,
                'price': t.price,
                'quantity': t.quantity
            } for t in trades])
            
            if df.empty:
                return True
                
            # Convert timeframe to pandas frequency
            freq_map = {
                '1s': '1S',
                '1m': '1T',
                '5m': '5T',
                '15m': '15T',
                '1h': '1H',
                '4h': '4H',
                '1d': '1D'
            }
            
            freq = freq_map.get(timeframe, '1T')
            
            # Resample to OHLCV
            df.set_index('timestamp', inplace=True)
            ohlcv = df['price'].resample(freq).ohlc()
            ohlcv['volume'] = df['quantity'].resample(freq).sum()
            ohlcv['trade_count'] = df['price'].resample(freq).count()
            
            # Remove any incomplete periods
            ohlcv = ohlcv.dropna()
            
            # Convert to database records
            ohlcv_records = []
            for ts, row in ohlcv.iterrows():
                record_id = f"{symbol}_{int(ts.timestamp())}_{timeframe}"
                ohlcv_records.append({
                    'id': record_id,
                    'symbol': symbol,
                    'timestamp': ts,
                    'timeframe': timeframe,
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume'],
                    'trade_count': row['trade_count']
                })
            
            # Bulk insert
            if ohlcv_records:
                self.db.bulk_insert_mappings(OHLCV, ohlcv_records)
                self.db.commit()
                logger.info(f"Resampled {len(ohlcv_records)} {timeframe} OHLCV records for {symbol}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error resampling trades to OHLCV: {e}")
            self.db.rollback()
            return False
    
    def get_analytics(
        self,
        symbols: List[str],
        metric: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Get precomputed analytics data
        
        Args:
            symbols: List of symbols (1 for single-asset metrics, 2 for pairs)
            metric: Metric name (e.g., 'zscore', 'correlation', 'spread')
            start_time: Start time for the query
            end_time: End time for the query
            limit: Maximum number of records to return
            
        Returns:
            DataFrame with analytics data
        """
        try:
            symbols_str = ",".join(sorted(symbols))
            
            query = self.db.query(Analytics).filter(
                Analytics.symbols == symbols_str,
                Analytics.metric == metric
            )
            
            if start_time:
                if not start_time.tzinfo:
                    start_time = pytz.utc.localize(start_time)
                query = query.filter(Analytics.timestamp >= start_time)
                
            if end_time:
                if not end_time.tzinfo:
                    end_time = pytz.utc.localize(end_time)
                query = query.filter(Analytics.timestamp <= end_time)
                
            analytics_data = query.order_by(Analytics.timestamp.desc()).limit(limit).all()
            
            if not analytics_data:
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': a.timestamp,
                'value': a.value,
                'metadata': a.metadata_
            } for a in analytics_data])
            
            return df.sort_values('timestamp')
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return pd.DataFrame()
    
    def save_analytics(
        self,
        symbols: List[str],
        metric: str,
        value: float,
        timestamp: datetime,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Save analytics data
        
        Args:
            symbols: List of symbols (1 for single-asset metrics, 2 for pairs)
            metric: Metric name
            value: Computed metric value
            timestamp: Timestamp of the data point
            metadata: Additional context as a dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            symbols_str = ",".join(sorted(symbols))
            record_id = f"{symbols_str}_{metric}_{int(timestamp.timestamp())}"
            
            record = Analytics(
                id=record_id,
                symbols=symbols_str,
                metric=metric,
                value=value,
                timestamp=timestamp,
                metadata_=json.dumps(metadata) if metadata else None
            )
            
            self.db.add(record)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving analytics data: {e}")
            self.db.rollback()
            return False
    
    def _trade_to_dict(self, trade: Trade) -> dict:
        """Convert Trade ORM object to dictionary"""
        return {
            'id': trade.id,
            'symbol': trade.symbol,
            'price': trade.price,
            'quantity': trade.quantity,
            'timestamp': trade.timestamp.isoformat(),
            'created_at': trade.created_at.isoformat() if trade.created_at else None
        }
