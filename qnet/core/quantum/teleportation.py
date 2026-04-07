"""
Quantum Teleportation - Transfer quantum states using entanglement.

Implements the quantum teleportation protocol allowing transfer of
unknown quantum states between nodes using classical communication
and pre-shared entanglement.
"""

from __future__ import annotations

import uuid
import math
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any, List
from enum import Enum

from qnet.core.quantum.qubit import Qubit, QubitState, GateType
from qnet.core.quantum.entanglement import EntangledPair, BellState


class TeleportationStatus(Enum):
    """Status of teleportation operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DECOHERENCE_ERROR = "decoherence_error"


@dataclass
class TeleportationResult:
    """
    Result of a quantum teleportation operation.
    
    Contains the original state, transferred state (if successful),
    and various metrics about the teleportation.
    """
    success: bool
    original_state: Optional[Qubit] = None
    teleported_state: Optional[Qubit] = None
    status: TeleportationStatus = TeleportationStatus.PENDING
    fidelity: float = 0.0
    classical_bits_sent: int = 0
    entanglement_used: Optional[str] = None
    error_message: Optional[str] = None
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "success": self.success,
            "status": self.status.value,
            "fidelity": self.fidelity,
            "classical_bits_sent": self.classical_bits_sent,
            "entanglement_used": self.entanglement_used,
            "error_message": self.error_message,
            "duration": self.duration,
        }


@dataclass
class BellMeasurement:
    """
    Represents a Bell state measurement performed during teleportation.
    
    The measurement projects onto one of the four Bell states
    and yields two classical bits of information.
    """
    qubit_1: Qubit
    qubit_2: Qubit
    result: BellState
    classical_bits: Tuple[int, int]
    
    @property
    def measurement_circuit(self) -> str:
        """Return ASCII representation of measurement circuit."""
        return """
        ┌───┐
{q1}─┤CNOT├─◎──▶ M1
        └───┘
{q2}──H──▶ M2
        """
    
    def get_correction_gate(self) -> Tuple[GateType, GateType]:
        """
        Determine correction gates based on measurement result.
        
        Returns:
            Tuple of (X-gate needed, Z-gate needed)
        """
        if self.result == BellState.PHI_PLUS:
            return (GateType.IDENTITY, GateType.IDENTITY)
        elif self.result == BellState.PHI_MINUS:
            return (GateType.IDENTITY, GateType.PAULI_Z)
        elif self.result == BellState.PSI_PLUS:
            return (GateType.PAULI_X, GateType.IDENTITY)
        else:  # PSI_MINUS
            return (GateType.PAULI_X, GateType.PAULI_Z)


class QuantumTeleportation:
    """
    Quantum teleportation protocol implementation.
    
    Teleports an unknown quantum state from one node to another
    using pre-shared entanglement and classical communication.
    
    Protocol Steps:
    1. Alice and Bob share an entangled Bell pair
    2. Alice has unknown state |ψ⟩ to send
    3. Alice performs Bell measurement on |ψ⟩ and her half of entanglement
    4. Alice sends 2 classical bits to Bob (measurement result)
    5. Bob applies corrections based on classical bits
    6. Bob now has |ψ⟩
    
    Theoretical Fidelity: 2/3 (classical limit) → 1.0 (quantum with ideal entanglement)
    """
    
    def __init__(self, entanglement_manager=None):
        """
        Initialize teleportation protocol handler.
        
        Args:
            entanglement_manager: Optional EntanglementManager for resource tracking
        """
        self.entanglement_manager = entanglement_manager
        self.teleportation_history: List[TeleportationResult] = []
    
    def teleport(
        self,
        state_to_send: Qubit,
        entangled_pair: EntangledPair,
        sender_id: str,
        receiver_id: str,
        start_time: float = 0.0
    ) -> TeleportationResult:
        """
        Perform quantum teleportation of a qubit state.
        
        Args:
            state_to_send: Unknown quantum state to teleport
            entangled_pair: Pre-shared entangled pair between sender and receiver
            sender_id: ID of sending node
            receiver_id: ID of receiving node
            start_time: Simulation time when teleportation started
            
        Returns:
            TeleportationResult with outcome details
        """
        result = TeleportationResult(
            success=False,
            original_state=state_to_send.clone(),
            entanglement_used=entangled_pair.id,
        )
        
        if not entangled_pair.is_active:
            result.status = TeleportationStatus.FAILED
            result.error_message = "Entangled pair is no longer active"
            return result
        
        if entangled_pair.fidelity < 0.5:
            result.status = TeleportationStatus.DECOHERENCE_ERROR
            result.error_message = "Entanglement fidelity too low for teleportation"
            result.fidelity = entangled_pair.fidelity
            return result
        
        qubit_at_sender = entangled_pair.qubit_a if entangled_pair.node_a == sender_id else entangled_pair.qubit_b
        qubit_at_receiver = entangled_pair.qubit_b if entangled_pair.node_b == receiver_id else entangled_pair.qubit_a
        
        if qubit_at_sender is None or qubit_at_receiver is None:
            result.status = TeleportationStatus.FAILED
            result.error_message = "Qubit missing from entangled pair"
            return result
        
        cnot_qubit = state_to_send.apply_gate(GateType.CNOT, qubit_at_sender)
        m1 = cnot_qubit.measure()
        
        hadamard_state = state_to_send.apply_gate(GateType.HADAMARD)
        m2 = hadamard_state.measure()
        
        result.classical_bits_sent = 2
        
        if m1 == 1:
            qubit_at_receiver = qubit_at_receiver.apply_gate(GateType.PAULI_X)
        if m2 == 1:
            qubit_at_receiver = qubit_at_receiver.apply_gate(GateType.PAULI_Z)
        
        result.teleported_state = qubit_at_receiver
        result.fidelity = entangled_pair.fidelity * state_to_send.fidelity
        result.success = True
        result.status = TeleportationStatus.COMPLETED
        
        entangled_pair.is_active = False
        
        self.teleportation_history.append(result)
        return result
    
    def teleport_with_classical_fallback(
        self,
        state_to_send: Qubit,
        entangled_pair: Optional[EntangledPair],
        channel_quality: float = 0.95
    ) -> Tuple[Optional[Qubit], bool]:
        """
        Attempt teleportation with classical communication fallback.
        
        If quantum teleportation fails due to decoherence,
        falls back to classical state transfer (if state is known).
        
        Args:
            state_to_send: Quantum state to transfer
            entangled_pair: Entangled pair to use (if None, uses classical)
            channel_quality: Probability of successful classical transfer
            
        Returns:
            Tuple of (resulting state or None, was_quantum)
        """
        import random
        
        if entangled_pair and entangled_pair.is_active and entangled_pair.fidelity > 0.7:
            result = self.teleport(
                state_to_send,
                entangled_pair,
                entangled_pair.node_a,
                entangled_pair.node_b
            )
            if result.success:
                return result.teleported_state, True
        
        if random.random() < channel_quality:
            return state_to_send.clone(), False
        
        return None, False
    
    def batch_teleport(
        self,
        states: List[Qubit],
        entangled_pairs: List[EntangledPair],
        sender_id: str,
        receiver_id: str
    ) -> List[TeleportationResult]:
        """
        Teleport multiple qubits in sequence.
        
        Args:
            states: List of quantum states to teleport
            entangled_pairs: List of entangled pairs (one per state)
            sender_id: Source node ID
            receiver_id: Destination node ID
            
        Returns:
            List of teleportation results
        """
        results = []
        
        for state, pair in zip(states, entangled_pairs):
            result = self.teleport(state, pair, sender_id, receiver_id)
            results.append(result)
        
        return results
    
    def calculate_teleportation_fidelity(
        self,
        entanglement_fidelity: float,
        gate_fidelity: float,
        measurement_fidelity: float
    ) -> float:
        """
        Calculate expected teleportation fidelity.
        
        Args:
            entanglement_fidelity: Fidelity of shared entanglement
            gate_fidelity: Fidelity of quantum gates used
            measurement_fidelity: Fidelity of measurements
            
        Returns:
            Expected teleportation fidelity
        """
        return entanglement_fidelity * gate_fidelity * measurement_fidelity
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get teleportation statistics."""
        if not self.teleportation_history:
            return {
                "total_attempts": 0,
                "successful": 0,
                "failed": 0,
                "average_fidelity": 0.0,
                "total_classical_bits": 0,
            }
        
        successful = [r for r in self.teleportation_history if r.success]
        failed = [r for r in self.teleportation_history if not r.success]
        
        return {
            "total_attempts": len(self.teleportation_history),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.teleportation_history),
            "average_fidelity": sum(r.fidelity for r in successful) / len(successful) if successful else 0.0,
            "total_classical_bits": sum(r.classical_bits_sent for r in self.teleportation_history),
        }


