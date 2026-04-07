"""
Quantum Superposition - Multi-qubit superposition states and operations.

Handles multi-qubit quantum states including GHZ states, W states,
and general N-qubit superpositions for quantum networking.
"""

from __future__ import annotations

import uuid
import math
import random
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any, Callable
from enum import Enum

from qnet.core.quantum.qubit import Qubit, QubitState


class SuperpositionType(Enum):
    """Types of multi-qubit superposition states."""
    COMPUTATIONAL = "computational"
    GHZ = "ghz"           # |000⟩ + |111⟩)/√2
    W = "w"               # (|100⟩ + |010⟩ + |001⟩)/√3
    BELL = "bell"         # Two-qubit Bell states
    CAT = "cat"           # Schrodinger cat states
    LINEAR = "linear"     # Linear cluster states
    CUSTOM = "custom"


@dataclass
class SuperpositionState:
    """
    Represents a multi-qubit superposition state.
    
    Manages N-qubit quantum states in various superposition
    configurations for quantum networking applications.
    
    Attributes:
        qubits: List of qubits in superposition
        amplitudes: Complex amplitudes for each basis state
        state_type: Type of superposition
        fidelity: Overall state fidelity
    """
    
    qubits: List[Qubit] = field(default_factory=list)
    amplitudes: Dict[int, complex] = field(default_factory=dict)
    state_type: SuperpositionType = SuperpositionType.COMPUTATIONAL
    fidelity: float = 1.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Initialize or validate amplitudes."""
        if self.amplitudes and not self.qubits:
            n_qubits = int(math.log2(len(self.amplitudes)))
            self.qubits = [Qubit.random() for _ in range(n_qubits)]
        elif self.qubits and not self.amplitudes:
            self._compute_amplitudes()
    
    def _compute_amplitudes(self) -> None:
        """Compute amplitudes from qubit states."""
        self.amplitudes.clear()
        n = len(self.qubits)
        for i in range(2 ** n):
            amplitude = complex(1, 0)
            for j, qubit in enumerate(self.qubits):
                bit = (i >> (n - 1 - j)) & 1
                amplitude *= qubit.alpha if bit == 0 else qubit.beta
            self.amplitudes[i] = amplitude
        self._normalize_amplitudes()
    
    def _normalize_amplitudes(self) -> None:
        """Normalize amplitudes to sum to 1."""
        norm = math.sqrt(sum(abs(a)**2 for a in self.amplitudes.values()))
        if norm > 1e-10:
            self.amplitudes = {k: v / norm for k, v in self.amplitudes.items()}
    
    @classmethod
    def create_ghz_state(cls, n_qubits: int) -> SuperpositionState:
        """
        Create Greenberger-Horne-Zeilinger (GHZ) state.
        
        GHZ state: (|00...0⟩ + |11...1⟩)/√2
        Used for multipartite quantum communication.
        
        Args:
            n_qubits: Number of qubits (2-100)
            
        Returns:
            GHZ superposition state
        """
        qubits = []
        amplitudes = {}
        
        for i in range(2 ** n_qubits):
            if i == 0 or i == (2 ** n_qubits) - 1:
                amplitudes[i] = complex(1 / math.sqrt(2), 0)
            else:
                amplitudes[i] = complex(0, 0)
            qubits.append(Qubit.zero())
        
        return cls(
            qubits=qubits,
            amplitudes=amplitudes,
            state_type=SuperpositionType.GHZ
        )
    
    @classmethod
    def create_w_state(cls, n_qubits: int) -> SuperpositionState:
        """
        Create W state - maximally entangled across n qubits.
        
        W state: (|100...0⟩ + |010...0⟩ + ... + |000...1⟩)/√n
        Robust to particle loss.
        
        Args:
            n_qubits: Number of qubits (2-100)
            
        Returns:
            W superposition state
        """
        qubits = []
        amplitudes = {}
        
        amplitude = complex(1 / math.sqrt(n_qubits), 0)
        for i in range(2 ** n_qubits):
            bit_count = bin(i).count('1')
            if bit_count == 1:
                amplitudes[i] = amplitude
            else:
                amplitudes[i] = complex(0, 0)
            qubits.append(Qubit.zero())
        
        return cls(
            qubits=qubits,
            amplitudes=amplitudes,
            state_type=SuperpositionType.W
        )
    
    @classmethod
    def create_linear_cluster(cls, n_qubits: int) -> SuperpositionState:
        """
        Create linear cluster state for measurement-based QC.
        
        Args:
            n_qubits: Number of qubits in the cluster
            
        Returns:
            Linear cluster state
        """
        qubits = [Qubit.plus() for _ in range(n_qubits)]
        amplitudes = {}
        
        for i in range(2 ** n_qubits):
            bits = [(i >> (n_qubits - 1 - j)) & 1 for j in range(n_qubits)]
            parity = sum(bits[1:]) % 2
            if parity == 0:
                amplitudes[i] = complex(1 / math.sqrt(2 ** (n_qubits - 1)), 0)
            else:
                amplitudes[i] = complex(0, 0)
        
        return cls(
            qubits=qubits,
            amplitudes=amplitudes,
            state_type=SuperpositionType.LINEAR
        )
    
    @classmethod
    def create_cat_state(cls, n_qubits: int, cat_type: str = "even") -> SuperpositionState:
        """
        Create Schrodinger cat state.
        
        Even cat: (|00...0⟩ + |11...1⟩)/√2
        Odd cat: (|00...0⟩ - |11...1⟩)/√2
        
        Args:
            n_qubits: Number of qubits
            cat_type: "even" or "odd" parity
            
        Returns:
            Cat superposition state
        """
        qubits = []
        amplitudes = {}
        sign = 1 if cat_type == "even" else -1
        
        for i in range(2 ** n_qubits):
            if i == 0:
                amplitudes[i] = complex(1 / math.sqrt(2), 0)
            elif i == (2 ** n_qubits) - 1:
                amplitudes[i] = complex(sign / math.sqrt(2), 0)
            else:
                amplitudes[i] = complex(0, 0)
            qubits.append(Qubit.zero())
        
        return cls(
            qubits=qubits,
            amplitudes=amplitudes,
            state_type=SuperpositionType.CAT
        )
    
    def measure_partial(self, qubits_to_measure: List[int]) -> Tuple[int, SuperpositionState]:
        """
        Measure subset of qubits in superposition.
        
        Args:
            qubits_to_measure: Indices of qubits to measure
            
        Returns:
            Tuple of (measurement result, remaining state)
        """
        n = len(self.qubits)
        m = len(qubits_to_measure)
        
        probabilities = {}
        for state_idx, amplitude in self.amplitudes.items():
            bits = [(state_idx >> (n - 1 - j)) & 1 for j in range(n)]
            measured_bits = tuple(bits[q] for q in qubits_to_measure)
            measured_value = sum(b << (m - 1 - i) for i, b in enumerate(measured_bits))
            
            if measured_value not in probabilities:
                probabilities[measured_value] = 0
            probabilities[measured_value] += abs(amplitude)**2
        
        r = random.random()
        cumulative = 0
        measured_value = 0
        for val, prob in sorted(probabilities.items()):
            cumulative += prob
            if cumulative >= r:
                measured_value = val
                break
        
        new_amplitudes = {}
        new_qubits = [q for i, q in enumerate(self.qubits) if i not in qubits_to_measure]
        
        for state_idx, amplitude in self.amplitudes.items():
            bits = [(state_idx >> (n - 1 - j)) & 1 for j in range(n)]
            measured_bits = tuple(bits[q] for q in qubits_to_measure)
            measured_val = sum(b << (m - 1 - i) for i, b in enumerate(measured_bits))
            
            if measured_val == measured_value:
                new_bits = [bits[i] for i in range(n) if i not in qubits_to_measure]
                new_idx = sum(b << (len(new_bits) - 1 - i) for i, b in enumerate(new_bits))
                new_amplitudes[new_idx] = amplitude
        
        norm = math.sqrt(sum(abs(a)**2 for a in new_amplitudes.values()))
        if norm > 1e-10:
            new_amplitudes = {k: v / norm for k, v in new_amplitudes.items()}
        
        new_state = SuperpositionState(
            qubits=new_qubits,
            amplitudes=new_amplitudes,
            state_type=self.state_type,
            fidelity=self.fidelity
        )
        
        return measured_value, new_state
    
    def apply_decoherence(self, decay_rate: float, time_elapsed: float) -> float:
        """
        Apply decoherence to all qubits in superposition.
        
        Args:
            decay_rate: Decoherence rate γ
            time_elapsed: Time since last update
            
        Returns:
            New fidelity value
        """
        for qubit in self.qubits:
            qubit.apply_decoherence(decay_rate, time_elapsed)
        
        self.fidelity = math.exp(-decay_rate * time_elapsed * len(self.qubits)) * self.fidelity
        return self.fidelity
    
    def get_entanglement_entropy(self) -> float:
        """
        Calculate entanglement entropy (approximation).
        
        Returns:
            Von Neumann entropy approximation
        """
        if not self.amplitudes:
            return 0.0
        
        entropy = 0.0
        for amp in self.amplitudes.values():
            p = abs(amp)**2
            if p > 1e-10:
                entropy -= p * math.log2(p)
        
        return entropy
    
    def get_nonlocal_correlations(self) -> float:
        """
        Estimate nonlocal correlation strength.
        
        Returns:
            Correlation measure (0-1)
        """
        entropy = self.get_entanglement_entropy()
        n = len(self.qubits)
        max_entropy = n if n > 0 else 1
        return min(1.0, entropy / max_entropy)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "state_type": self.state_type.value,
            "n_qubits": len(self.qubits),
            "fidelity": self.fidelity,
            "entropy": self.get_entanglement_entropy(),
            "nonlocal_correlations": self.get_nonlocal_correlations(),
            "amplitudes": {str(k): {"r": v.real, "i": v.imag} for k, v in self.amplitudes.items()},
        }
    
    def __repr__(self) -> str:
        return f"SuperpositionState({self.state_type.value}, {len(self.qubits)} qubits, fidelity={self.fidelity:.3f})"


@dataclass
class SuperpositionManager:
    """
    Manages multiple superposition states in a quantum network.
    
    Handles creation, manipulation, and measurement of
    various multi-qubit superposition states.
    """
    
    states: Dict[str, SuperpositionState] = field(default_factory=dict)
    max_states: int = 1000
    
    def create_state(
        self,
        state_type: SuperpositionType,
        n_qubits: int,
        **kwargs
    ) -> Optional[SuperpositionState]:
        """Create a new superposition state."""
        if len(self.states) >= self.max_states:
            return None
        
        if state_type == SuperpositionType.GHZ:
            state = SuperpositionState.create_ghz_state(n_qubits)
        elif state_type == SuperpositionType.W:
            state = SuperpositionState.create_w_state(n_qubits)
        elif state_type == SuperpositionType.LINEAR:
            state = SuperpositionState.create_linear_cluster(n_qubits)
        elif state_type == SuperpositionType.CAT:
            cat_type = kwargs.get("cat_type", "even")
            state = SuperpositionState.create_cat_state(n_qubits, cat_type)
        else:
            state = SuperpositionState(state_type=state_type)
        
        self.states[state.id] = state
        return state
    
    def get_state(self, state_id: str) -> Optional[SuperpositionState]:
        """Get state by ID."""
        return self.states.get(state_id)
    
    def remove_state(self, state_id: str) -> bool:
        """Remove state by ID."""
        if state_id in self.states:
            del self.states[state_id]
            return True
        return False
    
    def apply_decoherence_all(self, decay_rate: float, time_elapsed: float) -> float:
        """Apply decoherence to all states."""
        total_fidelity = 0.0
        for state in self.states.values():
            state.apply_decoherence(decay_rate, time_elapsed)
            total_fidelity += state.fidelity
        
        return total_fidelity / len(self.states) if self.states else 1.0
    
    @property
    def average_fidelity(self) -> float:
        """Average fidelity across all states."""
        if not self.states:
            return 1.0
        return sum(s.fidelity for s in self.states.values()) / len(self.states)
    
    @property
    def total_states(self) -> int:
        """Total number of superposition states."""
        return len(self.states)
