"""
Quantum Decoherence - Decoherence modeling for quantum systems.

Implements realistic decoherence models including exponential decay,
amplitude damping, depolarization, and phase damping for accurate
quantum network simulation.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from abc import ABC, abstractmethod

from qnet.core.quantum.qubit import Qubit


class DecoherenceType(Enum):
    """Types of decoherence mechanisms."""
    EXPONENTIAL = "exponential"
    AMPLITUDE_DAMPING = "amplitude_damping"
    DEPOLARIZATION = "depolarization"
    PHASE_DAMPING = "phase_damping"
    THERMAL = "thermal"
    COLLECTIVE = "collective"


@dataclass
class DecoherenceResult:
    """
    Result of decoherence calculation for a quantum state.
    
    Contains fidelity metrics and decoherence parameters.
    """
    initial_fidelity: float
    final_fidelity: float
    decoherence_type: DecoherenceType
    time_elapsed: float
    decay_rate: float
    fidelity_loss: float
    is_below_threshold: bool
    threshold: float = 0.7
    
    @property
    def recovery_possible(self) -> bool:
        """Whether quantum error correction is still possible."""
        return self.final_fidelity > 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "initial_fidelity": self.initial_fidelity,
            "final_fidelity": self.final_fidelity,
            "decoherence_type": self.decoherence_type.value,
            "time_elapsed": self.time_elapsed,
            "decay_rate": self.decay_rate,
            "fidelity_loss": self.fidelity_loss,
            "is_below_threshold": self.is_below_threshold,
            "recovery_possible": self.recovery_possible,
        }


class DecoherenceModel(ABC):
    """
    Abstract base class for decoherence models.
    
    Subclasses implement specific decoherence mechanisms
    for accurate quantum system simulation.
    """
    
    def __init__(self, decay_rate: float = 0.001, threshold: float = 0.7):
        """
        Initialize decoherence model.
        
        Args:
            decay_rate: Base decay rate γ (1/τ where τ is coherence time)
            threshold: Fidelity threshold for entanglement validity
        """
        self.decay_rate = decay_rate
        self.threshold = threshold
    
    @abstractmethod
    def calculate_fidelity(self, initial_fidelity: float, time_elapsed: float) -> float:
        """
        Calculate fidelity after time elapsed.
        
        Args:
            initial_fidelity: Starting fidelity
            time_elapsed: Time since last update
            
        Returns:
            New fidelity value
        """
        pass
    
    @abstractmethod
    def apply_to_qubit(self, qubit: Qubit, time_elapsed: float) -> float:
        """
        Apply decoherence to a qubit.
        
        Args:
            qubit: Qubit to apply decoherence to
            time_elapsed: Time elapsed
            
        Returns:
            New fidelity value
        """
        pass
    
    def simulate(self, initial_fidelity: float, time_elapsed: float) -> DecoherenceResult:
        """
        Simulate decoherence process.
        
        Args:
            initial_fidelity: Starting fidelity
            time_elapsed: Simulation time
            
        Returns:
            DecoherenceResult with full details
        """
        final_fidelity = self.calculate_fidelity(initial_fidelity, time_elapsed)
        return DecoherenceResult(
            initial_fidelity=initial_fidelity,
            final_fidelity=final_fidelity,
            decoherence_type=self.decoherence_type(),
            time_elapsed=time_elapsed,
            decay_rate=self.decay_rate,
            fidelity_loss=initial_fidelity - final_fidelity,
            is_below_threshold=final_fidelity < self.threshold,
            threshold=self.threshold
        )
    
    @abstractmethod
    def decoherence_type(self) -> DecoherenceType:
        """Return the decoherence type for this model."""
        pass


class ExponentialDecoherence(DecoherenceModel):
    """
    Standard exponential decoherence model.
    
    Fidelity decays as F(t) = F₀ * e^(-γt)
    
    Most common model for decoherence in isolated quantum systems.
    """
    
    def decoherence_type(self) -> DecoherenceType:
        return DecoherenceType.EXPONENTIAL
    
    def calculate_fidelity(self, initial_fidelity: float, time_elapsed: float) -> float:
        """
        Calculate exponentially decayed fidelity.
        
        Args:
            initial_fidelity: Starting fidelity F₀
            time_elapsed: Time t
            
        Returns:
            F₀ * e^(-γt)
        """
        return initial_fidelity * math.exp(-self.decay_rate * time_elapsed)
    
    def apply_to_qubit(self, qubit: Qubit, time_elapsed: float) -> float:
        """Apply exponential decoherence to qubit."""
        new_fidelity = self.calculate_fidelity(qubit.fidelity, time_elapsed)
        noise = random.gauss(0, (1 - new_fidelity) * 0.05)
        qubit.alpha += complex(noise, 0)
        qubit.beta += complex(noise, 0)
        qubit.fidelity = new_fidelity
        return new_fidelity


class AmplitudeDamping(DecoherenceModel):
    """
    Amplitude damping decoherence model.
    
    Models energy loss to environment (|1⟩ → |0⟩ transitions).
    Relevant for superconducting qubits and trapped ions.
    
    Kraus operators:
    K₀ = [[1, 0], [0, √(1-γ)]]
    K₁ = [[0, √γ], [0, 0]]
    """
    
    def __init__(self, damping_rate: float = 0.001, threshold: float = 0.7):
        super().__init__(damping_rate, threshold)
        self.damping_rate = damping_rate
    
    def decoherence_type(self) -> DecoherenceType:
        return DecoherenceType.AMPLITUDE_DAMPING
    
    def calculate_fidelity(self, initial_fidelity: float, time_elapsed: float) -> float:
        """
        Calculate fidelity with amplitude damping.
        
        Args:
            initial_fidelity: Starting fidelity
            time_elapsed: Time elapsed
            
        Returns:
            F(t) = 1 - (1 - F₀)(1 - e^(-γt))
        """
        p = 1 - math.exp(-self.damping_rate * time_elapsed)
        return 1 - (1 - initial_fidelity) * (1 - p)
    
    def apply_to_qubit(self, qubit: Qubit, time_elapsed: float) -> float:
        """Apply amplitude damping to qubit."""
        p = 1 - math.exp(-self.damping_rate * time_elapsed)
        qubit.beta = qubit.beta * math.sqrt(1 - p)
        if random.random() < p * abs(qubit.beta)**2:
            qubit.alpha = complex(1, 0)
            qubit.beta = complex(0, 0)
        qubit.fidelity = self.calculate_fidelity(qubit.fidelity, time_elapsed)
        return qubit.fidelity


class Depolarization(DecoherenceModel):
    """
    Depolarizing decoherence model.
    
    All states equally likely to be corrupted.
    Useful for modeling white noise environments.
    
    F(t) = F₀ * (1 - 3p(t)/4) where p(t) = 1 - e^(-4γt/3)
    """
    
    def __init__(self, depolarization_rate: float = 0.001, threshold: float = 0.7):
        super().__init__(depolarization_rate, threshold)
    
    def decoherence_type(self) -> DecoherenceType:
        return DecoherenceType.DEPOLARIZATION
    
    def calculate_fidelity(self, initial_fidelity: float, time_elapsed: float) -> float:
        """
        Calculate fidelity with depolarization.
        
        Args:
            initial_fidelity: Starting fidelity
            time_elapsed: Time elapsed
            
        Returns:
            F(t) = (1 - 3/4 * p(t)) * F₀
        """
        p = 1 - math.exp(-4 * self.decay_rate * time_elapsed / 3)
        return initial_fidelity * (1 - 0.75 * p)
    
    def apply_to_qubit(self, qubit: Qubit, time_elapsed: float) -> float:
        """Apply depolarization to qubit."""
        p = 1 - math.exp(-4 * self.decay_rate * time_elapsed / 3)
        if random.random() < p:
            error_type = random.randint(0, 2)
            if error_type == 0:
                qubit.alpha, qubit.beta = qubit.beta, qubit.alpha
            elif error_type == 1:
                qubit.alpha = -qubit.alpha
                qubit.beta = -qubit.beta
            else:
                qubit.beta = -qubit.beta
        qubit.fidelity = self.calculate_fidelity(qubit.fidelity, time_elapsed)
        return qubit.fidelity


class PhaseDamping(DecoherenceModel):
    """
    Phase damping decoherence model.
    
    Loss of quantum coherence without energy loss.
    Relevant for dephasing noise in quantum gates.
    
    F(t) = 1 - (1 - F₀) * (1 - e^(-2γt))
    """
    
    def decoherence_type(self) -> DecoherenceType:
        return DecoherenceType.PHASE_DAMPING
    
    def calculate_fidelity(self, initial_fidelity: float, time_elapsed: float) -> float:
        """
        Calculate fidelity with phase damping.
        
        Args:
            initial_fidelity: Starting fidelity
            time_elapsed: Time elapsed
            
        Returns:
            F(t) = 1 - (1 - F₀) * e^(-2γt)
        """
        return 1 - (1 - initial_fidelity) * math.exp(-2 * self.decay_rate * time_elapsed)
    
    def apply_to_qubit(self, qubit: Qubit, time_elapsed: float) -> float:
        """Apply phase damping to qubit."""
        phase_noise = random.gauss(0, math.sqrt(time_elapsed * self.decay_rate))
        qubit.beta = qubit.beta * complex(math.cos(phase_noise), math.sin(phase_noise))
        qubit.fidelity = self.calculate_fidelity(qubit.fidelity, time_elapsed)
        return qubit.fidelity


class ThermalDecoherence(DecoherenceModel):
    """
    Thermal decoherence model.
    
    Models decoherence due to finite temperature environment.
    More sophisticated than simple exponential decay.
    
    F(t) = F₀ * e^(-γt) * (1 + ε * (1 - e^(-γt)))
    where ε is thermal population.
    """
    
    def __init__(self, decay_rate: float = 0.001, thermal_population: float = 0.01, threshold: float = 0.7):
        super().__init__(decay_rate, threshold)
        self.thermal_population = thermal_population
    
    def decoherence_type(self) -> DecoherenceType:
        return DecoherenceType.THERMAL
    
    def calculate_fidelity(self, initial_fidelity: float, time_elapsed: float) -> float:
        """Calculate fidelity with thermal effects."""
        exp_term = math.exp(-self.decay_rate * time_elapsed)
        return initial_fidelity * exp_term * (1 + self.thermal_population * (1 - exp_term))
    
    def apply_to_qubit(self, qubit: Qubit, time_elapsed: float) -> float:
        """Apply thermal decoherence to qubit."""
        qubit.fidelity = self.calculate_fidelity(qubit.fidelity, time_elapsed)
        if random.random() < self.thermal_population * 0.1:
            qubit.alpha, qubit.beta = qubit.beta, qubit.alpha
        return qubit.fidelity


class CollectiveDecoherence(DecoherenceModel):
    """
    Collective decoherence model.
    
    Models decoherence when qubits interact with common environment.
    Relevant for coupled qubit systems.
    
    Includes both individual and collective dephasing.
    """
    
    def __init__(self, individual_rate: float = 0.001, collective_rate: float = 0.0005, threshold: float = 0.7):
        super().__init__(individual_rate, threshold)
        self.collective_rate = collective_rate
    
    def decoherence_type(self) -> DecoherenceType:
        return DecoherenceType.COLLECTIVE
    
    def calculate_fidelity(self, initial_fidelity: float, time_elapsed: float) -> float:
        """Calculate fidelity with collective effects."""
        individual = math.exp(-self.decay_rate * time_elapsed)
        collective = math.exp(-self.collective_rate * time_elapsed)
        return initial_fidelity * (0.7 * individual + 0.3 * collective)
    
    def apply_to_qubit(self, qubit: Qubit, time_elapsed: float) -> float:
        """Apply collective decoherence to qubit."""
        qubit.fidelity = self.calculate_fidelity(qubit.fidelity, time_elapsed)
        return qubit.fidelity


class DecoherenceSimulator:
    """
    High-level decoherence simulator managing multiple models.
    
    Combines different decoherence mechanisms and provides
    unified interface for quantum network simulation.
    """
    
    def __init__(self, default_model: str = "exponential"):
        """
        Initialize decoherence simulator.
        
        Args:
            default_model: Default decoherence model name
        """
        self.models: Dict[str, DecoherenceModel] = {
            "exponential": ExponentialDecoherence(),
            "amplitude_damping": AmplitudeDamping(),
            "depolarization": Depolarization(),
            "phase_damping": PhaseDamping(),
            "thermal": ThermalDecoherence(),
            "collective": CollectiveDecoherence(),
        }
        self.active_model = self.models.get(default_model, self.models["exponential"])
        self.history: List[DecoherenceResult] = []
    
    def set_model(self, model_name: str) -> bool:
        """Set active decoherence model."""
        if model_name in self.models:
            self.active_model = self.models[model_name]
            return True
        return False
    
    def simulate(self, initial_fidelity: float, time_elapsed: float) -> DecoherenceResult:
        """Simulate decoherence with active model."""
        result = self.active_model.simulate(initial_fidelity, time_elapsed)
        self.history.append(result)
        return result
    
    def apply_to_qubit(self, qubit: Qubit, time_elapsed: float) -> float:
        """Apply decoherence to qubit."""
        return self.active_model.apply_to_qubit(qubit, time_elapsed)
    
    def apply_to_qubits(self, qubits: List[Qubit], time_elapsed: float) -> Dict[str, float]:
        """Apply decoherence to multiple qubits."""
        results = {}
        for i, qubit in enumerate(qubits):
            results[f"qubit_{i}"] = self.apply_to_qubit(qubit, time_elapsed)
        return results
    
    def get_average_fidelity(self, qubits: List[Qubit]) -> float:
        """Calculate average fidelity across qubits."""
        if not qubits:
            return 1.0
        return sum(q.fidelity for q in qubits) / len(qubits)
    
    def get_coherence_time(self, target_fidelity: float = 0.5) -> float:
        """
        Estimate coherence time for target fidelity.
        
        Args:
            target_fidelity: Target fidelity level
            
        Returns:
            Estimated time to reach target fidelity
        """
        if self.active_model.decay_rate <= 0:
            return float('inf')
        return -math.log(target_fidelity) / self.active_model.decay_rate
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get decoherence statistics."""
        if not self.history:
            return {"total_simulations": 0}
        
        return {
            "total_simulations": len(self.history),
            "average_fidelity_loss": sum(r.fidelity_loss for r in self.history) / len(self.history),
            "below_threshold_count": sum(1 for r in self.history if r.is_below_threshold),
            "below_threshold_rate": sum(1 for r in self.history if r.is_below_threshold) / len(self.history),
            "recovery_possible_rate": sum(1 for r in self.history if r.recovery_possible) / len(self.history),
        }
