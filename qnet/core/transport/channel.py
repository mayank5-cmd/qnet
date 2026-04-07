"""
Quantum and Classical Channels - Physical communication channels.

Implements quantum channels for qubit transmission and classical
channels for traditional networking over quantum network infrastructure.
"""

from __future__ import annotations

import uuid
import math
import random
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Tuple
from enum import Enum
from abc import ABC, abstractmethod

from qnet.core.quantum.qubit import Qubit
from qnet.core.quantum.entanglement import EntangledPair, BellState
from qnet.core.quantum.decoherence import DecoherenceSimulator, ExponentialDecoherence


class ChannelState(Enum):
    """State of a communication channel."""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class ChannelType(Enum):
    """Type of communication channel."""
    QUANTUM_DIRECT = "quantum_direct"
    QUANTUM_ENTANGLED = "quantum_entangled"
    CLASSICAL_QUANTUM = "classical_quantum"
    CLASSICAL_PURE = "classical_pure"


@dataclass
class ChannelMetrics:
    """Metrics for channel performance monitoring."""
    packets_sent: int = 0
    packets_received: int = 0
    packets_dropped: int = 0
    total_latency: float = 0.0
    total_fidelity_loss: float = 0.0
    uptime: float = 0.0
    last_used: float = 0.0
    
    @property
    def average_latency(self) -> float:
        """Average packet latency."""
        return self.total_latency / self.packets_sent if self.packets_sent > 0 else 0.0
    
    @property
    def packet_loss_rate(self) -> float:
        """Packet loss rate."""
        total = self.packets_sent + self.packets_dropped
        return self.packets_dropped / total if total > 0 else 0.0
    
    @property
    def throughput(self) -> float:
        """Throughput in packets per second."""
        return self.packets_received / self.uptime if self.uptime > 0 else 0.0


