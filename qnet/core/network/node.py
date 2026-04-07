"""
Quantum Node - Network node representation for quantum networks.

Implements nodes with quantum processing capabilities, memory management,
and network communication features for quantum networking simulation.
"""

from __future__ import annotations

import uuid
import time
import random
import math
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Set
from enum import Enum
from collections import defaultdict

from qnet.core.quantum.qubit import Qubit, QuantumRegister, QubitState
from qnet.core.quantum.entanglement import EntangledPair, EntanglementManager, BellState
from qnet.core.quantum.teleportation import QuantumTeleportation, TeleportationResult
from qnet.core.quantum.decoherence import DecoherenceSimulator, DecoherenceResult
from qnet.core.transport.packet import Packet, PacketType, PacketPriority, PacketState
from qnet.core.transport.buffer import PacketBuffer, BufferStrategy
from qnet.core.transport.channel import Channel, QuantumChannel, ClassicalChannel


class NodeType(Enum):
    """Types of quantum network nodes."""
    ENDPOINT = "endpoint"
    RELAY = "relay"
    REPEATER = "repeater"
    MEMORY = "memory"
    GATEWAY = "gateway"
    ROUTER = "router"
    CONTROLLER = "controller"


class NodeState(Enum):
    """Operational states of a network node."""
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    ONLINE = "online"
    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    COMPROMISED = "compromised"


@dataclass
class NodeMetrics:
    """Performance metrics for a node."""
    packets_sent: int = 0
    packets_received: int = 0
    packets_forwarded: int = 0
    qubits_created: int = 0
    qubits_consumed: int = 0
    entanglements_created: int = 0
    entanglements_succeeded: int = 0
    teleportations: int = 0
    teleportation_successes: int = 0
    average_queue_time: float = 0.0
    total_queue_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    uptime: float = 0.0
    last_activity: float = 0.0
    
    @property
    def entanglement_success_rate(self) -> float:
        """Rate of successful entanglement attempts."""
        if self.entanglements_created == 0:
            return 0.0
        return self.entanglements_succeeded / self.entanglements_created
    
    @property
    def teleportation_success_rate(self) -> float:
        """Rate of successful teleportations."""
        if self.teleportations == 0:
            return 0.0
        return self.teleportation_successes / self.teleportations


