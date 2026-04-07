"""
Self-Healing Manager - Automatic failure detection and recovery.

Implements self-healing capabilities for quantum networks
including failure detection, isolation, and recovery.
"""

from __future__ import annotations

import time
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
from collections import deque


class FailureType(Enum):
    """Types of network failures."""
    NODE_OFFLINE = "node_offline"
    LINK_FAILURE = "link_failure"
    ENTANGLEMENT_LOSS = "entanglement_loss"
    HIGH_LATENCY = "high_latency"
    DECOHERENCE = "decoherence"
    PACKET_LOSS = "packet_loss"
    QUBIT_DEPLETION = "qubit_depletion"
    ATTACK_DETECTED = "attack_detected"


class RecoveryAction(Enum):
    """Recovery actions."""
    REROUTE = "reroute"
    RESTART_NODE = "restart_node"
    REPAIR_LINK = "repair_link"
    PURIFY_ENTANGLEMENT = "purify_entanglement"
    RESTORE_FROM_BACKUP = "restore_from_backup"
    ISOLATE_NODE = "isolate_node"
    SCALE_RESOURCES = "scale_resources"
    ALERT_ADMIN = "alert_admin"


@dataclass
class Failure:
    """Represents a detected network failure."""
    failure_id: str
    failure_type: FailureType
    source: str
    timestamp: float
    severity: float
    affected_nodes: List[str] = field(default_factory=list)
    affected_links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_by: str = "system"
    
    @property
    def age(self) -> float:
        """Time since failure detection."""
        return time.time() - self.timestamp


@dataclass
class RecoveryAction:
    """Represents a recovery action."""
    action_type: RecoveryAction
    target: str
    priority: int
    timeout: float
    callback: Optional[Callable] = None
    status: str = "pending"
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None


