"""
Simulation Monitor - Metrics collection and alert system.

Implements comprehensive monitoring, metrics collection,
and alerting for quantum network simulations.
"""

from __future__ import annotations

import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Deque
from enum import Enum
from collections import deque
import statistics
import json

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of monitoring alerts."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ATTACK_DETECTED = "attack_detected"
    NODE_FAILURE = "node_failure"
    LINK_FAILURE = "link_failure"
    DECOHERENCE_WARNING = "decoherence_warning"
    SECURITY_BREACH = "security_breach"


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Alert:
    """
    Monitoring alert.
    
    Represents a condition that requires attention
    during simulation.
    """
    alert_id: str = ""
    alert_type: AlertType = AlertType.INFO
    severity: AlertSeverity = AlertSeverity.LOW
    source: str = ""
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[float] = None
    
    def acknowledge(self) -> None:
        """Mark alert as acknowledged."""
        self.acknowledged = True
    
    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.resolved = True
        self.resolved_at = time.time()
    
    @property
    def age(self) -> float:
        """Time since alert was created."""
        return time.time() - self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.name,
            "source": self.source,
            "message": self.message,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "age": self.age,
            "data": self.data,
        }


@dataclass
class MetricSample:
    """Single metric sample."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricWindow:
    """Rolling window for metric statistics."""
    samples: Deque[MetricSample] = field(default_factory=lambda: deque(maxlen=1000))
    window_size: int = 100
    
    def add(self, sample: MetricSample) -> None:
        """Add sample to window."""
        self.samples.append(sample)
    
    @property
    def count(self) -> int:
        """Number of samples in window."""
        return len(self.samples)
    
    @property
    def latest(self) -> Optional[float]:
        """Latest sample value."""
        if not self.samples:
            return None
        return self.samples[-1].value
    
    @property
    def mean(self) -> float:
        """Mean of values in window."""
        if not self.samples:
            return 0.0
        return statistics.mean(s.value for s in self.samples)
    
    @property
    def stdev(self) -> float:
        """Standard deviation of values in window."""
        if len(self.samples) < 2:
            return 0.0
        return statistics.stdev(s.value for s in self.samples)
    
    @property
    def min(self) -> Optional[float]:
        """Minimum value in window."""
        if not self.samples:
            return None
        return min(s.value for s in self.samples)
    
    @property
    def max(self) -> Optional[float]:
        """Maximum value in window."""
        if not self.samples:
            return None
        return max(s.value for s in self.samples)


class SimulationMonitor:
    """
    Comprehensive simulation monitoring system.
    
    Collects metrics, generates alerts, and provides
    real-time visibility into simulation state.
    
    Features:
    - Real-time metrics collection
    - Rolling window statistics
    - Alert generation and management
    - Event logging
    - Webhook notifications
    """
    
    def __init__(
        self,
        history_size: int = 10000,
        alert_history_size: int = 1000,
        log_level: int = logging.INFO
    ):
        """
        Initialize monitor.
        
        Args:
            history_size: Number of metric samples to keep
            alert_history_size: Number of alerts to keep
            log_level: Logging level
        """
        self._metrics: Dict[str, MetricWindow] = {}
        self._alerts: Dict[str, Alert] = {}
        self._alert_order: List[str] = []
        self._event_log: Deque[Dict[str, Any]] = deque(maxlen=1000)
        self._lock = threading.RLock()
        self._callbacks: Dict[str, List[Callable]] = {
            'alert': [],
            'metric': [],
            'threshold_exceeded': [],
        }
        self._thresholds: Dict[str, Dict[str, float]] = {}
        self._webhooks: List[str] = []
        self._alert_counter = 0
        self._start_time = time.time()
    
    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[float] = None
    ) -> None:
        """
        Record a metric sample.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional metric tags
            timestamp: Optional timestamp (uses current time if None)
        """
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = MetricWindow()
            
            sample = MetricSample(
                name=name,
                value=value,
                timestamp=timestamp or time.time(),
                tags=tags or {}
            )
            
            self._metrics[name].add(sample)
            
            self._check_thresholds(name, value)
            
            for callback in self._callbacks.get('metric', []):
                try:
                    callback(name, value, tags)
                except Exception as e:
                    logger.error(f"Metric callback error: {e}")
    
    def record_metrics(self, metrics: Dict[str, Any]) -> None:
        """Record multiple metrics at once."""
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                self.record_metric(name, float(value))
    
    def _check_thresholds(self, metric_name: str, value: float) -> None:
        """Check if metric exceeds thresholds."""
        if metric_name not in self._thresholds:
            return
        
        thresholds = self._thresholds[metric_name]
        
        if 'max' in thresholds and value > thresholds['max']:
            self.create_alert(
                AlertType.WARNING,
                severity=AlertSeverity.HIGH,
                source=metric_name,
                message=f"{metric_name} exceeded maximum threshold: {value:.2f} > {thresholds['max']:.2f}"
            )
            
            for callback in self._callbacks.get('threshold_exceeded', []):
                try:
                    callback(metric_name, value, 'max', thresholds['max'])
                except Exception as e:
                    logger.error(f"Threshold callback error: {e}")
        
        if 'min' in thresholds and value < thresholds['min']:
            self.create_alert(
                AlertType.WARNING,
                severity=AlertSeverity.HIGH,
                source=metric_name,
                message=f"{metric_name} below minimum threshold: {value:.2f} < {thresholds['min']:.2f}"
            )
    
    def set_threshold(
        self,
        metric_name: str,
        max_value: Optional[float] = None,
        min_value: Optional[float] = None
    ) -> None:
        """Set threshold for metric monitoring."""
        self._thresholds[metric_name] = {}
        if max_value is not None:
            self._thresholds[metric_name]['max'] = max_value
        if min_value is not None:
            self._thresholds[metric_name]['min'] = min_value
    
    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity = AlertSeverity.LOW,
        source: str = "",
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
        auto_resolve: bool = False
    ) -> Alert:
        """
        Create and register new alert.
        
        Args:
            alert_type: Type of alert
            severity: Alert severity
            source: Source of alert
            message: Alert message
            data: Additional alert data
            auto_resolve: Whether to auto-resolve
            
        Returns:
            Created alert
        """
        with self._lock:
            self._alert_counter += 1
            alert_id = f"alert_{self._alert_counter}"
            
            alert = Alert(
                alert_id=alert_id,
                alert_type=alert_type,
                severity=severity,
                source=source,
                message=message,
                data=data or {}
            )
            
            self._alerts[alert_id] = alert
            self._alert_order.append(alert_id)
            
            if len(self._alert_order) > 1000:
                old_id = self._alert_order.pop(0)
                self._alerts.pop(old_id, None)
            
            for callback in self._callbacks.get('alert', []):
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")
            
            logger.log(
                logging.WARNING if severity >= AlertSeverity.HIGH else logging.INFO,
                f"[{alert_type.value}] {message}"
            )
            
            return alert
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].acknowledge()
                return True
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].resolve()
                return True
            return False
    
    def log_event(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log simulation event."""
        event = {
            'type': event_type,
            'timestamp': time.time(),
            'elapsed': time.time() - self._start_time,
            'data': data or {}
        }
        self._event_log.append(event)
    
    def get_metric(
        self,
        name: str,
        stat: str = "latest"
    ) -> Optional[float]:
        """
        Get metric statistic.
        
        Args:
            name: Metric name
            stat: Statistic to retrieve (latest, mean, min, max, stdev)
            
        Returns:
            Metric value or None
        """
        with self._lock:
            if name not in self._metrics:
                return None
            
            window = self._metrics[name]
            return getattr(window, stat, None)
    
    def get_metric_history(
        self,
        name: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get metric history."""
        with self._lock:
            if name not in self._metrics:
                return []
            
            samples = list(self._metrics[name].samples)[-limit:]
            return [
                {
                    'value': s.value,
                    'timestamp': s.timestamp,
                    'tags': s.tags
                }
                for s in samples
            ]
    
    def get_active_alerts(
        self,
        alert_type: Optional[AlertType] = None,
        min_severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get active (unresolved) alerts."""
        with self._lock:
            alerts = [
                a for a in self._alerts.values()
                if not a.resolved
            ]
            
            if alert_type:
                alerts = [a for a in alerts if a.alert_type == alert_type]
            
            if min_severity:
                alerts = [a for a in alerts if a.severity.value >= min_severity.value]
            
            return sorted(alerts, key=lambda a: (-a.severity.value, -a.timestamp))
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts."""
        with self._lock:
            active = [a for a in self._alerts.values() if not a.resolved]
            critical = [a for a in active if a.severity == AlertSeverity.CRITICAL]
            
            return {
                "total": len(self._alerts),
                "active": len(active),
                "critical": len(critical),
                "by_type": {
                    at.value: len([a for a in active if a.alert_type == at])
                    for at in AlertType
                },
                "by_severity": {
                    s.name: len([a for a in active if a.severity == s])
                    for s in AlertSeverity
                }
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary."""
        with self._lock:
            return {
                "uptime": time.time() - self._start_time,
                "metrics_count": len(self._metrics),
                "alert_summary": self.get_alert_summary(),
                "latest_metrics": {
                    name: window.latest
                    for name, window in self._metrics.items()
                },
            }
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for monitoring events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize monitor state."""
        return {
            "metrics": {
                name: {
                    "count": window.count,
                    "latest": window.latest,
                    "mean": window.mean,
                    "min": window.min,
                    "max": window.max,
                }
                for name, window in self._metrics.items()
            },
            "alerts": self.get_alert_summary(),
            "events_logged": len(self._event_log),
        }
    
    def export_metrics(self, filepath: str) -> None:
        """Export metrics to JSON file."""
        with self._lock:
            data = {
                'export_time': time.time(),
                'metrics': {
                    name: [
                        {'value': s.value, 'timestamp': s.timestamp, 'tags': s.tags}
                        for s in window.samples
                    ]
                    for name, window in self._metrics.items()
                },
                'alerts': [a.to_dict() for a in self._alerts.values()],
                'events': list(self._event_log),
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def __repr__(self) -> str:
        return f"SimulationMonitor({len(self._metrics)} metrics, {len(self.get_active_alerts())} active alerts)"