class Channel(ABC):
    """
    Abstract base class for communication channels.
    
    Defines the interface for both quantum and classical channels.
    """
    
    def __init__(
        self,
        channel_id: str,
        node_a: str,
        node_b: str,
        bandwidth: float = 1.0,
        latency_base: float = 5.0,
        latency_variance: float = 2.0,
        error_rate: float = 0.001,
    ):
        """
        Initialize channel.
        
        Args:
            channel_id: Unique channel identifier
            node_a: First endpoint node ID
            node_b: Second endpoint node ID
            bandwidth: Channel bandwidth (arbitrary units)
            latency_base: Base latency in ms
            latency_variance: Latency variance
            error_rate: Base error rate
        """
        self.id = channel_id
        self.node_a = node_a
        self.node_b = node_b
        self.bandwidth = bandwidth
        self.latency_base = latency_base
        self.latency_variance = latency_variance
        self.error_rate = error_rate
        self.state = ChannelState.IDLE
        self.metrics = ChannelMetrics()
        self.created_at = time.time()
        self.active_connections: int = 0
    
    @abstractmethod
    def transmit(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, Any]:
        """
        Transmit data over channel.
        
        Args:
            data: Data to transmit
            metadata: Optional transmission metadata
            
        Returns:
            Tuple of (success, latency, received_data)
        """
        pass
    
    @abstractmethod
    def get_estimated_delay(self, data_size: int) -> float:
        """Estimate transmission delay."""
        pass
    
    def get_other_node(self, node_id: str) -> Optional[str]:
        """Get the other endpoint of this channel."""
        if node_id == self.node_a:
            return self.node_b
        elif node_id == self.node_b:
            return self.node_a
        return None
    
    def is_operational(self) -> bool:
        """Check if channel is operational."""
        return self.state in [ChannelState.IDLE, ChannelState.ACTIVE]
    
    def reset_metrics(self) -> None:
        """Reset channel metrics."""
        self.metrics = ChannelMetrics()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize channel to dictionary."""
        return {
            "id": self.id,
            "node_a": self.node_a,
            "node_b": self.node_b,
            "state": self.state.value,
            "bandwidth": self.bandwidth,
            "latency_base": self.latency_base,
            "error_rate": self.error_rate,
            "metrics": {
                "packets_sent": self.metrics.packets_sent,
                "packets_received": self.metrics.packets_received,
                "packets_dropped": self.metrics.packets_dropped,
                "average_latency": self.metrics.average_latency,
                "packet_loss_rate": self.metrics.packet_loss_rate,
            }
        }


class QuantumChannel(Channel):
    """
    Quantum communication channel for qubit transmission.
    
    Models loss, noise, and decoherence in quantum channels.
    Supports both direct qubit transmission and entanglement-based communication.
    """
    
    def __init__(
        self,
        channel_id: str,
        node_a: str,
        node_b: str,
        channel_type: ChannelType = ChannelType.QUANTUM_DIRECT,
        loss_rate: float = 0.01,
        decoherence_rate: float = 0.001,
        max_qubits_buffer: int = 100,
        use_entanglement: bool = False,
        entangled_pair: Optional[EntangledPair] = None,
        **kwargs
    ):
        """
        Initialize quantum channel.
        
        Args:
            channel_id: Channel identifier
            node_a: Source node
            node_b: Destination node
            channel_type: Type of quantum channel
            loss_rate: Photon loss rate per km
            decoherence_rate: Decoherence rate
            max_qubits_buffer: Maximum qubits in transit
            use_entanglement: Whether to use entanglement-assisted communication
            entangled_pair: Pre-shared entangled pair
        """
        super().__init__(channel_id, node_a, node_b, **kwargs)
        self.channel_type = channel_type
        self.loss_rate = loss_rate
        self.decoherence_rate = decoherence_rate
        self.max_qubits_buffer = max_qubits_buffer
        self.qubits_in_transit: List[Qubit] = []
        self.decoherence_simulator = DecoherenceSimulator("exponential")
        self.use_entanglement = use_entanglement
        self.entangled_pair = entangled_pair
        self.fidelity_history: List[float] = []
    
    def transmit(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, Any]:
        """
        Transmit qubits over quantum channel.
        
        Args:
            data: Qubit or list of qubits to transmit
            metadata: Optional transmission metadata
            
        Returns:
            Tuple of (success, latency, received_qubits)
        """
        if not self.is_operational():
            return False, 0.0, None
        
        self.metrics.packets_sent += 1
        self.active_connections += 1
        self.state = ChannelState.ACTIVE
        
        if isinstance(data, Qubit):
            qubits = [data]
        else:
            qubits = data
        
        received_qubits = []
        latency = self.get_estimated_delay(len(qubits))
        
        for qubit in qubits:
            if random.random() < self.loss_rate:
                self.metrics.packets_dropped += 1
                continue
            
            received_qubit = qubit.clone()
            fidelity = self.decoherence_simulator.apply_to_qubit(received_qubit, latency)
            
            if fidelity < 0.5:
                self.metrics.packets_dropped += 1
                continue
            
            received_qubits.append(received_qubit)
        
        self.metrics.packets_received += len(received_qubits)
        self.metrics.total_latency += latency
        self.metrics.total_fidelity_loss += sum(1 - q.fidelity for q in received_qubits)
        self.metrics.last_used = time.time()
        
        self.active_connections = max(0, self.active_connections - 1)
        if self.active_connections == 0:
            self.state = ChannelState.IDLE
        
        return len(received_qubits) > 0, latency, received_qubits
    
    def transmit_with_entanglement(
        self,
        state_to_send: Qubit,
        entangled_pair: Optional[EntangledPair] = None
    ) -> Tuple[bool, float, Optional[Qubit], float]:
        """
        Transmit qubit using entanglement (teleportation).
        
        Args:
            state_to_send: Quantum state to teleport
            entangled_pair: Entangled pair for teleportation
            
        Returns:
            Tuple of (success, latency, teleported_state, fidelity)
        """
        pair = entangled_pair or self.entangled_pair
        
        if not pair or not pair.is_active:
            return False, 0.0, None, 0.0
        
        latency = self.get_estimated_delay(1) + 0.5
        
        if random.random() < self.loss_rate:
            return False, latency, None, 0.0
        
        teleported = state_to_send.clone()
        fidelity = pair.fidelity * state_to_send.fidelity
        
        self.decoherence_simulator.apply_to_qubit(teleported, latency)
        teleported.fidelity = fidelity
        
        self.metrics.packets_sent += 1
        self.metrics.packets_received += 1
        self.metrics.total_latency += latency
        self.metrics.total_fidelity_loss += (1 - fidelity)
        
        return True, latency, teleported, fidelity
    
    def get_estimated_delay(self, data_size: int) -> float:
        """Calculate quantum channel delay."""
        base_delay = self.latency_base / 1000
        variance = random.uniform(-self.latency_variance, self.latency_variance) / 1000
        return max(0.001, base_delay + variance)
    
    def get_channel_loss_probability(self, distance: float) -> float:
        """
        Calculate channel loss probability based on distance.
        
        Args:
            distance: Distance in arbitrary units
            
        Returns:
            Loss probability
        """
        return 1 - math.exp(-self.loss_rate * distance)
    
    def create_entangled_pair(
        self,
        bell_state: BellState = BellState.PHI_PLUS,
        fidelity_target: float = 0.95
    ) -> Optional[EntangledPair]:
        """
        Attempt to create entangled pair over this channel.
        
        Args:
            bell_state: Desired Bell state
            fidelity_target: Target fidelity for the pair
            
        Returns:
            Created entangled pair or None
        """
        latency = self.get_estimated_delay(1)
        
        if random.random() < self.get_channel_loss_probability(latency):
            return None
        
        pair = EntangledPair.create_pair(
            self.node_a,
            self.node_b,
            bell_state,
            time.time()
        )
        
        fidelity = 1.0
        if random.random() < 0.1:
            fidelity = random.uniform(0.7, fidelity_target)
        
        pair.fidelity = fidelity
        self.entangled_pair = pair
        
        return pair
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize quantum channel to dictionary."""
        base = super().to_dict()
        base.update({
            "channel_type": self.channel_type.value,
            "loss_rate": self.loss_rate,
            "decoherence_rate": self.decoherence_rate,
            "use_entanglement": self.use_entanglement,
            "entangled_pair_active": self.entangled_pair.is_active if self.entangled_pair else False,
            "average_fidelity": sum(self.fidelity_history) / len(self.fidelity_history) if self.fidelity_history else 1.0,
        })
        return base


