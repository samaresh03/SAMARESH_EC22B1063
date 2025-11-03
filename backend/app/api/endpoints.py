from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import JSONResponse, Response
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import asyncio
import logging
import pandas as pd

from ...models import get_db, Trade, OHLCV
from ...services.websocket_service import BinanceWebSocketClient
from ...services.data_service import DataService
from ...services.analytics_service import AnalyticsService
from ...services.upload_service import UploadService
from ...services.alert_service import get_alert_service, AlertCondition
from ...config import DEFAULT_SYMBOLS, ANALYTICS_CONFIG

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

# Global WebSocket client
websocket_client = None

# Initialize WebSocket client
def init_websocket_client():
    global websocket_client
    if websocket_client is None:
        websocket_client = BinanceWebSocketClient()
        
        # Register callbacks
        websocket_client.register_callback("trade", lambda data: handle_new_trade(data))
        
        # Start WebSocket client in the background
        asyncio.create_task(start_websocket_client())

# Start WebSocket client
async def start_websocket_client():
    if websocket_client:
        await websocket_client.start()

# Handle new trade data
async def handle_new_trade(trade_data: dict):
    """Process and broadcast new trade data"""
    try:
        # Broadcast to all connected WebSocket clients
        await manager.broadcast({
            "type": "trade",
            "data": trade_data
        })
        
        # Here you could add additional processing, e.g., updating analytics
        
    except Exception as e:
        logger.error(f"Error handling new trade: {e}")

# Initialize WebSocket client on startup
@router.on_event("startup")
async def startup_event():
    init_websocket_client()