@dataclass 
class TeleportationChannel:
    """
    Represents a quantum teleportation channel between two nodes.
    
    Manages the resources needed for continuous teleportation
    including entanglement pairs and classical communication.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_a: Optional[str] = None
    node_b: Optional[str] = None
    entangled_pairs: List[EntangledPair] = field(default_factory=list)
    max_pairs: int = 100
    throughput: float = 0.0
    average_latency: float = 0.0
    total_teleported: int = 0
    
    def add_entangled_pair(self, pair: EntangledPair) -> bool:
        """Add entangled pair to channel."""
        if len(self.entangled_pairs) < self.max_pairs:
            self.entangled_pairs.append(pair)
            return True
        return False
    
    def get_available_pair(self) -> Optional[EntangledPair]:
        """Get first available (active) entangled pair."""
        for pair in self.entangled_pairs:
            if pair.is_active:
                return pair
        return None
    
    def get_available_pairs_count(self) -> int:
        """Count of available (active) entangled pairs."""
        return sum(1 for p in self.entangled_pairs if p.is_active)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize channel to dictionary."""
        return {
            "id": self.id,
            "node_a": self.node_a,
            "node_b": self.node_b,
            "total_pairs": len(self.entangled_pairs),
            "available_pairs": self.get_available_pairs_count(),
            "max_pairs": self.max_pairs,
            "throughput": self.throughput,
            "average_latency": self.average_latency,
            "total_teleported": self.total_teleported,
        }
