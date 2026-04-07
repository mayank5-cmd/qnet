"""
Attack Simulator - Security attack simulation and detection.

Implements various attack types for testing quantum network
security including eavesdropping, MITM, and network attacks.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from abc import ABC, abstractmethod

from qnet.security.qkd import QKDResult


class AttackType(Enum):
    """Types of security attacks."""
    EAVESDROPPING = "eavesdropping"
    MITM = "man_in_the_middle"
    TRAFFIC_INTERCEPTION = "traffic_interception"
    NODE_COMPROMISE = "node_compromise"
    QUANTUM_HACKING = "quantum_hacking"
    DOS = "denial_of_service"
    ENTANGLEMENT_SPOOFING = "entanglement_spoofing"
    DECOY_ATTACK = "decoy_attack"
    TIME_SHIFT = "time_shift"
    PSEUDOSITY_ATTACK = "pseudosity_attack"


@dataclass
class Attack:
    """
    Represents a security attack simulation.
    """
    attack_id: str
    attack_type: AttackType
    attacker_node: Optional[str] = None
    target_node: Optional[str] = None
    start_time: float = 0.0
    end_time: Optional[float] = None
    success: bool = False
    detected: bool = False
    damage_level: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Attack duration."""
        end = self.end_time or time.time()
        return end - self.start_time


@dataclass
class AttackResult:
    """Result of attack simulation."""
    attack: Attack
    intercepted_data: Any = None
    detection_probability: float = 0.0
    qber_increase: float = 0.0
    key_compromised: bool = False
    message: str = ""


