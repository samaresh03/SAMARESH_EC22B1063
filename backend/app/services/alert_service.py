import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
import pytz
from enum import Enum

logger = logging.getLogger(__name__)

class AlertCondition(str, Enum):
    """Alert condition types"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    ZSCORE_ABOVE = "zscore_above"
    ZSCORE_BELOW = "zscore_below"
    CORRELATION_ABOVE = "correlation_above"
    CORRELATION_BELOW = "correlation_below"
    VOLUME_ABOVE = "volume_above"
    VOLUME_BELOW = "volume_below"

class AlertStatus(str, Enum):
    """Alert status types"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    INACTIVE = "inactive"

class Alert:
    """Alert object"""
    
    def __init__(
        self,
        alert_id: str,
        symbol: str,
        condition: AlertCondition,
        threshold: float,
        timeframe: str = "1m",
        name: str = None
    ):
        self.alert_id = alert_id
        self.symbol = symbol
        self.condition = condition
        self.threshold = threshold
        self.timeframe = timeframe
        self.name = name or f"{symbol}_{condition}_{threshold}"
        self.status = AlertStatus.ACTIVE
        self.created_at = datetime.now(tz=pytz.UTC)
        self.triggered_at = None
        self.trigger_count = 0
        self.last_value = None
    
    def check(self, current_value: float) -> bool:
        """Check if alert condition is met"""
        self.last_value = current_value
        
        if self.condition == AlertCondition.PRICE_ABOVE:
            return current_value > self.threshold
        elif self.condition == AlertCondition.PRICE_BELOW:
            return current_value < self.threshold
        elif self.condition == AlertCondition.ZSCORE_ABOVE:
            return current_value > self.threshold
        elif self.condition == AlertCondition.ZSCORE_BELOW:
            return current_value < self.threshold
        elif self.condition == AlertCondition.CORRELATION_ABOVE:
            return current_value > self.threshold
        elif self.condition == AlertCondition.CORRELATION_BELOW:
            return current_value < self.threshold
        elif self.condition == AlertCondition.VOLUME_ABOVE:
            return current_value > self.threshold
        elif self.condition == AlertCondition.VOLUME_BELOW:
            return current_value < self.threshold
        
        return False
    
    def trigger(self):
        """Mark alert as triggered"""
        self.status = AlertStatus.TRIGGERED
        self.triggered_at = datetime.now(tz=pytz.UTC)
        self.trigger_count += 1
    
    def reset(self):
        """Reset alert to active state"""
        self.status = AlertStatus.ACTIVE
        self.triggered_at = None
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'symbol': self.symbol,
            'condition': self.condition.value,
            'threshold': self.threshold,
            'timeframe': self.timeframe,
            'name': self.name,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'trigger_count': self.trigger_count,
            'last_value': self.last_value
        }

class AlertService:
    """Service for managing alerts"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.callbacks: List[Callable] = []
    
    def create_alert(
        self,
        symbol: str,
        condition: AlertCondition,
        threshold: float,
        timeframe: str = "1m",
        name: str = None
    ) -> Alert:
        """Create a new alert"""
        alert_id = f"{symbol}_{condition.value}_{threshold}_{datetime.now().timestamp()}"
        
        alert = Alert(
            alert_id=alert_id,
            symbol=symbol,
            condition=condition,
            threshold=threshold,
            timeframe=timeframe,
            name=name
        )
        
        self.alerts[alert_id] = alert
        logger.info(f"Created alert: {alert.name}")
        
        return alert
    
    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Deleted alert: {alert_id}")
            return True
        return False
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID"""
        return self.alerts.get(alert_id)
    
    def get_alerts(self, symbol: str = None, status: AlertStatus = None) -> List[Alert]:
        """Get alerts filtered by symbol and/or status"""
        alerts = list(self.alerts.values())
        
        if symbol:
            alerts = [a for a in alerts if a.symbol == symbol]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        return alerts
    
    def check_alerts(self, symbol: str, current_value: float) -> List[Alert]:
        """Check all alerts for a symbol and return triggered ones"""
        triggered = []
        
        for alert in self.get_alerts(symbol=symbol, status=AlertStatus.ACTIVE):
            if alert.check(current_value):
                alert.trigger()
                triggered.append(alert)
                
                # Call registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")
        
        return triggered
    
    def register_callback(self, callback: Callable):
        """Register a callback to be called when an alert is triggered"""
        self.callbacks.append(callback)
    
    def get_all_alerts_dict(self) -> List[Dict]:
        """Get all alerts as dictionaries"""
        return [alert.to_dict() for alert in self.alerts.values()]
    
    def reset_alert(self, alert_id: str) -> bool:
        """Reset an alert to active state"""
        alert = self.get_alert(alert_id)
        if alert:
            alert.reset()
            return True
        return False
    
    def deactivate_alert(self, alert_id: str) -> bool:
        """Deactivate an alert"""
        alert = self.get_alert(alert_id)
        if alert:
            alert.status = AlertStatus.INACTIVE
            return True
        return False
    
    def activate_alert(self, alert_id: str) -> bool:
        """Activate an alert"""
        alert = self.get_alert(alert_id)
        if alert:
            alert.status = AlertStatus.ACTIVE
            return True
        return False

# Global alert service instance
_alert_service = None

def get_alert_service() -> AlertService:
    """Get or create the global alert service"""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
