"""
Quantum Link - Connection between quantum network nodes.

Implements various link types for connecting quantum nodes,
including direct quantum links, entanglement links, and
classical fallback connections.
"""

from __future__ import annotations

import uuid
import time
import random
import math
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Callable
from enum import Enum
from abc import ABC, abstractmethod

from qnet.core.quantum.qubit import Qubit
from qnet.core.quantum.entanglement import EntangledPair, BellState
from qnet.core.transport.channel import Channel, QuantumChannel, ClassicalChannel, ChannelState


class LinkType(Enum):
    """Types of links between quantum nodes."""
    QUANTUM_DIRECT = "quantum_direct"
    QUANTUM_ENTANGLED = "quantum_entangled"
    QUANTUM_REPEATER = "quantum_repeater"
    CLASSICAL = "classical"
    HYBRID = "hybrid"


class LinkState(Enum):
    """State of a quantum link."""
    IDLE = "idle"
    ACTIVE = "active"
    ESTABLISHING = "establishing"
    FAILED = "failed"
    DEGRADED = "degraded"


@dataclass
class LinkMetrics:
    """Performance metrics for a link."""
    packets_transmitted: int = 0
    packets_received: int = 0
    qubits_transmitted: int = 0
    qubits_received: int = 0
    entanglement_attempts: int = 0
    entanglement_successes: int = 0
    total_latency: float = 0.0
    total_fidelity_loss: float = 0.0
    uptime: float = 0.0
    last_used: float = 0.0
    
    @property
    def entanglement_success_rate(self) -> float:
        """Rate of successful entanglement generation."""
        if self.entanglement_attempts == 0:
            return 0.0
        return self.entanglement_successes / self.entanglement_attempts
    
    @property
    def average_latency(self) -> float:
        """Average transmission latency."""
        if self.packets_transmitted == 0:
            return 0.0
        return self.total_latency / self.packets_transmitted
    
    @property
    def throughput(self) -> float:
        """Throughput in qubits per second."""
        if self.uptime == 0:
            return 0.0
        return self.qubits_received / self.uptime


