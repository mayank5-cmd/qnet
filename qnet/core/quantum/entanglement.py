"""
Quantum Entanglement - Bell states and entanglement management.

Implements quantum entanglement creation, verification, and management
for distributed quantum networking.
"""

from __future__ import annotations

import uuid
import math
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any
from qnet.core.quantum.qubit import Qubit, QubitState


class BellState(Enum):
    """
    The four maximally entangled two-qubit Bell states.
    
    These form a complete basis for entangled states:
    - |Φ+⟩ = (|00⟩ + |11⟩)/√2 (most commonly used)
    - |Φ-⟩ = (|00⟩ - |11⟩)/√2
    - |Ψ+⟩ = (|01⟩ + |10⟩)/√2
    - |Ψ-⟩ = (|01⟩ - |10⟩)/√2
    """
    PHI_PLUS = "Φ+"   # (|00⟩ + |11⟩)/√2
    PHI_MINUS = "Φ-"  # (|00⟩ - |11⟩)/√2
    PSI_PLUS = "Ψ+"   # (|01⟩ + |10⟩)/√2
    PSI_MINUS = "Ψ-"  # (|01⟩ - |10⟩)/√2
    
    @property
    def ket_notation(self) -> str:
        """Return Dirac notation for the Bell state."""
        notations = {
            BellState.PHI_PLUS: "(|00⟩ + |11⟩)/√2",
            BellState.PHI_MINUS: "(|00⟩ - |11⟩)/√2",
            BellState.PSI_PLUS: "(|01⟩ + |10⟩)/√2",
            BellState.PSI_MINUS: "(|01⟩ - |10⟩)/√2",
        }
        return notations[self]
    
    @property
    def stabilizer(self) -> str:
        """Return stabilizer representation."""
        stabilizers = {
            BellState.PHI_PLUS: "ZZ, XX",
            BellState.PHI_MINUS: "ZZ, -XX",
            BellState.PSI_PLUS: "ZY, XY",
            BellState.PSI_MINUS: "ZY, -XY",
        }
        return stabilizers[self]