class ClassicalChannel(Channel):
    """
    Classical communication channel over quantum network.
    
    Provides reliable classical communication with quantum-enhanced
    security features.
    """
    
    def __init__(
        self,
        channel_id: str,
        node_a: str,
        node_b: str,
        bandwidth: float = 1000.0,
        is_encrypted: bool = True,
        encryption_key: Optional[str] = None,
        use_quantum_key: bool = False,
        quantum_key_rate: float = 0.0,
        **kwargs
    ):
        """
        Initialize classical channel.
        
        Args:
            channel_id: Channel identifier
            node_a: Source node
            node_b: Destination node
            bandwidth: Bandwidth in Mbps
            is_encrypted: Whether channel uses encryption
            encryption_key: Classical encryption key
            use_quantum_key: Whether to use quantum-generated key
            quantum_key_rate: Rate of quantum key generation
        """
        super().__init__(channel_id, node_a, node_b, bandwidth=bandwidth, **kwargs)
        self.is_encrypted = is_encrypted
        self.encryption_key = encryption_key
        self.use_quantum_key = use_quantum_key
        self.quantum_key_rate = quantum_key_rate
        self.quantum_key_bits: List[int] = []
        self.buffer: List[bytes] = []
    
    def transmit(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, bytes]:
        """
        Transmit data over classical channel.
        
        Args:
            data: Bytes to transmit
            metadata: Optional transmission metadata
            
        Returns:
            Tuple of (success, latency, received_data)
        """
        if not self.is_operational():
            return False, 0.0, b''
        
        self.metrics.packets_sent += 1
        self.active_connections += 1
        self.state = ChannelState.ACTIVE
        
        if isinstance(data, bytes):
            payload = data
        elif isinstance(data, str):
            payload = data.encode('utf-8')
        else:
            payload = str(data).encode('utf-8')
        
        if random.random() < self.error_rate:
            self.metrics.packets_dropped += 1
            self.active_connections = max(0, self.active_connections - 1)
            return False, 0.0, b''
        
        latency = self.get_estimated_delay(len(payload))
        
        if self.is_encrypted:
            payload = self._encrypt(payload)
        
        self.metrics.packets_received += 1
        self.metrics.total_latency += latency
        self.metrics.last_used = time.time()
        
        self.active_connections = max(0, self.active_connections - 1)
        if self.active_connections == 0:
            self.state = ChannelState.IDLE
        
        return True, latency, payload
    
    def get_estimated_delay(self, data_size: int) -> float:
        """Calculate classical channel delay."""
        transmission_time = data_size / (self.bandwidth * 1_000_000)
        queue_delay = random.uniform(0, 0.001)
        base_latency = self.latency_base / 1000
        return transmission_time + queue_delay + base_latency
    
    def _encrypt(self, data: bytes) -> bytes:
        """Simple XOR encryption (placeholder for real crypto)."""
        if not self.encryption_key and not self.quantum_key_bits:
            return data
        
        key = self.encryption_key or ''.join(str(b) for b in self.quantum_key_bits[:8])
        key_bytes = key.encode('utf-8')
        key_len = len(key_bytes)
        
        encrypted = bytearray(data)
        for i in range(len(encrypted)):
            encrypted[i] ^= key_bytes[i % key_len]
        
        return bytes(encrypted)
    
    def add_quantum_key_bits(self, bits: List[int]) -> None:
        """Add quantum-generated key bits for encryption."""
        self.quantum_key_bits.extend(bits)
    
    def get_security_level(self) -> float:
        """
        Get channel security level based on key material.
        
        Returns:
            Security level 0.0 to 1.0
        """
        if not self.is_encrypted:
            return 0.0
        
        if self.use_quantum_key:
            return min(1.0, len(self.quantum_key_bits) / 256)
        
        return 0.5