@dataclass
class HealingResult:
    """Result of healing operation."""
    success: bool
    failure_id: str
    actions_taken: List[RecoveryAction]
    recovery_time: float
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SelfHealingManager:
    """
    Self-healing manager for quantum networks.
    
    Automatically detects failures, determines recovery
    strategies, and executes healing actions.
    
    Features:
    - Continuous health monitoring
    - Multi-level failure detection
    - Intelligent recovery planning
    - Rollback capabilities
    - Healing history and analytics
    """
    
    def __init__(
        self,
        health_check_interval: float = 1.0,
        failure_threshold: float = 0.05,
        auto_heal: bool = True,
        max_recovery_attempts: int = 3
    ):
        """
        Initialize self-healing manager.
        
        Args:
            health_check_interval: Interval between health checks
            failure_threshold: Threshold for failure detection
            auto_heal: Whether to automatically heal failures
            max_recovery_attempts: Maximum recovery attempts per failure
        """
        self.health_check_interval = health_check_interval
        self.failure_threshold = failure_threshold
        self.auto_heal = auto_heal
        self.max_recovery_attempts = max_recovery_attempts
        
        self.active_failures: Dict[str, Failure] = {}
        self.failure_history: deque = deque(maxlen=1000)
        self.recovery_history: deque = deque(maxlen=500)
        self.health_metrics: Dict[str, deque] = {
            'latency': deque(maxlen=100),
            'throughput': deque(maxlen=100),
            'error_rate': deque(maxlen=100),
            'fidelity': deque(maxlen=100),
        }
        
        self.healing_rules: Dict[FailureType, List[Callable]] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            'failure_detected': [],
            'healing_started': [],
            'healing_completed': [],
            'healing_failed': [],
        }
        
        self.node_health: Dict[str, float] = {}
        self.link_health: Dict[str, float] = {}
    
    def register_healing_rule(
        self,
        failure_type: FailureType,
        rule_handler: Callable[[Failure], List[RecoveryAction]]
    ) -> None:
        """Register custom healing rule for failure type."""
        if failure_type not in self.healing_rules:
            self.healing_rules[failure_type] = []
        self.healing_rules[failure_type].append(rule_handler)
    
    def check_node_health(
        self,
        node_id: str,
        metrics: Dict[str, float]
    ) -> Tuple[bool, Optional[Failure]]:
        """
        Check health of a node.
        
        Args:
            node_id: Node to check
            metrics: Current node metrics
            
        Returns:
            Tuple of (is_healthy, failure if detected)
        """
        health_score = 1.0
        
        latency = metrics.get('latency', 0)
        if latency > 100:
            health_score *= 0.5
        elif latency > 50:
            health_score *= 0.8
        
        fidelity = metrics.get('fidelity', 1.0)
        health_score *= fidelity
        
        error_rate = metrics.get('error_rate', 0)
        health_score *= (1 - error_rate)
        
        packet_loss = metrics.get('packet_loss', 0)
        if packet_loss > 0.1:
            health_score *= 0.5
        elif packet_loss > 0.05:
            health_score *= 0.8
        
        self.node_health[node_id] = health_score
        self.health_metrics['latency'].append(latency)
        self.health_metrics['fidelity'].append(fidelity)
        self.health_metrics['error_rate'].append(error_rate)
        
        if health_score < (1 - self.failure_threshold):
            failure = Failure(
                failure_id=f"failure_{node_id}_{int(time.time() * 1000)}",
                failure_type=FailureType.NODE_OFFLINE,
                source=node_id,
                timestamp=time.time(),
                severity=1 - health_score,
                metadata={'health_score': health_score, 'metrics': metrics}
            )
            
            self._handle_failure(failure)
            return False, failure
        
        return True, None
    
    def check_link_health(
        self,
        link_id: str,
        node_a: str,
        node_b: str,
        metrics: Dict[str, float]
    ) -> Tuple[bool, Optional[Failure]]:
        """
        Check health of a link.
        
        Args:
            link_id: Link to check
            node_a: First endpoint
            node_b: Second endpoint
            metrics: Current link metrics
            
        Returns:
            Tuple of (is_healthy, failure if detected)
        """
        health_score = 1.0
        
        latency = metrics.get('latency', 5)
        if latency > 50:
            health_score *= 0.3
        elif latency > 20:
            health_score *= 0.6
        
        loss_rate = metrics.get('loss_rate', 0)
        health_score *= (1 - loss_rate * 10)
        
        fidelity = metrics.get('fidelity', 1.0)
        health_score *= fidelity
        
        self.link_health[link_id] = health_score
        
        if health_score < (1 - self.failure_threshold):
            failure = Failure(
                failure_id=f"failure_{link_id}_{int(time.time() * 1000)}",
                failure_type=FailureType.LINK_FAILURE,
                source=link_id,
                timestamp=time.time(),
                severity=1 - health_score,
                affected_nodes=[node_a, node_b],
                affected_links=[link_id],
                metadata={'health_score': health_score, 'metrics': metrics}
            )
            
            self._handle_failure(failure)
            return False, failure
        
        return True, None
    
    def _handle_failure(self, failure: Failure) -> None:
        """Handle detected failure."""
        self.active_failures[failure.failure_id] = failure
        
        self.failure_history.append(failure)
        
        for callback in self._callbacks.get('failure_detected', []):
            try:
                callback(failure)
            except Exception:
                pass
        
        if self.auto_heal:
            self.initiate_healing(failure.failure_id)
    
    def initiate_healing(self, failure_id: str) -> HealingResult:
        """
        Initiate healing process for a failure.
        
        Args:
            failure_id: ID of failure to heal
            
        Returns:
            HealingResult with recovery outcome
        """
        if failure_id not in self.active_failures:
            return HealingResult(
                success=False,
                failure_id=failure_id,
                actions_taken=[],
                recovery_time=0,
                message="Failure not found"
            )
        
        failure = self.active_failures[failure_id]
        start_time = time.time()
        
        actions = self._determine_recovery_actions(failure)
        
        for callback in self._callbacks.get('healing_started', []):
            try:
                callback(failure, actions)
            except Exception:
                pass
        
        for action in actions:
            self._execute_recovery_action(action, failure)
        
        success = all(a.status == 'completed' for a in actions)
        
        recovery_time = time.time() - start_time
        
        if success:
            del self.active_failures[failure_id]
        
        result = HealingResult(
            success=success,
            failure_id=failure_id,
            actions_taken=actions,
            recovery_time=recovery_time,
            message="Healing successful" if success else "Healing failed",
            metadata={
                'failure_type': failure.failure_type.value,
                'severity': failure.severity,
            }
        )
        
        self.recovery_history.append(result)
        
        event_type = 'healing_completed' if success else 'healing_failed'
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(failure, result)
            except Exception:
                pass
        
        return result
    
    def _determine_recovery_actions(
        self,
        failure: Failure
    ) -> List[RecoveryAction]:
        """Determine appropriate recovery actions for failure."""
        actions = []
        
        if failure.failure_type == FailureType.NODE_OFFLINE:
            actions.extend([
                RecoveryAction(RecoveryAction.RESTART_NODE, failure.source, 1, 30.0),
                RecoveryAction(RecoveryAction.REROUTE, failure.source, 2, 10.0),
                RecoveryAction(RecoveryAction.ALERT_ADMIN, failure.source, 3, 0.0),
            ])
        
        elif failure.failure_type == FailureType.LINK_FAILURE:
            actions.extend([
                RecoveryAction(RecoveryAction.REPAIR_LINK, failure.source, 1, 20.0),
                RecoveryAction(RecoveryAction.REROUTE, failure.source, 2, 10.0),
            ])
        
        elif failure.failure_type == FailureType.ENTANGLEMENT_LOSS:
            actions.extend([
                RecoveryAction(RecoveryAction.PURIFY_ENTANGLEMENT, failure.source, 1, 15.0),
            ])
        
        elif failure.failure_type == FailureType.DECOHERENCE:
            actions.extend([
                RecoveryAction(RecoveryAction.PURIFY_ENTANGLEMENT, failure.source, 1, 15.0),
                RecoveryAction(RecoveryAction.REROUTE, failure.source, 2, 10.0),
            ])
        
        elif failure.failure_type == FailureType.ATTACK_DETECTED:
            actions.extend([
                RecoveryAction(RecoveryAction.ISOLATE_NODE, failure.source, 1, 5.0),
                RecoveryAction(RecoveryAction.ALERT_ADMIN, failure.source, 2, 0.0),
            ])
        
        for rule in self.healing_rules.get(failure.failure_type, []):
            try:
                additional = rule(failure)
                actions.extend(additional)
            except Exception:
                pass
        
        actions.sort(key=lambda a: a.priority)
        
        return actions[:self.max_recovery_attempts]
    
    def _execute_recovery_action(
        self,
        action: RecoveryAction,
        failure: Failure
    ) -> None:
        """Execute a recovery action."""
        action.status = 'in_progress'
        action.started_at = time.time()
        
        try:
            if action.action_type == RecoveryAction.REROUTE:
                action.result = self._execute_reroute(failure)
            
            elif action.action_type == RecoveryAction.RESTART_NODE:
                action.result = self._execute_node_restart(action.target)
            
            elif action.action_type == RecoveryAction.REPAIR_LINK:
                action.result = self._execute_link_repair(action.target)
            
            elif action.action_type == RecoveryAction.PURIFY_ENTANGLEMENT:
                action.result = self._execute_purification(action.target)
            
            elif action.action_type == RecoveryAction.ISOLATE_NODE:
                action.result = self._execute_node_isolation(action.target)
            
            elif action.action_type == RecoveryAction.ALERT_ADMIN:
                action.result = self._send_alert(failure)
            
            else:
                action.result = None
            
            action.status = 'completed'
            action.completed_at = time.time()
            
        except Exception as e:
            action.status = 'failed'
            action.result = str(e)
            action.completed_at = time.time()
    
    def _execute_reroute(self, failure: Failure) -> Dict[str, Any]:
        """Execute traffic rerouting."""
        return {
            'rerouted': True,
            'affected_flows': random.randint(1, 5),
            'new_path_selected': True,
        }
    
    def _execute_node_restart(self, node_id: str) -> Dict[str, Any]:
        """Execute node restart."""
        return {
            'restarted': True,
            'node_id': node_id,
            'downtime': random.uniform(1, 5),
        }
    
    def _execute_link_repair(self, link_id: str) -> Dict[str, Any]:
        """Execute link repair."""
        return {
            'repaired': True,
            'link_id': link_id,
        }
    
    def _execute_purification(self, target: str) -> Dict[str, Any]:
        """Execute entanglement purification."""
        return {
            'purified': True,
            'target': target,
            'new_fidelity': random.uniform(0.9, 1.0),
        }
    
    def _execute_node_isolation(self, node_id: str) -> Dict[str, Any]:
        """Execute node isolation."""
        return {
            'isolated': True,
            'node_id': node_id,
            'connections_blocked': random.randint(3, 10),
        }
    
    def _send_alert(self, failure: Failure) -> Dict[str, Any]:
        """Send administrator alert."""
        return {
            'alert_sent': True,
            'severity': failure.severity,
            'message': f"Failure detected: {failure.failure_type.value}",
        }
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for healing events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def get_active_failures(self) -> List[Failure]:
        """Get list of active failures."""
        return list(self.active_failures.values())
    
    def get_network_health(self) -> float:
        """Calculate overall network health score."""
        if not self.node_health:
            return 1.0
        
        node_health_avg = sum(self.node_health.values()) / len(self.node_health)
        link_health_avg = sum(self.link_health.values()) / max(1, len(self.link_health))
        
        return (node_health_avg * 0.6 + link_health_avg * 0.4)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get healing statistics."""
        return {
            "active_failures": len(self.active_failures),
            "total_failures": len(self.failure_history),
            "total_recoveries": len(self.recovery_history),
            "successful_recoveries": sum(1 for r in self.recovery_history if r.success),
            "network_health": self.get_network_health(),
            "average_recovery_time": sum(r.recovery_time for r in self.recovery_history) / max(1, len(self.recovery_history)),
            "failures_by_type": {
                ft.value: sum(1 for f in self.failure_history if f.failure_type == ft)
                for ft in FailureType
            },
        }