@dataclass
class EntangledPair:
    """
    Represents a pair of entangled qubits shared between two nodes.
    
    Manages the lifecycle of quantum entanglement including creation,
    purification, and decoherence tracking.
    
    Attributes:
        id: Unique identifier for this entangled pair
        bell_state: Current Bell state of the pair
        qubit_a: First qubit (typically at source node)
        qubit_b: Second qubit (typically at destination node)
        fidelity: Entanglement fidelity (0.0 - 1.0)
        node_a: Source node identifier
        node_b: Destination node identifier
        created_at: Simulation time of creation
        last_purified: Last purification timestamp
        is_active: Whether entanglement is still valid
    """
    
    bell_state: BellState = BellState.PHI_PLUS
    qubit_a: Optional[Qubit] = None
    qubit_b: Optional[Qubit] = None
    fidelity: float = 1.0
    node_a: Optional[str] = None
    node_b: Optional[str] = None
    created_at: float = 0.0
    last_purified: float = 0.0
    is_active: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Initialize qubits if not provided."""
        if self.qubit_a is None:
            self.qubit_a = self._create_bell_qubit(self.bell_state, is_first=True)
        if self.qubit_b is None:
            self.qubit_b = self._create_bell_qubit(self.bell_state, is_first=False)
    
    def _create_bell_qubit(self, state: BellState, is_first: bool) -> Qubit:
        """Create qubit in appropriate Bell state component."""
        sqrt2 = math.sqrt(2)
        
        if state == BellState.PHI_PLUS:
            if is_first:
                return Qubit(alpha=complex(1/sqrt2, 0), beta=complex(0, 0))
            return Qubit(alpha=complex(0, 0), beta=complex(1/sqrt2, 0))
        
        elif state == BellState.PHI_MINUS:
            if is_first:
                return Qubit(alpha=complex(1/sqrt2, 0), beta=complex(0, 0))
            return Qubit(alpha=complex(0, 0), beta=complex(-1/sqrt2, 0))
        
        elif state == BellState.PSI_PLUS:
            if is_first:
                return Qubit(alpha=complex(1/sqrt2, 0), beta=complex(0, 0))
            return Qubit(alpha=complex(0, 0), beta=complex(1/sqrt2, 0))
        
        else:  # PSI_MINUS
            if is_first:
                return Qubit(alpha=complex(1/sqrt2, 0), beta=complex(0, 0))
            return Qubit(alpha=complex(0, 0), beta=complex(-1/sqrt2, 0))
    
    def measure_correlated(self) -> Tuple[int, int]:
        """
        Perform correlated measurement on entangled pair.
        
        Returns:
            Tuple of measurement results that should be correlated
        """
        result_a = self.qubit_a.measure() if self.qubit_a else random.randint(0, 1)
        result_b = self.qubit_b.measure() if self.qubit_b else random.randint(0, 1)
        return result_a, result_b
    
    def apply_decoherence(self, decay_rate: float, time_elapsed: float) -> float:
        """
        Apply decoherence to both qubits in the pair.
        
        Args:
            decay_rate: Decoherence rate γ
            time_elapsed: Time since last update
            
        Returns:
            New fidelity value
        """
        if self.qubit_a:
            self.qubit_a.apply_decoherence(decay_rate, time_elapsed)
        if self.qubit_b:
            self.qubit_b.apply_decoherence(decay_rate, time_elapsed)
        
        self.fidelity = self.qubit_a.fidelity if self.qubit_a else self.fidelity
        
        if self.fidelity < 0.5:
            self.is_active = False
        
        return self.fidelity
    
    def purify(self, other_pair: EntangledPair) -> bool:
        """
        Attempt entanglement purification using CNOT protocol.
        
        Two pairs are measured and kept only if both measurements succeed.
        This improves fidelity at the cost of losing one pair.
        
        Args:
            other_pair: Another entangled pair for purification
            
        Returns:
            True if purification successful, False otherwise
        """
        if not self.is_active or not other_pair.is_active:
            return False
        
        if self.qubit_a and self.qubit_b and other_pair.qubit_a and other_pair.qubit_b:
            self.qubit_a = self.qubit_a.apply_gate(GateType.CNOT, other_pair.qubit_a)
            
            m1 = self.qubit_a.measure()
            m2 = other_pair.qubit_a.measure()
            
            if m1 == m2:
                self.fidelity = min(1.0, (2 * self.fidelity**2 + 2 * other_pair.fidelity**2) / 
                                   (self.fidelity**2 + other_pair.fidelity**2))
                self.last_purified = 0.0
                return True
        
        self.is_active = False
        return False
    
    def apply_single_qubit_operation(self, qubit: str, gate: Any) -> None:
        """
        Apply single-qubit gate to one side of entanglement.
        
        Args:
            qubit: 'a' or 'b' to specify which qubit
            gate: GateType to apply
        """
        if qubit == 'a' and self.qubit_a:
            self.qubit_a = self.qubit_a.apply_gate(gate)
        elif qubit == 'b' and self.qubit_b:
            self.qubit_b = self.qubit_b.apply_gate(gate)
    
    def get_concurrence(self) -> float:
        """
        Calculate concurrence - a measure of entanglement.
        
        Returns:
            Concurrence value between 0 (separable) and 1 (maximally entangled)
        """
        if self.qubit_a and self.qubit_b:
            p00 = abs(self.qubit_a.alpha * self.qubit_b.alpha)**2
            p01 = abs(self.qubit_a.alpha * self.qubit_b.beta)**2
            p10 = abs(self.qubit_a.beta * self.qubit_a.alpha)**2
            p11 = abs(self.qubit_a.beta * self.qubit_b.beta)**2
            return 2 * math.sqrt(max(p00 * p11, p01 * p10))
        return self.fidelity
    
    def swap_entanglement(self, target: EntangledPair) -> bool:
        """
        Perform entanglement swapping with another pair.
        
        Allows entanglement between non-adjacent nodes by using
        two adjacent entangled pairs and measurement.
        
        Args:
            target: Another entangled pair
            
        Returns:
            True if swap successful
        """
        if not (self.is_active and target.is_active):
            return False
        
        if (self.qubit_a and self.qubit_b and 
            target.qubit_a and target.qubit_b):
            
            target.qubit_a = self.qubit_a.apply_gate(GateType.CNOT, target.qubit_a)
            m1 = self.qubit_a.measure()
            m2 = target.qubit_a.measure()
            
            if m2 == 1:
                target.qubit_b = target.qubit_b.apply_gate(GateType.PAULI_X)
            if m1 == m1:
                target.qubit_b = target.qubit_b.apply_gate(GateType.PAULI_Z)
            
            target.fidelity = self.fidelity * target.fidelity
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entangled pair to dictionary."""
        return {
            "id": self.id,
            "bell_state": self.bell_state.value,
            "fidelity": self.fidelity,
            "node_a": self.node_a,
            "node_b": self.node_b,
            "created_at": self.created_at,
            "last_purified": self.last_purified,
            "is_active": self.is_active,
            "concurrence": self.get_concurrence(),
            "qubit_a": self.qubit_a.to_dict() if self.qubit_a else None,
            "qubit_b": self.qubit_b.to_dict() if self.qubit_b else None,
        }
    
    @classmethod
    def create_pair(
        cls,
        node_a: str,
        node_b: str,
        bell_state: BellState = BellState.PHI_PLUS,
        created_at: float = 0.0
    ) -> EntangledPair:
        """Factory method to create an entangled pair."""
        return cls(
            bell_state=bell_state,
            node_a=node_a,
            node_b=node_b,
            created_at=created_at
        )
    
    def __repr__(self) -> str:
        return (f"EntangledPair({self.bell_state.value}, "
                f"fidelity={self.fidelity:.3f}, "
                f"{self.node_a}↔{self.node_b})")