class ChannelManager:
    """
    Manages multiple channels in a quantum network.
    
    Handles channel creation, routing, and resource allocation.
    """
    
    def __init__(self):
        """Initialize channel manager."""
        self.channels: Dict[str, Channel] = {}
        self.node_channels: Dict[str, List[str]] = {}
    
    def add_channel(self, channel: Channel) -> None:
        """Add channel to manager."""
        self.channels[channel.id] = channel
        
        if channel.node_a not in self.node_channels:
            self.node_channels[channel.node_a] = []
        if channel.node_b not in self.node_channels:
            self.node_channels[channel.node_b] = []
        
        self.node_channels[channel.node_a].append(channel.id)
        self.node_channels[channel.node_b].append(channel.id)
    
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get channel by ID."""
        return self.channels.get(channel_id)
    
    def get_channels_between(self, node_a: str, node_b: str) -> List[Channel]:
        """Get all channels between two nodes."""
        return [
            c for c in self.channels.values()
            if (c.node_a == node_a and c.node_b == node_b) or
               (c.node_a == node_b and c.node_b == node_a)
        ]
    
    def get_node_channels(self, node_id: str) -> List[Channel]:
        """Get all channels connected to a node."""
        channel_ids = self.node_channels.get(node_id, [])
        return [self.channels[cid] for cid in channel_ids if cid in self.channels]
    
    def remove_channel(self, channel_id: str) -> bool:
        """Remove channel from manager."""
        if channel_id not in self.channels:
            return False
        
        channel = self.channels[channel_id]
        if channel.node_a in self.node_channels:
            self.node_channels[channel.node_a].remove(channel_id)
        if channel.node_b in self.node_channels:
            self.node_channels[channel.node_b].remove(channel_id)
        
        del self.channels[channel_id]
        return True
    
    @property
    def total_channels(self) -> int:
        """Total number of channels."""
        return len(self.channels)
    
    @property
    def operational_channels(self) -> int:
        """Number of operational channels."""
        return sum(1 for c in self.channels.values() if c.is_operational())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get channel manager statistics."""
        return {
            "total_channels": self.total_channels,
            "operational_channels": self.operational_channels,
            "quantum_channels": sum(1 for c in self.channels.values() if isinstance(c, QuantumChannel)),
            "classical_channels": sum(1 for c in self.channels.values() if isinstance(c, ClassicalChannel)),
            "total_packets_sent": sum(c.metrics.packets_sent for c in self.channels.values()),
            "total_packets_received": sum(c.metrics.packets_received for c in self.channels.values()),
            "total_packet_loss": sum(c.metrics.packets_dropped for c in self.channels.values()),
        }
