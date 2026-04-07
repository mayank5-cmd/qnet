"""
Traffic Predictor - AI-based traffic prediction for quantum networks.

Implements time series prediction and pattern recognition
for traffic forecasting and network optimization.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import deque
import statistics


class PredictionModel(Enum):
    """Available prediction models."""
    SIMPLE_MOVING_AVERAGE = "sma"
    EXPONENTIAL_SMOOTHING = "ema"
    LINEAR_REGRESSION = "linear"
    POLYNOMIAL = "polynomial"
    ARIMA = "arima"
    LSTM = "lstm"


@dataclass
class TrafficSample:
    """Traffic measurement sample."""
    timestamp: float
    packets: int
    qubits: int
    latency: float
    throughput: float
    errors: int = 0


@dataclass
class Prediction:
    """Traffic prediction result."""
    predicted_value: float
    confidence: float
    horizon: int
    model: PredictionModel
    timestamp: float
    lower_bound: float
    upper_bound: float


@dataclass
class TrafficPattern:
    """Recognized traffic pattern."""
    pattern_type: str
    description: str
    confidence: float
    period: Optional[float] = None
    peak_times: List[float] = field(default_factory=list)


class TrafficPredictor:
    """
    AI-based traffic prediction system.
    
    Predicts network traffic patterns to enable
    proactive resource allocation and optimization.
    
    Features:
    - Multiple prediction models
    - Traffic pattern recognition
    - Anomaly detection
    - Multi-step forecasting
    """
    
    def __init__(
        self,
        model: PredictionModel = PredictionModel.EXPONENTIAL_SMOOTHING,
        window_size: int = 100,
        forecast_horizon: int = 10
    ):
        """
        Initialize traffic predictor.
        
        Args:
            model: Primary prediction model
            window_size: Historical data window
            forecast_horizon: Steps to forecast
        """
        self.model = model
        self.window_size = window_size
        self.forecast_horizon = forecast_horizon
        
        self.samples: deque = deque(maxlen=window_size)
        self.predictions: deque = deque(maxlen=100)
        
        self.smoothing_factor = 0.3
        self.trend = 0.0
        self.baseline = 0.0
        
        self.anomaly_threshold = 2.5
        self.patterns: List[TrafficPattern] = []
    
    def add_sample(self, sample: TrafficSample) -> None:
        """Add traffic sample to history."""
        self.samples.append(sample)
        
        if len(self.samples) > 1:
            prev = self.samples[-2]
            
            if self.model == PredictionModel.EXPONENTIAL_SMOOTHING:
                alpha = self.smoothing_factor
                self.baseline = alpha * sample.packets + (1 - alpha) * self.baseline
                self.trend = alpha * (self.baseline - self.samples[-2].packets if len(self.samples) > 1 else 0) + (1 - alpha) * self.trend
    
    def predict_next(self) -> Prediction:
        """
        Predict next traffic value.
        
        Returns:
            Prediction for next time step
        """
        if not self.samples:
            return Prediction(
                predicted_value=0.0,
                confidence=0.0,
                horizon=1,
                model=self.model,
                timestamp=0.0,
                lower_bound=0.0,
                upper_bound=0.0
            )
        
        if self.model == PredictionModel.SIMPLE_MOVING_AVERAGE:
            predicted = self._sma_predict()
        elif self.model == PredictionModel.EXPONENTIAL_SMOOTHING:
            predicted = self._ema_predict()
        elif self.model == PredictionModel.LINEAR_REGRESSION:
            predicted = self._linear_predict()
        else:
            predicted = self._ema_predict()
        
        confidence = self._calculate_confidence()
        
        variance = self._calculate_variance()
        
        return Prediction(
            predicted_value=predicted,
            confidence=confidence,
            horizon=1,
            model=self.model,
            timestamp=self.samples[-1].timestamp if self.samples else 0.0,
            lower_bound=max(0, predicted - 2 * variance),
            upper_bound=predicted + 2 * variance
        )
    
    def predict_multi_step(self, steps: int) -> List[Prediction]:
        """
        Predict multiple steps ahead.
        
        Args:
            steps: Number of steps to forecast
            
        Returns:
            List of predictions
        """
        predictions = []
        current_baseline = self.baseline
        current_trend = self.trend
        
        for i in range(steps):
            if self.model == PredictionModel.EXPONENTIAL_SMOOTHING:
                predicted = current_baseline + (i + 1) * current_trend
            else:
                predicted = self._ema_predict() + (i + 1) * self.trend
            
            confidence = self._calculate_confidence() * (1 - 0.05 * i)
            
            predictions.append(Prediction(
                predicted_value=max(0, predicted),
                confidence=max(0, confidence),
                horizon=i + 1,
                model=self.model,
                timestamp=self.samples[-1].timestamp if self.samples else 0.0,
                lower_bound=max(0, predicted - 2 * (1 + 0.1 * i)),
                upper_bound=predicted + 2 * (1 + 0.1 * i)
            ))
        
        return predictions
    
    def _sma_predict(self) -> float:
        """Simple moving average prediction."""
        if len(self.samples) < 2:
            return self.samples[-1].packets if self.samples else 0.0
        
        recent = list(self.samples)[-self.window_size:]
        return sum(s.packets for s in recent) / len(recent)
    
    def _ema_predict(self) -> float:
        """Exponential moving average prediction."""
        if not self.samples:
            return 0.0
        
        return self.baseline + self.trend
    
    def _linear_predict(self) -> float:
        """Linear regression prediction."""
        if len(self.samples) < 2:
            return self.samples[-1].packets if self.samples else 0.0
        
        n = len(self.samples)
        x = list(range(n))
        y = [s.packets for s in self.samples]
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return y_mean
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        return slope * n + intercept
    
    def _calculate_confidence(self) -> float:
        """Calculate prediction confidence."""
        if len(self.samples) < 10:
            return 0.3
        
        variance = self._calculate_variance()
        cv = variance / max(1, self.baseline) if self.baseline > 0 else 1.0
        
        confidence = max(0, 1 - cv)
        
        return min(1.0, confidence)
    
    def _calculate_variance(self) -> float:
        """Calculate sample variance."""
        if len(self.samples) < 2:
            return 0.0
        
        values = [s.packets for s in self.samples]
        return statistics.variance(values) if len(values) > 1 else 0.0
    
    def detect_anomaly(self, sample: TrafficSample) -> Tuple[bool, float]:
        """
        Detect if sample is anomalous.
        
        Args:
            sample: Traffic sample to check
            
        Returns:
            Tuple of (is_anomaly, anomaly_score)
        """
        if len(self.samples) < 10:
            return False, 0.0
        
        recent = list(self.samples)[-20:]
        
        mean_packets = sum(s.packets for s in recent) / len(recent)
        std_packets = statistics.stdev([s.packets for s in recent]) if len(recent) > 1 else 1.0
        
        if std_packets == 0:
            std_packets = 1.0
        
        z_score = abs(sample.packets - mean_packets) / std_packets
        
        is_anomaly = z_score > self.anomaly_threshold
        anomaly_score = min(1.0, z_score / self.anomaly_threshold)
        
        return is_anomaly, anomaly_score
    
    def recognize_patterns(self) -> List[TrafficPattern]:
        """
        Recognize traffic patterns in historical data.
        
        Returns:
            List of detected patterns
        """
        if len(self.samples) < 50:
            return []
        
        self.patterns = []
        
        if self._is_periodic():
            pattern = TrafficPattern(
                pattern_type="periodic",
                description="Detected periodic traffic pattern",
                confidence=0.8,
                period=24.0
            )
            self.patterns.append(pattern)
        
        if self._is_bursty():
            pattern = TrafficPattern(
                pattern_type="bursty",
                description="Detected bursty traffic pattern",
                confidence=0.7
            )
            self.patterns.append(pattern)
        
        return self.patterns
    
    def _is_periodic(self) -> bool:
        """Check for periodic pattern."""
        if len(self.samples) < 100:
            return False
        
        values = [s.packets for s in list(self.samples)[-100:]]
        
        peaks = []
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                peaks.append(i)
        
        if len(peaks) < 2:
            return False
        
        intervals = [peaks[i+1] - peaks[i] for i in range(len(peaks) - 1)]
        if not intervals:
            return False
        
        interval_variance = statistics.variance(intervals) if len(intervals) > 1 else 0
        
        return interval_variance < 10
    
    def _is_bursty(self) -> bool:
        """Check for bursty pattern."""
        if len(self.samples) < 20:
            return False
        
        values = [s.packets for s in list(self.samples)[-20:]]
        
        if self.baseline == 0:
            return False
        
        burst_factor = max(values) / self.baseline if self.baseline > 0 else 1.0
        
        return burst_factor > 2.0
    
    def suggest_optimization(self) -> List[str]:
        """
        Suggest network optimizations based on predictions.
        
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        if len(self.samples) < 10:
            return ["Insufficient data for optimization"]
        
        recent = list(self.samples)[-10:]
        avg_packets = sum(s.packets for s in recent) / len(recent)
        
        if avg_packets > 1000:
            suggestions.append("High traffic detected - consider scaling up resources")
        
        recent_latency = sum(s.latency for s in recent) / len(recent)
        if recent_latency > 50:
            suggestions.append("High latency detected - optimize routing paths")
        
        prediction = self.predict_next()
        if prediction.predicted_value > avg_packets * 1.5:
            suggestions.append("Traffic spike predicted - prepare for increased load")
        
        for pattern in self.patterns:
            if pattern.pattern_type == "bursty":
                suggestions.append("Bursty traffic - consider implementing traffic shaping")
        
        if not suggestions:
            suggestions.append("Network operating normally - no optimizations needed")
        
        return suggestions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get predictor statistics."""
        return {
            "model": self.model.value,
            "window_size": self.window_size,
            "samples_collected": len(self.samples),
            "predictions_made": len(self.predictions),
            "patterns_detected": len(self.patterns),
            "baseline": self.baseline,
            "trend": self.trend,
            "variance": self._calculate_variance(),
        }