@dataclass
class EntanglementManager:
    """
    Manages entangled pairs across a quantum network.
    
    Tracks entanglement resources, handles pair distribution,
    and maintains entanglement tables for routing.
    """
    
    pairs: Dict[str, EntangledPair] = field(default_factory=dict)
    node_pairs: Dict[str, List[str]] = field(default_factory=dict)
    max_pairs_per_node: int = 1000
    
    def create_pair(
        self,
        node_a: str,
        node_b: str,
        bell_state: BellState = BellState.PHI_PLUS,
        created_at: float = 0.0
    ) -> Optional[EntangledPair]:
        """Create new entangled pair between two nodes."""
        if node_a not in self.node_pairs:
            self.node_pairs[node_a] = []
        if node_b not in self.node_pairs:
            self.node_pairs[node_b] = []
        
        if (len(self.node_pairs[node_a]) >= self.max_pairs_per_node or
            len(self.node_pairs[node_b]) >= self.max_pairs_per_node):
            return None
        
        pair = EntangledPair.create_pair(node_a, node_b, bell_state, created_at)
        self.pairs[pair.id] = pair
        self.node_pairs[node_a].append(pair.id)
        self.node_pairs[node_b].append(pair.id)
        
        return pair
    
    def get_pair(self, pair_id: str) -> Optional[EntangledPair]:
        """Get entangled pair by ID."""
        return self.pairs.get(pair_id)
    
    def get_pairs_for_node(self, node_id: str) -> List[EntangledPair]:
        """Get all pairs involving a node."""
        pair_ids = self.node_pairs.get(node_id, [])
        return [self.pairs[pid] for pid in pair_ids if pid in self.pairs]
    
    def get_active_pairs_for_node(self, node_id: str) -> List[EntangledPair]:
        """Get all active (high-fidelity) pairs involving a node."""
        return [p for p in self.get_pairs_for_node(node_id) if p.is_active and p.fidelity > 0.7]
    
    def remove_pair(self, pair_id: str) -> bool:
        """Remove entangled pair from manager."""
        if pair_id not in self.pairs:
            return False
        
        pair = self.pairs[pair_id]
        if pair.node_a in self.node_pairs:
            self.node_pairs[pair.node_a].remove(pair_id)
        if pair.node_b in self.node_pairs:
            self.node_pairs[pair.node_b].remove(pair_id)
        
        del self.pairs[pair_id]
        return True
    
    def apply_decoherence_all(self, decay_rate: float, time_elapsed: float) -> int:
        """Apply decoherence to all pairs."""
        active_count = 0
        for pair in self.pairs.values():
            pair.apply_decoherence(decay_rate, time_elapsed)
            if pair.is_active:
                active_count += 1
        return active_count
    
    @property
    def total_pairs(self) -> int:
        """Total number of entangled pairs."""
        return len(self.pairs)
    
    @property
    def active_pairs(self) -> int:
        """Number of active entangled pairs."""
        return sum(1 for p in self.pairs.values() if p.is_active)
    
    @property
    def average_fidelity(self) -> float:
        """Average fidelity across all pairs."""
        if not self.pairs:
            return 1.0
        return sum(p.fidelity for p in self.pairs.values()) / len(self.pairs)


from qnet.core.quantum.qubit import GateType