# Health check endpoint
@router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Trade endpoints
@router.get("/trades/latest")
async def get_latest_trades(
    symbol: str = "btcusdt",
    limit: int = 100,
    data_service: DataService = Depends(DataService)
):
    """Get latest trades for a symbol"""
    try:
        trades = data_service.get_latest_trades(symbol=symbol, limit=limit)
        return {"data": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Error getting latest trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# OHLCV endpoints
@router.get("/ohlcv")
async def get_ohlcv(
    symbol: str,
    timeframe: str = "1m",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    data_service: DataService = Depends(DataService)
):
    """Get OHLCV data for a symbol and timeframe"""
    try:
        if timeframe not in ANALYTICS_CONFIG["supported_timeframes"]:
            raise HTTPException(status_code=400, detail=f"Unsupported timeframe. Supported: {ANALYTICS_CONFIG['supported_timeframes']}")
        
        df = data_service.get_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        if df.empty:
            return {"data": [], "count": 0}
            
        # Convert DataFrame to list of dicts
        ohlcv_data = []
        for _, row in df.iterrows():
            ohlcv_data.append({
                "timestamp": row["timestamp"].isoformat(),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
                "trade_count": row.get("trade_count", 0)
            })
            
        return {"data": ohlcv_data, "count": len(ohlcv_data)}
        
    except Exception as e:
        logger.error(f"Error getting OHLCV data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@router.get("/analytics/price-stats")
async def get_price_stats(
    symbol: str,
    timeframe: str = "1m",
    window: int = 20,
    data_service: DataService = Depends(DataService),
    analytics_service: AnalyticsService = Depends(AnalyticsService)
):
    """Get price statistics for a symbol"""
    try:
        df = data_service.get_ohlcv(symbol=symbol, timeframe=timeframe)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol} {timeframe}")
            
        stats = analytics_service.calculate_price_stats(df["close"])
        
        return {"symbol": symbol, "timeframe": timeframe, "stats": stats}
        
    except Exception as e:
        logger.error(f"Error calculating price stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/pair-metrics")
async def get_pair_metrics(
    symbol1: str,
    symbol2: str,
    timeframe: str = "1m",
    window: int = 20,
    data_service: DataService = Depends(DataService),
    analytics_service: AnalyticsService = Depends(AnalyticsService)
):
    """Get pair trading metrics for two symbols"""
    try:
        df1 = data_service.get_ohlcv(symbol=symbol1, timeframe=timeframe)
        df2 = data_service.get_ohlcv(symbol=symbol2, timeframe=timeframe)
        
        if df1.empty or df2.empty:
            raise HTTPException(status_code=404, detail=f"No data found for one or both symbols")
            
        # Align the data
        aligned = pd.concat([
            df1["close"].rename(symbol1),
            df2["close"].rename(symbol2)
        ], axis=1).dropna()
        
        if aligned.empty:
            raise HTTPException(status_code=400, detail="No overlapping data between the two symbols")
            
        # Calculate metrics
        ols_result = analytics_service.calculate_ols_regression(
            y=aligned[symbol1],
            x=aligned[symbol2]
        )
        
        spread = analytics_service.calculate_spread(
            y=aligned[symbol1],
            x=aligned[symbol2],
            method="ratio"
        )
        
        zscore = analytics_service.calculate_zscore(spread, window=window)
        
        coint_result = analytics_service.calculate_cointegration(
            y=aligned[symbol1],
            x=aligned[symbol2]
        )
        
        rolling_corr = analytics_service.calculate_rolling_correlation(
            x=aligned[symbol1],
            y=aligned[symbol2],
            window=window
        )
        
        return {
            "symbol1": symbol1,
            "symbol2": symbol2,
            "timeframe": timeframe,
            "window": window,
            "ols_regression": ols_result,
            "spread": spread.dropna().tolist(),
            "zscore": zscore.dropna().tolist(),
            "cointegration": coint_result,
            "rolling_correlation": rolling_corr.dropna().tolist(),
            "timestamps": aligned.index.astype(str).tolist()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating pair metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time data
@router.websocket("/ws/ticks")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await asyncio.sleep(10)
            await websocket.send_json({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Alert endpoints
@router.post("/alerts")
async def create_alert(
    symbol: str,
    condition: str,
    threshold: float,
    timeframe: str = "1m"
):
    """Create a new price alert"""
    # TODO: Implement alert storage and checking
    return {"status": "success", "message": "Alert created successfully"}

@router.get("/alerts")
async def get_alerts():
    """Get all active alerts"""
    # TODO: Implement fetching alerts from storage
    return {"alerts": []}

# Data export endpoint
@router.get("/export/csv")
async def export_data(
    symbol: str,
    timeframe: str = "1m",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    data_service: DataService = Depends(DataService)
):
    """Export data as CSV"""
    try:
        df = data_service.get_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the given parameters")
            
        # Convert to CSV
        csv_data = df.to_csv(index=False)
        
        # Create response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={symbol}_{timeframe}_{datetime.utcnow().date()}.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Upload endpoints
@router.post("/upload/ohlcv")
async def upload_ohlcv(
    file: UploadFile = File(...),
    upload_service: UploadService = Depends(UploadService)
):
    """Upload OHLCV data from CSV file"""
    try:
        # Read file content
        content = await file.read()
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Upload data
        result = upload_service.upload_csv(content, file.filename)
        
        if result['success']:
            return {"status": "success", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading OHLCV data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/ticks")
async def upload_ticks(
    file: UploadFile = File(...),
    upload_service: UploadService = Depends(UploadService)
):
    """Upload tick data from NDJSON file"""
    try:
        # Read file content
        content = await file.read()
        
        # Validate file type
        if not file.filename.endswith('.ndjson'):
            raise HTTPException(status_code=400, detail="Only NDJSON files are supported")
        
        # Upload data
        result = upload_service.upload_ndjson(content, file.filename)
        
        if result['success']:
            return {"status": "success", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading tick data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upload/template")
async def get_upload_template(upload_service: UploadService = Depends(UploadService)):
    """Get CSV template for OHLCV data upload"""
    template = upload_service.get_upload_template()
    return Response(
        content=template,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ohlcv_template.csv"}
    )

# Alert endpoints
@router.post("/alerts")
async def create_alert(
    symbol: str,
    condition: str,
    threshold: float,
    timeframe: str = "1m",
    name: str = None
):
    """Create a new alert"""
    try:
        alert_service = get_alert_service()
        
        # Validate condition
        try:
            alert_condition = AlertCondition(condition)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid condition. Supported: {[c.value for c in AlertCondition]}"
            )
        
        alert = alert_service.create_alert(
            symbol=symbol,
            condition=alert_condition,
            threshold=threshold,
            timeframe=timeframe,
            name=name
        )
        
        return {"status": "success", "alert": alert.to_dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts(symbol: str = None, status: str = None):
    """Get all alerts, optionally filtered by symbol and/or status"""
    try:
        alert_service = get_alert_service()
        
        alerts = alert_service.get_alerts(symbol=symbol)
        
        if status:
            alerts = [a for a in alerts if a.status.value == status]
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "count": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str):
    """Get a specific alert"""
    try:
        alert_service = get_alert_service()
        alert = alert_service.get_alert(alert_id)
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"alert": alert.to_dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert"""
    try:
        alert_service = get_alert_service()
        
        if not alert_service.delete_alert(alert_id):
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"status": "success", "message": "Alert deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/reset")
async def reset_alert(alert_id: str):
    """Reset an alert to active state"""
    try:
        alert_service = get_alert_service()
        
        if not alert_service.reset_alert(alert_id):
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = alert_service.get_alert(alert_id)
        return {"status": "success", "alert": alert.to_dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/deactivate")
async def deactivate_alert(alert_id: str):
    """Deactivate an alert"""
    try:
        alert_service = get_alert_service()
        
        if not alert_service.deactivate_alert(alert_id):
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = alert_service.get_alert(alert_id)
        return {"status": "success", "alert": alert.to_dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/activate")
async def activate_alert(alert_id: str):
    """Activate an alert"""
    try:
        alert_service = get_alert_service()
        
        if not alert_service.activate_alert(alert_id):
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = alert_service.get_alert(alert_id)
        return {"status": "success", "alert": alert.to_dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))
