"""
Qubit - Quantum bit representation and operations.

Represents a quantum bit |ψ⟩ = α|0⟩ + β|1⟩ with full quantum state management,
gate operations, and measurement capabilities.
"""

from __future__ import annotations

import uuid
import math
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any, TypeAlias


class QubitState(Enum):
    """Classical basis states."""
    ZERO = 0
    ONE = 1
    SUPERPOSITION = 2
    ENTANGLED = 3
    UNDEFINED = 4


class GateType(Enum):
    """Quantum gate types."""
    IDENTITY = "I"
    PAULI_X = "X"
    PAULI_Y = "Y"
    PAULI_Z = "Z"
    HADAMARD = "H"
    PHASE = "S"
    PI_8 = "T"
    CNOT = "CNOT"
    CZ = "CZ"
    SWAP = "SWAP"


@dataclass
class Qubit:
    """
    Represents a quantum bit |ψ⟩ = α|0⟩ + β|1⟩.
    
    The qubit maintains complex amplitudes α and β such that |α|² + |β|² = 1.
    Includes fidelity tracking for decoherence simulation.
    
    Attributes:
        id: Unique identifier for this qubit
        alpha: Amplitude for |0⟩ state (complex number)
        beta: Amplitude for |1⟩ state (complex number)
        fidelity: Quantum state fidelity (0.0 - 1.0)
        state: Current quantum state enum
        created_at: Simulation time when qubit was created
        location: Node ID where qubit resides
    """
    
    alpha: complex = field(default=complex(1, 0))
    beta: complex = field(default=complex(0, 0))
    fidelity: float = 1.0
    state: QubitState = QubitState.ZERO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    location: Optional[str] = None
    created_at: float = 0.0
    
    def __post_init__(self):
        """Normalize quantum state after initialization."""
        self._normalize()
        self._update_state()
    
    def _normalize(self) -> None:
        """Ensure |α|² + |β|² = 1 (normalization)."""
        norm = math.sqrt(abs(self.alpha)**2 + abs(self.beta)**2)
        if norm > 1e-10:
            self.alpha = self.alpha / norm
            self.beta = self.beta / norm
        else:
            self.alpha = complex(1, 0)
            self.beta = complex(0, 0)
    
    def _update_state(self) -> None:
        """Update quantum state classification."""
        alpha_zero = abs(self.alpha) < 1e-6
        beta_zero = abs(self.beta) < 1e-6
        
        if alpha_zero and beta_zero:
            self.state = QubitState.UNDEFINED
        elif alpha_zero:
            self.state = QubitState.ONE
        elif beta_zero:
            self.state = QubitState.ZERO
        elif abs(abs(self.alpha)**2 - 0.5) < 0.01:
            self.state = QubitState.SUPERPOSITION
        else:
            self.state = QubitState.SUPERPOSITION
    
    @property
    def probabilities(self) -> Tuple[float, float]:
        """Return measurement probabilities P(0) and P(1)."""
        p0 = abs(self.alpha)**2
        p1 = abs(self.beta)**2
        return (p0, p1)
    
    @property
    def ket_notation(self) -> str:
        """Return Dirac ket notation representation."""
        alpha_real = round(self.alpha.real, 3)
        alpha_imag = round(self.alpha.imag, 3)
        beta_real = round(self.beta.real, 3)
        beta_imag = round(self.beta.imag, 3)
        
        def fmt_complex(c: complex) -> str:
            if abs(c) < 1e-6:
                return "0"
            parts = []
            if abs(c.real) > 1e-6:
                parts.append(str(c.real))
            if abs(c.imag) > 1e-6:
                parts.append(f"{c.imag}j" if c.imag > 0 else f"{c.imag}j")
            return "+".join(parts) if parts else "0"
        
        alpha_str = fmt_complex(self.alpha)
        beta_str = fmt_complex(self.beta)
        
        return f"({alpha_str})|0⟩ + ({beta_str})|1⟩"
    
    def apply_gate(self, gate: GateType, target: Optional[Qubit] = None) -> Qubit:
        """
        Apply a quantum gate operation.
        
        Args:
            gate: The quantum gate to apply
            target: For two-qubit gates, the target qubit
            
        Returns:
            New Qubit instance with gate applied
        """
        new_qubit = Qubit(
            alpha=self.alpha,
            beta=self.beta,
            fidelity=self.fidelity,
            location=self.location,
            created_at=self.created_at
        )
        
        if gate == GateType.IDENTITY:
            pass
        
        elif gate == GateType.PAULI_X:
            new_qubit.alpha, new_qubit.beta = self.beta, self.alpha
        
        elif gate == GateType.PAULI_Y:
            new_qubit.alpha = -self.beta * complex(0, 1)
            new_qubit.beta = self.alpha * complex(0, 1)
        
        elif gate == GateType.PAULI_Z:
            new_qubit.beta = -self.beta
        
        elif gate == GateType.HADAMARD:
            sqrt2 = math.sqrt(2)
            new_qubit.alpha = (self.alpha + self.beta) / sqrt2
            new_qubit.beta = (self.alpha - self.beta) / sqrt2
        
        elif gate == GateType.PHASE:
            new_qubit.beta = self.beta * complex(0, 1)
        
        elif gate == GateType.PI_8:
            new_qubit.beta = self.beta * complex(math.cos(math.pi/4), math.sin(math.pi/4))
        
        elif gate == GateType.CNOT and target:
            prob_zero = abs(self.alpha)**2
            if random.random() < prob_zero:
                pass
            else:
                new_qubit.alpha, new_qubit.beta = self.beta, self.alpha
        
        new_qubit._normalize()
        new_qubit._update_state()
        return new_qubit
    
    def measure(self, force_state: Optional[int] = None) -> int:
        """
        Measure the qubit in computational basis.
        
        Args:
            force_state: For testing, force a specific outcome
            
        Returns:
            0 or 1 (classical bit result)
        """
        if force_state is not None:
            result = force_state
        else:
            p0, p1 = self.probabilities
            result = 0 if random.random() < p0 else 1
        
        self.state = QubitState.ONE if result == 1 else QubitState.ZERO
        self.alpha = complex(1, 0) if result == 0 else complex(0, 0)
        self.beta = complex(0, 0) if result == 0 else complex(1, 0)
        
        return result
    
    def apply_decoherence(self, decay_rate: float, time_elapsed: float) -> float:
        """
        Apply decoherence effect to qubit.
        
        Args:
            decay_rate: Decoherence rate γ (1/τ)
            time_elapsed: Time since last update
            
        Returns:
            New fidelity value
        """
        self.fidelity = math.exp(-decay_rate * time_elapsed) * self.fidelity
        noise = random.gauss(0, (1 - self.fidelity) * 0.1)
        self.alpha += complex(noise, 0)
        self.beta += complex(noise, 0)
        self._normalize()
        return self.fidelity
    
    def clone(self) -> Qubit:
        """Create a deep copy of this qubit."""
        return Qubit(
            alpha=self.alpha,
            beta=self.beta,
            fidelity=self.fidelity,
            state=self.state,
            id=str(uuid.uuid4()),
            location=self.location,
            created_at=self.created_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize qubit to dictionary."""
        return {
            "id": self.id,
            "alpha": {"real": self.alpha.real, "imag": self.alpha.imag},
            "beta": {"real": self.beta.real, "imag": self.beta.imag},
            "fidelity": self.fidelity,
            "state": self.state.value,
            "location": self.location,
            "created_at": self.created_at,
            "probabilities": list(self.probabilities)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Qubit:
        """Deserialize qubit from dictionary."""
        return cls(
            id=data["id"],
            alpha=complex(data["alpha"]["real"], data["alpha"]["imag"]),
            beta=complex(data["beta"]["real"], data["beta"]["imag"]),
            fidelity=data["fidelity"],
            state=QubitState(data["state"]),
            location=data.get("location"),
            created_at=data.get("created_at", 0.0)
        )
    
    @classmethod
    def zero(cls) -> Qubit:
        """Create qubit in |0⟩ state."""
        return cls(alpha=complex(1, 0), beta=complex(0, 0), state=QubitState.ZERO)
    
    @classmethod
    def one(cls) -> Qubit:
        """Create qubit in |1⟩ state."""
        return cls(alpha=complex(0, 0), beta=complex(1, 0), state=QubitState.ONE)
    
    @classmethod
    def plus(cls) -> Qubit:
        """Create qubit in |+⟩ = (|0⟩ + |1⟩)/√2 state."""
        sqrt2 = math.sqrt(2)
        return cls(
            alpha=complex(1/sqrt2, 0),
            beta=complex(1/sqrt2, 0),
            state=QubitState.SUPERPOSITION
        )
    
    @classmethod
    def minus(cls) -> Qubit:
        """Create qubit in |-⟩ = (|0⟩ - |1⟩)/√2 state."""
        sqrt2 = math.sqrt(2)
        return cls(
            alpha=complex(1/sqrt2, 0),
            beta=complex(-1/sqrt2, 0),
            state=QubitState.SUPERPOSITION
        )
    
    @classmethod
    def random(cls) -> Qubit:
        """Create qubit in random pure state."""
        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(0, 2 * math.pi)
        return cls(
            alpha=complex(math.cos(theta) * math.cos(phi), 0),
            beta=complex(math.sin(theta) * math.exp(1j * phi), 0),
            state=QubitState.SUPERPOSITION
        )
    
    def __repr__(self) -> str:
        return f"Qubit({self.ket_notation}, fidelity={self.fidelity:.3f})"


@dataclass
class QuantumRegister:
    """
    Collection of qubits forming a quantum register.
    
    Manages multiple qubits with operations like
    entanglement creation and multi-qubit gates.
    """
    
    qubits: List[Qubit] = field(default_factory=list)
    capacity: int = 100
    
    def add_qubit(self, qubit: Qubit) -> bool:
        """Add qubit to register if capacity allows."""
        if len(self.qubits) < self.capacity:
            self.qubits.append(qubit)
            return True
        return False
    
    def remove_qubit(self, qubit_id: str) -> Optional[Qubit]:
        """Remove and return qubit by ID."""
        for i, q in enumerate(self.qubits):
            if q.id == qubit_id:
                return self.qubits.pop(i)
        return None
    
    def get_qubit(self, qubit_id: str) -> Optional[Qubit]:
        """Get qubit by ID."""
        for q in self.qubits:
            if q.id == qubit_id:
                return q
        return None
    
    @property
    def available_qubits(self) -> int:
        """Number of available qubits in register."""
        return self.capacity - len(self.qubits)
    
    @property
    def average_fidelity(self) -> float:
        """Average fidelity across all qubits."""
        if not self.qubits:
            return 1.0
        return sum(q.fidelity for q in self.qubits) / len(self.qubits)
    
    def apply_decoherence_to_all(self, decay_rate: float, time_elapsed: float) -> float:
        """Apply decoherence to all qubits."""
        for qubit in self.qubits:
            qubit.apply_decoherence(decay_rate, time_elapsed)
        return self.average_fidelity
    
    def __len__(self) -> int:
        return len(self.qubits)
