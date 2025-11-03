import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable, Any
import websockets
from datetime import datetime
import uuid
import pytz

from ..models import Trade, get_db
from ..config import BINANCE_WS_URL, DEFAULT_SYMBOLS

logger = logging.getLogger(__name__)

class BinanceWebSocketClient:
    def __init__(self, symbols: List[str] = None):
        self.symbols = symbols or DEFAULT_SYMBOLS
        self.websocket = None
        self.subscription_id = 1
        self.callbacks = {}
        self.running = False
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60
        
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback for a specific event type"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def _trigger_callbacks(self, event_type: str, data: Any):
        """Trigger all registered callbacks for an event type"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {e}")
    
    async def _connect(self):
        """Establish WebSocket connection to Binance"""
        try:
            # Create streams for all symbols: <symbol>@trade
            streams = [f"{symbol}@trade" for symbol in self.symbols]
            stream_url = f"{BINANCE_WS_URL}" + "/".join(streams)
            
            self.websocket = await websockets.connect(stream_url, ping_interval=30, ping_timeout=10)
            self._reconnect_delay = 1  # Reset reconnect delay on successful connection
            logger.info(f"Connected to Binance WebSocket API")
            self._trigger_callbacks("connection", {"status": "connected", "time": datetime.utcnow().isoformat()})
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise
    
    async def _reconnect(self):
        """Handle reconnection with exponential backoff"""
        while self.running:
            try:
                await self._connect()
                return  # Successfully reconnected
            except Exception as e:
                logger.error(f"Reconnection attempt failed: {e}")
                
            # Exponential backoff
            await asyncio.sleep(self._reconnect_delay)
            self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    async def _process_message(self, message: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Handle trade events
            if data.get('e') == 'trade':
                trade = self._parse_trade(data)
                self._trigger_callbacks("trade", trade)
                
                # Store in database
                await self._store_trade(trade)
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse message: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _parse_trade(self, data: dict) -> dict:
        """Parse trade data from WebSocket message"""
        return {
            'id': str(data.get('t')),  # Trade ID
            'symbol': data.get('s').lower(),  # Symbol
            'price': float(data.get('p')),  # Price
            'quantity': float(data.get('q')),  # Quantity
            'timestamp': datetime.fromtimestamp(data.get('T') / 1000, tz=pytz.UTC),  # Trade time
            'is_buyer_maker': data.get('m'),  # Is the buyer the market maker?
            'event_time': datetime.fromtimestamp(data.get('E') / 1000, tz=pytz.UTC),  # Event time
        }
    
    async def _store_trade(self, trade_data: dict):
        """Store trade data in the database"""
        from sqlalchemy.orm import Session
        from sqlalchemy.exc import IntegrityError
        
        db = next(get_db())
        try:
            trade = Trade(
                id=trade_data['id'],
                symbol=trade_data['symbol'],
                price=trade_data['price'],
                quantity=trade_data['quantity'],
                timestamp=trade_data['timestamp']
            )
            db.add(trade)
            db.commit()
        except IntegrityError:
            db.rollback()
            # Trade already exists, ignore
            pass
        except Exception as e:
            logger.error(f"Error storing trade: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _listen(self):
        """Listen for incoming messages"""
        while self.running:
            try:
                if not self.websocket or self.websocket.closed:
                    await self._reconnect()
                    
                message = await asyncio.wait_for(self.websocket.recv(), timeout=30)
                await self._process_message(message)
                
            except asyncio.TimeoutError:
                # No data received for timeout period, send ping
                if self.websocket and not self.websocket.closed:
                    await self.websocket.ping()
                continue
                
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                await asyncio.sleep(min(5, self._reconnect_delay))
                
            except Exception as e:
                logger.error(f"Error in WebSocket listener: {e}")
                await asyncio.sleep(min(5, self._reconnect_delay))
    
    async def start(self):
        """Start the WebSocket client"""
        if self.running:
            logger.warning("WebSocket client is already running")
            return
            
        self.running = True
        await self._connect()
        asyncio.create_task(self._listen())
        logger.info("WebSocket client started")
    
    async def stop(self):
        """Stop the WebSocket client"""
        self.running = False
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        logger.info("WebSocket client stopped")