class AttackSimulator:
    """
    Simulates various security attacks on quantum networks.
    
    Used for testing security measures and developing
    countermeasures.
    """
    
    def __init__(self):
        """Initialize attack simulator."""
        self.active_attacks: Dict[str, Attack] = {}
        self.attack_history: List[Attack] = []
        self._detection_sensitivity = 0.1
    
    def set_detection_sensitivity(self, sensitivity: float) -> None:
        """Set eavesdropping detection sensitivity."""
        self._detection_sensitivity = max(0.0, min(1.0, sensitivity))
    
    def simulate_eavesdropping(
        self,
        qkd_result: QKDResult,
        interception_strength: float = 0.1
    ) -> AttackResult:
        """
        Simulate eavesdropping on QKD channel.
        
        Args:
            qkd_result: QKD result to attack
            interception_strength: Probability of intercepting each qubit
            
        Returns:
            AttackResult with outcome
        """
        attack_id = f"eavesdrop_{int(time.time() * 1000)}"
        
        attack = Attack(
            attack_id=attack_id,
            attack_type=AttackType.EAVESDROPPING,
            start_time=time.time(),
            metadata={
                "interception_strength": interception_strength,
                "original_qber": qkd_result.qber,
            }
        )
        
        intercepted_bits = []
        for i, bit in enumerate(qkd_result.key_bits):
            if random.random() < interception_strength:
                intercepted_bits.append(random.randint(0, 1))
            else:
                intercepted_bits.append(bit)
        
        qber_increase = interception_strength * 0.5
        new_qber = min(1.0, qkd_result.qber + qber_increase)
        
        detection_prob = new_qber / (new_qber + self._detection_sensitivity)
        detected = random.random() < detection_prob
        
        attack.detected = detected
        attack.success = not detected
        attack.end_time = time.time()
        
        self.active_attacks[attack_id] = attack
        self.attack_history.append(attack)
        
        return AttackResult(
            attack=attack,
            intercepted_data=intercepted_bits if attack.success else None,
            detection_probability=detection_prob,
            qber_increase=qber_increase,
            key_compromised=attack.success,
            message="Eavesdropping successful - key may be compromised" if attack.success
                    else "Eavesdropping detected - key generation aborted"
        )
    
    def simulate_mitm(
        self,
        source: str,
        destination: str,
        num_qubits: int = 100
    ) -> AttackResult:
        """
        Simulate Man-in-the-Middle attack.
        
        Args:
            source: Source node ID
            destination: Destination node ID
            num_qubits: Number of qubits to intercept
            
        Returns:
            AttackResult
        """
        attack_id = f"mitm_{int(time.time() * 1000)}"
        
        attack = Attack(
            attack_id=attack_id,
            attack_type=AttackType.MITM,
            attacker_node="attacker",
            target_node=destination,
            start_time=time.time(),
            metadata={
                "source": source,
                "destination": destination,
                "qubits_intercepted": num_qubits,
            }
        )
        
        alice_bits = [random.randint(0, 1) for _ in range(num_qubits)]
        bob_bits = [random.randint(0, 1) for _ in range(num_qubits)]
        
        alice_alice = random.random() < 0.15
        
        attack.success = alice_alice
        attack.detected = not alice_alice
        attack.end_time = time.time()
        
        self.active_attacks[attack_id] = attack
        self.attack_history.append(attack)
        
        return AttackResult(
            attack=attack,
            intercepted_data={"alice_bits": alice_bits, "bob_bits": bob_bits},
            detection_probability=0.15 if alice_alice else 0.85,
            key_compromised=attack.success,
            message="MITM attack successful" if attack.success
                    else "MITM attack detected by parties"
        )
    
    def simulate_node_compromise(
        self,
        node_id: str,
        compromise_type: str = "full"
    ) -> AttackResult:
        """
        Simulate node compromise attack.
        
        Args:
            node_id: Node to compromise
            compromise_type: Type of compromise (full, partial, quantum_state)
            
        Returns:
            AttackResult
        """
        attack_id = f"compromise_{node_id}_{int(time.time() * 1000)}"
        
        attack = Attack(
            attack_id=attack_id,
            attack_type=AttackType.NODE_COMPROMISE,
            target_node=node_id,
            start_time=time.time(),
            metadata={
                "compromise_type": compromise_type,
            }
        )
        
        compromised_data = {
            "keys": [random.randint(0, 1) for _ in range(256)],
            "quantum_states": [{"alpha": random.random(), "beta": random.random()} for _ in range(10)],
            "routing_table": {"routes": []},
        }
        
        damage_level = {
            "full": 1.0,
            "partial": 0.5,
            "quantum_state": 0.3,
        }.get(compromise_type, 0.5)
        
        attack.success = True
        attack.damage_level = damage_level
        attack.end_time = time.time()
        
        self.active_attacks[attack_id] = attack
        self.attack_history.append(attack)
        
        return AttackResult(
            attack=attack,
            intercepted_data=compromised_data,
            detection_probability=0.1,
            key_compromised=compromise_type in ["full", "partial"],
            message=f"Node {node_id} compromised ({compromise_type})"
        )
    
    def simulate_dos(
        self,
        target_node: str,
        duration: float = 10.0,
        intensity: float = 0.8
    ) -> AttackResult:
        """
        Simulate Denial of Service attack.
        
        Args:
            target_node: Target node ID
            duration: Attack duration in seconds
            intensity: Attack intensity (0.0 - 1.0)
            
        Returns:
            AttackResult
        """
        attack_id = f"dos_{int(time.time() * 1000)}"
        
        attack = Attack(
            attack_id=attack_id,
            attack_type=AttackType.DOS,
            target_node=target_node,
            start_time=time.time(),
            end_time=time.time() + duration,
            metadata={
                "duration": duration,
                "intensity": intensity,
            }
        )
        
        packets_dropped = int(1000 * intensity)
        latency_increase = intensity * 100
        
        attack.success = intensity > 0.5
        attack.damage_level = intensity
        attack.end_time = time.time() + duration
        
        self.active_attacks[attack_id] = attack
        self.attack_history.append(attack)
        
        return AttackResult(
            attack=attack,
            intercepted_data={
                "packets_dropped": packets_dropped,
                "latency_increase_ms": latency_increase,
            },
            detection_probability=0.3 * intensity,
            message=f"DoS attack on {target_node}: {packets_dropped} packets dropped"
        )
    
    def detect_attack(
        self,
        qber: float,
        baseline_qber: float = 0.0
    ) -> Tuple[bool, float]:
        """
        Detect potential attack based on QBER.
        
        Args:
            qber: Current quantum bit error rate
            baseline_qber: Expected baseline QBER
            
        Returns:
            Tuple of (attack_detected, confidence)
        """
        qber_increase = qber - baseline_qber
        
        if qber_increase > 0.15:
            return True, 0.95
        elif qber_increase > 0.10:
            return True, 0.75
        elif qber_increase > 0.05:
            return True, 0.50
        elif qber_increase > 0.02:
            return True, 0.25
        
        return False, 0.0
    
    def get_attack_statistics(self) -> Dict[str, Any]:
        """Get attack simulation statistics."""
        return {
            "total_attacks": len(self.attack_history),
            "successful_attacks": sum(1 for a in self.attack_history if a.success),
            "detected_attacks": sum(1 for a in self.attack_history if a.detected),
            "active_attacks": len(self.active_attacks),
            "attacks_by_type": {
                at.value: sum(1 for a in self.attack_history if a.attack_type == at)
                for at in AttackType
            },
            "average_damage": sum(a.damage_level for a in self.attack_history) / max(1, len(self.attack_history)),
        }
    
    def get_active_attacks(self) -> List[Attack]:
        """Get currently active attacks."""
        return list(self.active_attacks.values())
    
    def stop_attack(self, attack_id: str) -> bool:
        """Stop an active attack."""
        if attack_id in self.active_attacks:
            self.active_attacks[attack_id].end_time = time.time()
            return True
        return False