@dataclass
class QuantumNode:
    """
    Quantum network node with processing capabilities.
    
    Represents a node in the quantum network with quantum memory,
    entanglement generation, and packet routing capabilities.
    
    Attributes:
        node_id: Unique identifier
        node_type: Type of node (endpoint, relay, repeater, etc.)
        position: (x, y, z) coordinates for visualization
        max_qubits: Maximum quantum memory
        max_neighbors: Maximum connected nodes
    """
    
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    node_type: NodeType = NodeType.ENDPOINT
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    max_qubits: int = 1000
    max_neighbors: int = 10
    state: NodeState = NodeState.INITIALIZING
    
    _neighbors: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _quantum_register: QuantumRegister = field(default_factory=QuantumRegister)
    _entanglement_manager: EntanglementManager = field(default_factory=EntanglementManager)
    _teleportation_handler: QuantumTeleportation = field(default_factory=QuantumTeleportation)
    _decoherence_simulator: DecoherenceSimulator = field(default_factory=DecoherenceSimulator)
    _packet_buffer: PacketBuffer = field(default_factory=lambda: PacketBuffer(capacity=1000))
    _routing_table: Dict[str, List[str]] = field(default_factory=dict)
    _channel_manager: Dict[str, Channel] = field(default_factory=dict)
    _metrics: NodeMetrics = field(default_factory=NodeMetrics)
    _created_at: float = field(default_factory=time.time)
    _last_update: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Initialize node components."""
        self._quantum_register.capacity = self.max_qubits
        self.state = NodeState.ONLINE
    
    @property
    def neighbors(self) -> List[str]:
        """Get list of neighbor node IDs."""
        return list(self._neighbors.keys())
    
    @property
    def qubit_count(self) -> int:
        """Current number of qubits in memory."""
        return len(self._quantum_register)
    
    @property
    def available_qubits(self) -> int:
        """Available quantum memory."""
        return self._quantum_register.available_qubits
    
    @property
    def average_fidelity(self) -> float:
        """Average qubit fidelity."""
        return self._quantum_register.average_fidelity
    
    @property
    def active_entanglements(self) -> int:
        """Number of active entangled pairs."""
        return self._entanglement_manager.active_pairs
    
    @property
    def uptime(self) -> float:
        """Node uptime in seconds."""
        return time.time() - self._created_at
    
    def create_qubit(self, state: Optional[Qubit] = None) -> Optional[Qubit]:
        """
        Create a new qubit in quantum memory.
        
        Args:
            state: Optional initial state (random if not provided)
            
        Returns:
            Created qubit or None if memory full
        """
        if self._quantum_register.available_qubits <= 0:
            return None
        
        qubit = state if state else Qubit.random()
        qubit.location = self.node_id
        qubit.created_at = time.time()
        
        if self._quantum_register.add_qubit(qubit):
            self._metrics.qubits_created += 1
            self._metrics.last_activity = time.time()
            return qubit
        return None
    
    def consume_qubit(self, qubit_id: str) -> Optional[Qubit]:
        """
        Remove and return qubit from memory.
        
        Args:
            qubit_id: ID of qubit to consume
            
        Returns:
            Removed qubit or None
        """
        qubit = self._quantum_register.remove_qubit(qubit_id)
        if qubit:
            self._metrics.qubits_consumed += 1
        return qubit
    
    def create_entanglement(self, target_node_id: str, bell_state: BellState = BellState.PHI_PLUS) -> Optional[EntangledPair]:
        """
        Create entanglement with target node.
        
        Args:
            target_node_id: ID of target node
            bell_state: Desired Bell state
            
        Returns:
            Created entangled pair or None
        """
        pair = self._entanglement_manager.create_pair(
            self.node_id,
            target_node_id,
            bell_state,
            time.time()
        )
        
        if pair:
            self._metrics.entanglements_created += 1
            self._metrics.entanglements_succeeded += 1
            self._metrics.last_activity = time.time()
        else:
            self._metrics.entanglements_created += 1
        
        return pair
    
    def teleport_qubit(self, qubit: Qubit, target_node_id: str) -> TeleportationResult:
        """
        Teleport qubit to target node using entanglement.
        
        Args:
            qubit: Qubit to teleport
            target_node_id: Destination node
            
        Returns:
            Teleportation result
        """
        available_pairs = self._entanglement_manager.get_active_pairs_for_node(target_node_id)
        
        if not available_pairs:
            return TeleportationResult(
                success=False,
                original_state=qubit,
                status=TeleportationStatus.FAILED,
                error_message="No entanglement available"
            )
        
        pair = available_pairs[0]
        result = self._teleportation_handler.teleport(
            qubit,
            pair,
            self.node_id,
            target_node_id,
            time.time()
        )
        
        self._metrics.teleportations += 1
        if result.success:
            self._metrics.teleportation_successes += 1
        
        return result
    
    def send_packet(self, packet: Packet) -> bool:
        """
        Add packet to send queue.
        
        Args:
            packet: Packet to send
            
        Returns:
            True if packet was queued
        """
        try:
            self._packet_buffer.add(packet)
            self._metrics.last_activity = time.time()
            return True
        except Exception:
            return False
    
    def receive_packet(self, packet: Packet) -> bool:
        """
        Process received packet.
        
        Args:
            packet: Received packet
            
        Returns:
            True if packet was processed successfully
        """
        self._metrics.packets_received += 1
        self._metrics.last_activity = time.time()
        
        if packet.header.destination_id == self.node_id:
            return True
        
        return self.forward_packet(packet)
    
    def forward_packet(self, packet: Packet) -> bool:
        """
        Forward packet to next hop.
        
        Args:
            packet: Packet to forward
            
        Returns:
            True if packet was forwarded
        """
        if not packet.decrement_ttl() or not packet.decrement_hops():
            packet.state = PacketState.FAILED
            return False
        
        next_hop = self._get_next_hop(packet.header.destination_id)
        
        if not next_hop:
            packet.state = PacketState.FAILED
            return False
        
        packet.add_to_path(self.node_id)
        self._metrics.packets_forwarded += 1
        
        channel = self._channel_manager.get(next_hop)
        if channel:
            success, _, _ = channel.transmit(packet.payload)
            return success
        
        return False
    
    def _get_next_hop(self, destination: str) -> Optional[str]:
        """Get next hop for destination using routing table."""
        if destination in self._routing_table:
            path = self._routing_table[destination]
            return path[0] if path else None
        return None
    
    def add_neighbor(self, neighbor_id: str, channel: Optional[Channel] = None, **kwargs) -> bool:
        """
        Add neighbor connection.
        
        Args:
            neighbor_id: Neighbor node ID
            channel: Optional channel to neighbor
            
        Returns:
            True if neighbor was added
        """
        if len(self._neighbors) >= self.max_neighbors:
            return False
        
        self._neighbors[neighbor_id] = {
            'channel': channel,
            'connected_at': time.time(),
            'latency': kwargs.get('latency', random.uniform(1, 10)),
            'bandwidth': kwargs.get('bandwidth', 1000),
            'is_quantum': kwargs.get('is_quantum', True),
            **kwargs
        }
        
        if channel:
            self._channel_manager[neighbor_id] = channel
        
        return True
    
    def remove_neighbor(self, neighbor_id: str) -> bool:
        """Remove neighbor connection."""
        if neighbor_id in self._neighbors:
            del self._neighbors[neighbor_id]
            if neighbor_id in self._channel_manager:
                del self._channel_manager[neighbor_id]
            return True
        return False
    
    def update_routing_table(self, destination: str, path: List[str], metric: float) -> None:
        """
        Update routing table entry.
        
        Args:
            destination: Destination node ID
            path: Path to destination
            metric: Routing metric value
        """
        self._routing_table[destination] = path
    
    def apply_decoherence(self, time_elapsed: float) -> float:
        """
        Apply decoherence to all qubits.
        
        Args:
            time_elapsed: Time since last update
            
        Returns:
            New average fidelity
        """
        avg_fidelity = self._quantum_register.apply_decoherence_to_all(
            self._decoherence_simulator.active_model.decay_rate,
            time_elapsed
        )
        
        self._entanglement_manager.apply_decoherence_all(
            self._decoherence_simulator.active_model.decay_rate,
            time_elapsed
        )
        
        self._last_update = time.time()
        
        if avg_fidelity < 0.5:
            self.state = NodeState.DEGRADED
        
        return avg_fidelity
    
    def get_distance_to(self, other: QuantumNode) -> float:
        """Calculate Euclidean distance to another node."""
        dx = self.position[0] - other.position[0]
        dy = self.position[1] - other.position[1]
        dz = self.position[2] - other.position[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "position": list(self.position),
            "state": self.state.value,
            "neighbors": self.neighbors,
            "qubit_count": self.qubit_count,
            "available_qubits": self.available_qubits,
            "active_entanglements": self.active_entanglements,
            "average_fidelity": self.average_fidelity,
            "packet_queue_size": len(self._packet_buffer),
            "metrics": {
                "packets_sent": self._metrics.packets_sent,
                "packets_received": self._metrics.packets_received,
                "teleportations": self._metrics.teleportations,
                "entanglement_success_rate": self._metrics.entanglement_success_rate,
            },
            "uptime": self.uptime,
        }
    
    def __repr__(self) -> str:
        return f"QuantumNode({self.node_id}, type={self.node_type.value}, qubits={self.qubit_count})"


@dataclass
class NodeCluster:
    """
    Cluster of related quantum nodes.
    
    Groups nodes for efficient management and
    collective operations.
    """
    
    cluster_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Cluster"
    nodes: List[QuantumNode] = field(default_factory=list)
    master_node: Optional[str] = None
    
    def add_node(self, node: QuantumNode) -> bool:
        """Add node to cluster."""
        if node.node_id in [n.node_id for n in self.nodes]:
            return False
        self.nodes.append(node)
        if self.master_node is None:
            self.master_node = node.node_id
        return True
    
    def remove_node(self, node_id: str) -> bool:
        """Remove node from cluster."""
        self.nodes = [n for n in self.nodes if n.node_id != node_id]
        if self.master_node == node_id:
            self.master_node = self.nodes[0].node_id if self.nodes else None
        return True
    
    @property
    def total_qubits(self) -> int:
        """Total qubits across all nodes."""
        return sum(n.qubit_count for n in self.nodes)
    
    @property
    def average_fidelity(self) -> float:
        """Average fidelity across all nodes."""
        if not self.nodes:
            return 1.0
        return sum(n.average_fidelity for n in self.nodes) / len(self.nodes)


from qnet.core.quantum.teleportation import TeleportationStatus
