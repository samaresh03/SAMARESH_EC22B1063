import logging
import pandas as pd
import io
from typing import Dict, List, Optional
from datetime import datetime
import pytz
from sqlalchemy.orm import Session

from ..models import OHLCV, get_db

logger = logging.getLogger(__name__)

class UploadService:
    """Service for handling OHLC data uploads"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or next(get_db())
    
    def upload_csv(self, file_content: bytes, filename: str) -> Dict:
        """
        Upload OHLC data from CSV file
        
        Expected CSV format:
        timestamp,symbol,timeframe,open,high,low,close,volume[,trade_count]
        
        Args:
            file_content: Raw file bytes
            filename: Name of the uploaded file
            
        Returns:
            Dictionary with upload results
        """
        try:
            # Read CSV
            df = pd.read_csv(io.BytesIO(file_content))
            
            # Validate required columns
            required_cols = ['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                return {
                    'success': False,
                    'error': f"Missing required columns: {', '.join(missing_cols)}",
                    'records_inserted': 0
                }
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Ensure timezone awareness
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            else:
                df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
            
            # Convert symbol to lowercase
            df['symbol'] = df['symbol'].str.lower()
            
            # Add trade_count if not present
            if 'trade_count' not in df.columns:
                df['trade_count'] = 0
            
            # Prepare records for insertion
            records = []
            for _, row in df.iterrows():
                record_id = f"{row['symbol']}_{int(row['timestamp'].timestamp())}_{row['timeframe']}"
                
                record = {
                    'id': record_id,
                    'symbol': row['symbol'],
                    'timestamp': row['timestamp'],
                    'timeframe': row['timeframe'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']),
                    'trade_count': float(row.get('trade_count', 0))
                }
                records.append(record)
            
            # Bulk insert
            if records:
                self.db.bulk_insert_mappings(OHLCV, records)
                self.db.commit()
                
                logger.info(f"Successfully uploaded {len(records)} OHLCV records from {filename}")
                
                return {
                    'success': True,
                    'message': f"Successfully uploaded {len(records)} OHLCV records",
                    'records_inserted': len(records),
                    'symbols': df['symbol'].unique().tolist(),
                    'timeframes': df['timeframe'].unique().tolist()
                }
            else:
                return {
                    'success': False,
                    'error': 'No valid records found in the file',
                    'records_inserted': 0
                }
            
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error: {e}")
            return {
                'success': False,
                'error': f"Failed to parse CSV: {str(e)}",
                'records_inserted': 0
            }
        except Exception as e:
            logger.error(f"Error uploading OHLC data: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': f"Upload failed: {str(e)}",
                'records_inserted': 0
            }
    
    def upload_ndjson(self, file_content: bytes, filename: str) -> Dict:
        """
        Upload tick data from NDJSON file (from browser collector)
        
        Expected format (one JSON object per line):
        {"symbol": "btcusdt", "ts": "2023-...", "price": 123.45, "size": 0.5}
        
        Args:
            file_content: Raw file bytes
            filename: Name of the uploaded file
            
        Returns:
            Dictionary with upload results
        """
        try:
            import json
            from ..models import Trade
            
            lines = file_content.decode('utf-8').strip().split('\n')
            records = []
            
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    data = json.loads(line)
                    
                    # Parse timestamp
                    ts = pd.to_datetime(data.get('ts'))
                    if ts.tz is None:
                        ts = ts.tz_localize('UTC')
                    
                    record = {
                        'id': f"{data.get('symbol')}_{int(ts.timestamp())}_{data.get('price')}",
                        'symbol': data.get('symbol', '').lower(),
                        'price': float(data.get('price', 0)),
                        'quantity': float(data.get('size', 0)),
                        'timestamp': ts
                    }
                    records.append(record)
                    
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid line: {line[:100]}... Error: {e}")
                    continue
            
            # Bulk insert trades
            if records:
                self.db.bulk_insert_mappings(Trade, records)
                self.db.commit()
                
                logger.info(f"Successfully uploaded {len(records)} tick records from {filename}")
                
                return {
                    'success': True,
                    'message': f"Successfully uploaded {len(records)} tick records",
                    'records_inserted': len(records),
                    'symbols': list(set([r['symbol'] for r in records]))
                }
            else:
                return {
                    'success': False,
                    'error': 'No valid records found in the file',
                    'records_inserted': 0
                }
            
        except Exception as e:
            logger.error(f"Error uploading NDJSON data: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': f"Upload failed: {str(e)}",
                'records_inserted': 0
            }
    
    def get_upload_template(self) -> str:
        """Get a CSV template for OHLC data upload"""
        template = """timestamp,symbol,timeframe,open,high,low,close,volume,trade_count
2023-01-01T00:00:00Z,btcusdt,1m,30000.00,30100.00,29900.00,30050.00,100.5,50
2023-01-01T00:01:00Z,btcusdt,1m,30050.00,30150.00,30000.00,30100.00,95.3,48
2023-01-01T00:02:00Z,btcusdt,1m,30100.00,30200.00,30050.00,30150.00,102.1,52"""
        return template
