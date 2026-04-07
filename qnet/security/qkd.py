"""
Quantum Key Distribution (QKD) - BB84 and E91 protocols.

Implements quantum key distribution protocols for secure
key generation over quantum networks.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import uuid


class QKDProtocolType(Enum):
    """QKD Protocol Types."""
    BB84 = "bb84"
    E91 = "e91"
    SIFT = "sift"
    E91_BIDIRECTIONAL = "e91_bi"


@dataclass
class QKDResult:
    """Result of QKD key generation."""
    success: bool
    key_bits: List[int]
    key_length: int
    protocol: str
    qber: float = 0.0
    eavesdropping_detected: bool = False
    sift_rate: float = 0.0
    raw_key_length: int = 0
    error_rate: float = 0.0
    duration: float = 0.0
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "key_length": self.key_length,
            "protocol": self.protocol,
            "qber": self.qber,
            "eavesdropping_detected": self.eavesdropping_detected,
            "sift_rate": self.sift_rate,
            "raw_key_length": self.raw_key_length,
            "error_rate": self.error_rate,
            "duration": self.duration,
            "message": self.message,
        }


class MeasurementBasis(Enum):
    """Measurement bases for QKD."""
    RECTILINEAR = "+"
    DIAGONAL = "X"


@dataclass
class QubitForQKD:
    """Qubit state for QKD transmission."""
    bit: int
    basis: MeasurementBasis
    state: complex = field(default=complex(0, 0))
    
    def __post_init__(self):
        """Initialize qubit state based on bit and basis."""
        if self.basis == MeasurementBasis.RECTILINEAR:
            self.state = complex(1, 0) if self.bit == 0 else complex(0, 1)
        else:
            sqrt2 = math.sqrt(2)
            if self.bit == 0:
                self.state = complex(1/sqrt2, 0)
            else:
                self.state = complex(-1/sqrt2, 0)


class QKDProtocol:
    """
    Base class for QKD protocols.
    
    Provides common functionality for quantum key distribution.
    """
    
    def __init__(self, name: str = "QKD"):
        """Initialize QKD protocol."""
        self.name = name
        self.keys: Dict[str, List[int]] = {}
    
    def generate_random_bits(self, count: int) -> List[int]:
        """Generate random bit sequence."""
        return [random.randint(0, 1) for _ in range(count)]
    
    def generate_random_bases(self, count: int) -> List[MeasurementBasis]:
        """Generate random measurement bases."""
        return [random.choice([MeasurementBasis.RECTILINEAR, MeasurementBasis.DIAGONAL]) 
                for _ in range(count)]
    
    def calculate_qber(self, key1: List[int], key2: List[int]) -> float:
        """Calculate Quantum Bit Error Rate."""
        if len(key1) != len(key2):
            return 1.0
        
        errors = sum(1 for a, b in zip(key1, key2) if a != b)
        return errors / len(key1) if len(key1) > 0 else 0.0


class BB84Protocol(QKDProtocol):
    """
    BB84 Quantum Key Distribution Protocol.
    
    The first QKD protocol, proposed by Bennett and Brassard in 1984.
    
    Protocol Steps:
    1. Alice generates random bits and bases
    2. Alice sends qubits in those states
    3. Bob measures in random bases
    4. Alice and Bob announce bases (not bits)
    5. They keep bits where bases match (sifting)
    6. Check subset of bits for eavesdropping
    7. Remaining bits form the key
    """
    
    def __init__(self):
        """Initialize BB84 protocol."""
        super().__init__("BB84")
        self.check_bit_count = 10
    
    def alice_generate_qubits(self, num_bits: int) -> Tuple[List[QubitForQKD], List[int], List[MeasurementBasis]]:
        """
        Alice: Generate random bits and prepare qubits.
        
        Args:
            num_bits: Number of bits to generate
            
        Returns:
            Tuple of (qubits, bits, bases)
        """
        bits = self.generate_random_bits(num_bits)
        bases = self.generate_random_bases(num_bits)
        qubits = [QubitForQKD(bit=b, basis=bs) for b, bs in zip(bits, bases)]
        
        return qubits, bits, bases
    
    def bob_measure(self, qubits: List[QubitForQKD]) -> Tuple[List[int], List[MeasurementBasis]]:
        """
        Bob: Measure qubits in random bases.
        
        Args:
            qubits: Received qubits
            
        Returns:
            Tuple of (measured_bits, measurement_bases)
        """
        bases = self.generate_random_bases(len(qubits))
        measured_bits = []
        
        for qubit, basis in zip(qubits, bases):
            if qubit.basis == basis:
                measured_bits.append(qubit.bit)
            else:
                measured_bits.append(random.randint(0, 1))
        
        return measured_bits, bases
    
    def sifting(
        self,
        alice_bases: List[MeasurementBasis],
        bob_bases: List[MeasurementBasis],
        bob_bits: List[int]
    ) -> Tuple[List[int], List[int], List[int]]:
        """
        Sift keys by keeping only matching bases.
        
        Args:
            alice_bases: Alice's measurement bases
            bob_bases: Bob's measurement bases
            bob_bits: Bob's measured bits
            
        Returns:
            Tuple of (sifted_bob_bits, alice_indices, bob_indices)
        """
        alice_indices = []
        bob_indices = []
        sifted_bits = []
        
        for i, (ab, bb) in enumerate(zip(alice_bases, bob_bases)):
            if ab == bb:
                alice_indices.append(i)
                bob_indices.append(i)
                sifted_bits.append(bob_bits[i])
        
        return sifted_bits, alice_indices, bob_indices
    
    def check_for_eavesdropping(
        self,
        alice_bits: List[int],
        bob_bits: List[int],
        check_positions: List[int]
    ) -> Tuple[bool, float]:
        """
        Check for eavesdropping using test bits.
        
        Args:
            alice_bits: Alice's bits
            bob_bits: Bob's bits
            check_positions: Positions to check
            
        Returns:
            Tuple of (eavesdropping_detected, qber)
        """
        if not check_positions or not alice_bits or not bob_bits:
            return False, 0.0
        
        errors = 0
        for pos in check_positions:
            if pos < len(alice_bits) and pos < len(bob_bits):
                if alice_bits[pos] != bob_bits[pos]:
                    errors += 1
        
        qber = errors / len(check_positions) if check_positions else 0.0
        eavesdropping_detected = qber > 0.11
        
        return eavesdropping_detected, qber
    
    def execute(
        self,
        num_bits: int = 1024,
        eavesdropping_probability: float = 0.0
    ) -> QKDResult:
        """
        Execute full BB84 protocol.
        
        Args:
            num_bits: Number of bits to transmit
            eavesdropping_probability: Probability of interception
            
        Returns:
            QKDResult with key generation outcome
        """
        import time
        start_time = time.time()
        
        alice_qubits, alice_bits, alice_bases = self.alice_generate_qubits(num_bits)
        
        transmitted_qubits = []
        for qubit in alice_qubits:
            if eavesdropping_probability > 0 and random.random() < eavesdropping_probability:
                intercepted_basis = random.choice([MeasurementBasis.RECTILINEAR, MeasurementBasis.DIAGONAL])
                measured_bit = random.randint(0, 1)
                eavesdropped_qubit = QubitForQKD(bit=measured_bit, basis=intercepted_basis)
                transmitted_qubits.append(eavesdropped_qubit)
            else:
                transmitted_qubits.append(qubit)
        
        bob_bits, bob_bases = self.bob_measure(transmitted_qubits)
        
        sifted_bits, alice_sifted_idx, bob_sifted_idx = self.sifting(
            alice_bases, bob_bases, bob_bits
        )
        
        if len(sifted_bits) < self.check_bit_count:
            return QKDResult(
                success=False,
                key_bits=[],
                key_length=0,
                protocol="BB84",
                message="Sifted key too short"
            )
        
        check_count = min(self.check_bit_count, len(sifted_bits) // 4)
        check_positions = random.sample(range(len(sifted_bits)), check_count)
        check_bits_alice = [alice_bits[i] for i in [alice_sifted_idx[p] for p in check_positions] if i < len(alice_bits)]
        check_bits_bob = [sifted_bits[p] for p in check_positions]
        
        eavesdropping_detected, qber = self.check_for_eavesdropping(
            check_bits_alice, check_bits_bob, list(range(len(check_bits_alice)))
        )
        
        final_key_positions = [i for i in range(len(sifted_bits)) if i not in check_positions]
        final_key = [sifted_bits[i] for i in final_key_positions]
        
        sift_rate = len(sifted_bits) / num_bits if num_bits > 0 else 0.0
        
        duration = time.time() - start_time
        
        return QKDResult(
            success=not eavesdropping_detected,
            key_bits=final_key,
            key_length=len(final_key),
            protocol="BB84",
            qber=qber,
            eavesdropping_detected=eavesdropping_detected,
            sift_rate=sift_rate,
            raw_key_length=len(sifted_bits),
            error_rate=qber,
            duration=duration,
            message="Key generation successful" if not eavesdropping_detected else "Eavesdropping detected"
        )


class E91Protocol(QKDProtocol):
    """
    E91 Quantum Key Distribution Protocol.
    
    Based on EPR paradox and Bell inequalities.
    Uses entangled pairs for key distribution.
    
    Protocol Steps:
    1. Generate entangled pairs, send one qubit to each party
    2. Both parties measure in random bases
    3. They keep only results where they chose complementary bases
    4. Check Bell inequality violation
    5. Use remaining bits as key
    """
    
    def __init__(self):
        """Initialize E91 protocol."""
        super().__init__("E91")
        self.bell_state = (complex(1/math.sqrt(2), 0), 0, 0, complex(1/math.sqrt(2), 0))
    
    def generate_epr_pair(self) -> Tuple[complex, complex, complex, complex]:
        """
        Generate EPR pair in Bell state |Φ+⟩.
        
        Returns:
            Tuple of (α, β, γ, δ) for state α|00⟩ + β|01⟩ + γ|10⟩ + δ|11⟩
        """
        return (complex(1/math.sqrt(2), 0), complex(0, 0), complex(0, 0), complex(1/math.sqrt(2), 0))
    
    def measure_epr(self, alice_angle: float, bob_angle: float) -> Tuple[int, int]:
        """
        Simulate EPR measurement.
        
        Args:
            alice_angle: Alice's measurement angle
            bob_angle: Bob's measurement angle
            
        Returns:
            Tuple of (alice_result, bob_result)
        """
        correlation = math.cos(2 * (alice_angle - bob_angle))
        
        if random.random() < abs(correlation):
            if correlation > 0:
                return 0, 0
            else:
                return 0, 1
        else:
            return random.randint(0, 1), random.randint(0, 1)
    
    def check_bell_inequality(self, measurements: List[Tuple[int, int, int]]) -> Tuple[bool, float]:
        """
        Check CHSH Bell inequality.
        
        S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
        S > 2 indicates quantum correlation
        
        Args:
            measurements: List of (setting_a, setting_b, outcome)
            
        Returns:
            Tuple of (violates_bell, S_value)
        """
        settings = {0: 0, 1: math.pi/4, 2: math.pi/2, 3: 3*math.pi/4}
        
        def correlation(set_a, set_b):
            pair_count = sum(1 for m in measurements if m[0] == set_a and m[1] == set_b)
            if pair_count == 0:
                return 0
            concordant = sum(1 for m in measurements if m[0] == set_a and m[1] == set_b and m[2] == 0)
            discordant = pair_count - concordant
            return (concordant - discordant) / pair_count
        
        S = (correlation(0, 0) - correlation(0, 1) + 
             correlation(1, 0) + correlation(1, 1))
        
        return S > 2 and S < 2 * math.sqrt(2), S
    
    def execute(
        self,
        num_pairs: int = 1024,
        eavesdropping_probability: float = 0.0
    ) -> QKDResult:
        """
        Execute E91 protocol.
        
        Args:
            num_pairs: Number of EPR pairs
            eavesdropping_probability: Probability of interception
            
        Returns:
            QKDResult with key generation outcome
        """
        import time
        start_time = time.time()
        
        measurements = []
        alice_raw = []
        bob_raw = []
        
        angles = [0, math.pi/4, math.pi/2, 3*math.pi/4]
        
        for _ in range(num_pairs):
            alice_setting = random.randint(0, 1)
            bob_setting = random.randint(0, 1)
            
            alice_angle = angles[alice_setting * 2]
            bob_angle = angles[bob_setting * 2 + 1]
            
            if eavesdropping_probability > 0 and random.random() < eavesdropping_probability:
                alice_angle = random.choice(angles)
            
            alice_result, bob_result = self.measure_epr(alice_angle, bob_angle)
            
            measurements.append((alice_setting, bob_setting, alice_result ^ bob_result))
            alice_raw.append(alice_result)
            bob_raw.append(bob_result)
        
        valid_indices = [i for i, m in enumerate(measurements) 
                        if m[0] != m[1]]
        
        violates_bell, S = self.check_bell_inequality(measurements)
        
        if not violates_bell:
            return QKDResult(
                success=False,
                key_bits=[],
                key_length=0,
                protocol="E91",
                message="Bell inequality not violated - possible eavesdropping or noise"
            )
        
        key = [alice_raw[i] for i in valid_indices[:num_pairs // 4]]
        
        return QKDResult(
            success=True,
            key_bits=key,
            key_length=len(key),
            protocol="E91",
            qber=0.0,
            eavesdropping_detected=eavesdropping_probability > 0.15,
            sift_rate=len(valid_indices) / num_pairs if num_pairs > 0 else 0.0,
            raw_key_length=len(valid_indices),
            duration=time.time() - start_time,
            message=f"E91 key generation successful. S={S:.3f}"
        )


class QKDManager:
    """
    Manager for QKD operations across the network.
    
    Handles key generation, storage, and distribution.
    """
    
    def __init__(self):
        """Initialize QKD manager."""
        self.protocols = {
            QKDProtocolType.BB84: BB84Protocol(),
            QKDProtocolType.E91: E91Protocol(),
        }
        self.active_keys: Dict[str, Dict[str, List[int]]] = {}
        self.key_history: List[QKDResult] = []
    
    def generate_key(
        self,
        node_a: str,
        node_b: str,
        protocol: QKDProtocolType = QKDProtocolType.BB84,
        **kwargs
    ) -> QKDResult:
        """
        Generate quantum key between two nodes.
        
        Args:
            node_a: First node ID
            node_b: Second node ID
            protocol: QKD protocol to use
            **kwargs: Additional protocol parameters
            
        Returns:
            QKDResult with generated key
        """
        protocol_handler = self.protocols.get(protocol, BB84Protocol())
        result = protocol_handler.execute(**kwargs)
        
        if result.success:
            if node_a not in self.active_keys:
                self.active_keys[node_a] = {}
            self.active_keys[node_a][node_b] = result.key_bits
            
            if node_b not in self.active_keys:
                self.active_keys[node_b] = {}
            self.active_keys[node_b][node_a] = result.key_bits
        
        self.key_history.append(result)
        return result
    
    def get_key(self, node_a: str, node_b: str) -> Optional[List[int]]:
        """Get existing key between nodes."""
        if node_a in self.active_keys:
            return self.active_keys[node_a].get(node_b)
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get QKD statistics."""
        return {
            "active_keys": len(self.active_keys),
            "total_keys_generated": len(self.key_history),
            "successful_keys": sum(1 for r in self.key_history if r.success),
            "eavesdropping_detected": sum(1 for r in self.key_history if r.eavesdropping_detected),
            "average_key_length": sum(r.key_length for r in self.key_history) / max(1, len(self.key_history)),
        }