class SecurityAnalyzer:
    """
    Analyzes security posture of quantum network.
    
    Provides vulnerability assessment and
    security recommendations.
    """
    
    def __init__(self, attack_simulator: AttackSimulator):
        """Initialize security analyzer."""
        self.attack_simulator = attack_simulator
    
    def assess_vulnerability(
        self,
        qber: float,
        key_length: int,
        protocol: str
    ) -> Dict[str, Any]:
        """
        Assess network vulnerability.
        
        Args:
            qber: Current QBER
            key_length: Generated key length
            protocol: QKD protocol used
            
        Returns:
            Vulnerability assessment
        """
        attack_detected, confidence = self.attack_simulator.detect_attack(qber)
        
        vulnerability_score = 0.0
        
        if qber > 0.15:
            vulnerability_score = 0.9
        elif qber > 0.10:
            vulnerability_score = 0.7
        elif qber > 0.05:
            vulnerability_score = 0.4
        else:
            vulnerability_score = 0.1
        
        if key_length < 128:
            vulnerability_score += 0.2
        elif key_length < 256:
            vulnerability_score += 0.1
        
        return {
            "vulnerable": vulnerability_score > 0.5,
            "vulnerability_score": min(1.0, vulnerability_score),
            "attack_detected": attack_detected,
            "detection_confidence": confidence,
            "recommendations": self._get_recommendations(vulnerability_score, protocol),
        }
    
    def _get_recommendations(self, score: float, protocol: str) -> List[str]:
        """Get security recommendations."""
        recommendations = []
        
        if score > 0.7:
            recommendations.append("CRITICAL: Immediately investigate potential security breach")
            recommendations.append("Consider aborting key generation and restarting")
            recommendations.append("Enable enhanced monitoring")
        elif score > 0.4:
            recommendations.append("WARNING: Increased error rates detected")
            recommendations.append("Monitor QBER closely")
            recommendations.append("Consider increasing privacy amplification")
        else:
            recommendations.append("Security posture: NOMINAL")
            recommendations.append("Continue normal monitoring")
        
        if protocol == "BB84":
            recommendations.append("Ensure single-photon source for BB84")
        
        return recommendations