class QuantumLink:
    """
    Quantum link connecting two network nodes.
    
    Manages both quantum and classical communication channels,
    entanglement generation, and link-level operations.
    
    Attributes:
        link_id: Unique identifier
        node_a: First endpoint
        node_b: Second endpoint
        link_type: Type of quantum link
    """
    
    def __init__(
        self,
        link_id: str,
        node_a: str,
        node_b: str,
        link_type: LinkType = LinkType.QUANTUM_ENTANGLED,
        distance: float = 1.0,
        latency: float = 5.0,
        bandwidth: float = 1000.0,
        error_rate: float = 0.001,
        quantum_channel: Optional[QuantumChannel] = None,
        classical_channel: Optional[ClassicalChannel] = None,
    ):
        """
        Initialize quantum link.
        
        Args:
            link_id: Unique link identifier
            node_a: First node ID
            node_b: Second node ID
            link_type: Type of link
            distance: Physical distance (arbitrary units)
            latency: Base latency in ms
            bandwidth: Channel bandwidth
            error_rate: Base error rate
            quantum_channel: Pre-configured quantum channel
            classical_channel: Pre-configured classical channel
        """
        self.link_id = link_id
        self.node_a = node_a
        self.node_b = node_b
        self.link_type = link_type
        self.distance = distance
        self.latency = latency
        self.bandwidth = bandwidth
        self.error_rate = error_rate
        
        self.state = LinkState.IDLE
        self.created_at = time.time()
        self.last_activity = time.time()
        self._metrics = LinkMetrics()
        
        self.quantum_channel = quantum_channel or QuantumChannel(
            channel_id=f"{link_id}_q",
            node_a=node_a,
            node_b=node_b,
            latency_base=latency,
            loss_rate=0.01 * distance,
        )
        
        self.classical_channel = classical_channel or ClassicalChannel(
            channel_id=f"{link_id}_c",
            node_a=node_a,
            node_b=node_b,
            bandwidth=bandwidth,
            latency_base=latency * 0.1,
        )
        
        self.entangled_pairs: List[EntangledPair] = []
        self.max_entangled_pairs = 100
    
    @property
    def is_active(self) -> bool:
        """Check if link is active."""
        return self.state == LinkState.ACTIVE
    
    @property
    def is_operational(self) -> bool:
        """Check if link is operational."""
        return self.state not in [LinkState.FAILED, LinkState.IDLE]
    
    @property
    def available_pairs(self) -> int:
        """Number of available entangled pairs."""
        return sum(1 for p in self.entangled_pairs if p.is_active)
    
    @property
    def average_fidelity(self) -> float:
        """Average fidelity of entangled pairs."""
        if not self.entangled_pairs:
            return 1.0
        return sum(p.fidelity for p in self.entangled_pairs) / len(self.entangled_pairs)
    
    @property
    def uptime(self) -> float:
        """Link uptime in seconds."""
        return time.time() - self.created_at
    
    def establish(self) -> bool:
        """
        Establish link connection.
        
        Returns:
            True if link was established
        """
        if self.state == LinkState.ACTIVE:
            return True
        
        self.state = LinkState.ESTABLISHING
        
        try:
            self.quantum_channel.state = ChannelState.ACTIVE
            self.classical_channel.state = ChannelState.ACTIVE
            self.state = LinkState.ACTIVE
            self.last_activity = time.time()
            return True
        except Exception:
            self.state = LinkState.FAILED
            return False
    
    def disconnect(self) -> None:
        """Disconnect link."""
        self.state = LinkState.IDLE
        self.quantum_channel.state = ChannelState.IDLE
        self.classical_channel.state = ChannelState.IDLE
    
    def create_entanglement(self, bell_state: BellState = BellState.PHI_PLUS) -> Optional[EntangledPair]:
        """
        Create entangled pair across this link.
        
        Args:
            bell_state: Desired Bell state
            
        Returns:
            Created entangled pair or None
        """
        if len(self.entangled_pairs) >= self.max_entangled_pairs:
            return None
        
        self._metrics.entanglement_attempts += 1
        
        success, latency, received_qubits, fidelity = self.quantum_channel.transmit_with_entanglement(
            Qubit.random(),
            self.quantum_channel.entangled_pair
        )
        
        if not success:
            return None
        
        pair = EntangledPair.create_pair(
            self.node_a,
            self.node_b,
            bell_state,
            time.time()
        )
        pair.fidelity = fidelity
        
        self.entangled_pairs.append(pair)
        self._metrics.entanglement_successes += 1
        self.last_activity = time.time()
        
        return pair
    
    def transmit_qubit(self, qubit: Qubit, use_entanglement: bool = True) -> Tuple[bool, float, Optional[Qubit]]:
        """
        Transmit qubit over link.
        
        Args:
            qubit: Qubit to transmit
            use_entanglement: Whether to use entanglement-assisted transmission
            
        Returns:
            Tuple of (success, latency, received_qubit)
        """
        if use_entanglement and self.available_pairs > 0:
            pair = next(p for p in self.entangled_pairs if p.is_active)
            success, latency, received, fidelity = self.quantum_channel.transmit_with_entanglement(
                qubit, pair
            )
            self._metrics.qubits_transmitted += 1
            self._metrics.qubits_received += 1 if success else 0
            self._metrics.total_latency += latency
            return success, latency, received
        
        success, latency, received = self.quantum_channel.transmit(qubit)
        
        if success and received:
            self._metrics.qubits_transmitted += 1
            self._metrics.qubits_received += len(received)
        
        self._metrics.total_latency += latency
        self.last_activity = time.time()
        
        return success, latency, received[0] if received else None
    
    def transmit_classical(self, data: bytes) -> Tuple[bool, float, bytes]:
        """
        Transmit classical data over link.
        
        Args:
            data: Bytes to transmit
            
        Returns:
            Tuple of (success, latency, received_data)
        """
        success, latency, received = self.classical_channel.transmit(data)
        
        self._metrics.packets_transmitted += 1
        self._metrics.packets_received += 1 if success else 0
        self._metrics.total_latency += latency
        self.last_activity = time.time()
        
        return success, latency, received
    
    def get_pair_for_route(self) -> Optional[EntangledPair]:
        """Get available entangled pair for routing."""
        for pair in self.entangled_pairs:
            if pair.is_active and pair.fidelity > 0.7:
                return pair
        return None
    
    def purify_pairs(self, target_fidelity: float = 0.95) -> int:
        """
        Attempt purification on entangled pairs.
        
        Args:
            target_fidelity: Target fidelity threshold
            
        Returns:
            Number of pairs that met target
        """
        purified = 0
        remaining = [p for p in self.entangled_pairs if p.is_active]
        
        while len(remaining) >= 2:
            p1 = remaining.pop(0)
            p2 = remaining.pop(0)
            
            if p1.purify(p2):
                purified += 1
                if p1.fidelity >= target_fidelity:
                    remaining.insert(0, p1)
            else:
                self.entangled_pairs.remove(p1)
                self.entangled_pairs.remove(p2)
        
        return purified
    
    def apply_decoherence(self, time_elapsed: float) -> float:
        """
        Apply decoherence to all entangled pairs.
        
        Args:
            time_elapsed: Time since last update
            
        Returns:
            New average fidelity
        """
        total_fidelity_loss = 0.0
        
        for pair in self.entangled_pairs:
            old_fidelity = pair.fidelity
            pair.apply_decoherence(0.001, time_elapsed)
            total_fidelity_loss += old_fidelity - pair.fidelity
        
        self._metrics.total_fidelity_loss = total_fidelity_loss
        
        if self.average_fidelity < 0.5:
            self.state = LinkState.DEGRADED
        
        return self.average_fidelity
    
    def get_other_node(self, node_id: str) -> Optional[str]:
        """Get the other endpoint of this link."""
        if node_id == self.node_a:
            return self.node_b
        elif node_id == self.node_b:
            return self.node_a
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize link to dictionary."""
        return {
            "link_id": self.link_id,
            "node_a": self.node_a,
            "node_b": self.node_b,
            "link_type": self.link_type.value,
            "state": self.state.value,
            "distance": self.distance,
            "latency": self.latency,
            "bandwidth": self.bandwidth,
            "available_pairs": self.available_pairs,
            "average_fidelity": self.average_fidelity,
            "metrics": {
                "entanglement_success_rate": self._metrics.entanglement_success_rate,
                "average_latency": self._metrics.average_latency,
                "throughput": self._metrics.throughput,
            },
            "uptime": self.uptime,
        }
    
    def __repr__(self) -> str:
        return f"QuantumLink({self.link_id}, {self.node_a}↔{self.node_b}, fidelity={self.average_fidelity:.3f})"


class LinkManager:
    """
    Manages multiple quantum links.
    
    Handles link creation, routing, and resource allocation
    across the quantum network.
    """
    
    def __init__(self):
        """Initialize link manager."""
        self.links: Dict[str, QuantumLink] = {}
        self.node_links: Dict[str, List[str]] = {}
    
    def add_link(self, link: QuantumLink) -> None:
        """Add link to manager."""
        self.links[link.link_id] = link
        
        if link.node_a not in self.node_links:
            self.node_links[link.node_a] = []
        if link.node_b not in self.node_links:
            self.node_links[link.node_b] = []
        
        self.node_links[link.node_a].append(link.link_id)
        self.node_links[link.node_b].append(link.link_id)
    
    def get_link(self, link_id: str) -> Optional[QuantumLink]:
        """Get link by ID."""
        return self.links.get(link_id)
    
    def get_links_between(self, node_a: str, node_b: str) -> List[QuantumLink]:
        """Get all links between two nodes."""
        return [
            link for link in self.links.values()
            if (link.node_a == node_a and link.node_b == node_b) or
               (link.node_a == node_b and link.node_b == node_a)
        ]
    
    def get_node_links(self, node_id: str) -> List[QuantumLink]:
        """Get all links connected to a node."""
        link_ids = self.node_links.get(node_id, [])
        return [self.links[lid] for lid in link_ids if lid in self.links]
    
    def remove_link(self, link_id: str) -> bool:
        """Remove link from manager."""
        if link_id not in self.links:
            return False
        
        link = self.links[link_id]
        if link.node_a in self.node_links:
            self.node_links[link.node_a].remove(link_id)
        if link.node_b in self.node_links:
            self.node_links[link.node_b].remove(link_id)
        
        del self.links[link_id]
        return True
    
    def create_link(
        self,
        node_a: str,
        node_b: str,
        link_type: LinkType = LinkType.QUANTUM_ENTANGLED,
        **kwargs
    ) -> QuantumLink:
        """Create and add new link."""
        link_id = str(uuid.uuid4())[:8]
        link = QuantumLink(
            link_id=link_id,
            node_a=node_a,
            node_b=node_b,
            link_type=link_type,
            **kwargs
        )
        self.add_link(link)
        return link
    
    @property
    def total_links(self) -> int:
        """Total number of links."""
        return len(self.links)
    
    @property
    def active_links(self) -> int:
        """Number of active links."""
        return sum(1 for l in self.links.values() if l.is_active)
    
    @property
    def total_entangled_pairs(self) -> int:
        """Total entangled pairs across all links."""
        return sum(l.available_pairs for l in self.links.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get link manager statistics."""
        return {
            "total_links": self.total_links,
            "active_links": self.active_links,
            "total_entangled_pairs": self.total_entangled_pairs,
            "average_fidelity": sum(l.average_fidelity for l in self.links.values()) / max(1, len(self.links)),
            "link_types": {
                lt.value: sum(1 for l in self.links.values() if l.link_type == lt)
                for lt in LinkType
            },
        }
