"""
Quantum Packet - Data structures for quantum network packets.

Implements various packet types for both quantum and classical
communication in the QNet protocol stack.
"""

from __future__ import annotations

import uuid
import struct
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Tuple
from enum import Enum
from abc import ABC, abstractmethod

from qnet.core.quantum.qubit import Qubit
from qnet.core.quantum.entanglement import EntangledPair, BellState


class PacketType(Enum):
    """
    Types of packets in QNet protocol.
    
    Quantum packets carry qubits or entanglement-related data.
    Classical packets handle routing, control, and acknowledgments.
    """
    QUANTUM_DATA = 0x01
    ENTANGLEMENT_REQUEST = 0x02
    ENTANGLEMENT_RESPONSE = 0x03
    ENTANGLEMENT_PURIFY = 0x04
    QUBIT_TELEPORT = 0x05
    KEY_BIT = 0x10
    KEY_AGREEMENT = 0x11
    ROUTING_UPDATE = 0x20
    PACKET_ACK = 0x30
    PACKET_NACK = 0x31
    HEARTBEAT = 0x40
    ATTACK_ALERT = 0x50
    TOPOLOGY_UPDATE = 0x60
    CONTROL_MESSAGE = 0x70


class PacketPriority(Enum):
    """Packet priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class PacketState(Enum):
    """Packet delivery state."""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    DROPPED = "dropped"


@dataclass
class PacketHeader:
    """
    Header structure for QNet packets.
    
    Contains all metadata needed for routing and delivery.
    """
    packet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    packet_type: PacketType = PacketType.QUANTUM_DATA
    priority: PacketPriority = PacketPriority.NORMAL
    source_id: str = ""
    destination_id: str = ""
    ttl: int = 64
    hop_limit: int = 64
    sequence_number: int = 0
    timestamp: float = field(default_factory=time.time)
    path: List[str] = field(default_factory=list)
    encryption_key_id: Optional[str] = None
    quantum_header: Optional[Dict[str, Any]] = None
    
    def to_bytes(self) -> bytes:
        """Serialize header to bytes."""
        return struct.pack(
            '!HH64s64sBBBBIBB',
            0x514E,  # Magic number 'QN'
            self.packet_type.value,
            self.source_id.encode('utf-8')[:32].ljust(32, b'\x00'),
            self.destination_id.encode('utf-8')[:32].ljust(32, b'\x00'),
            self.priority.value,
            self.ttl,
            self.hop_limit,
            self.sequence_number,
            0,  # Reserved
            0,  # Reserved
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> PacketHeader:
        """Deserialize header from bytes."""
        magic, ptype, source, dest, priority, ttl, hop, seq, _, _ = struct.unpack(
            '!HH64s64sBBBBIBB', data
        )
        return cls(
            packet_type=PacketType(ptype),
            source_id=source.decode('utf-8').rstrip('\x00'),
            destination_id=dest.decode('utf-8').rstrip('\x00'),
            priority=PacketPriority(priority),
            ttl=ttl,
            hop_limit=hop,
            sequence_number=seq,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "packet_id": self.packet_id,
            "packet_type": self.packet_type.name,
            "priority": self.priority.name,
            "source_id": self.source_id,
            "destination_id": self.destination_id,
            "ttl": self.ttl,
            "hop_limit": self.hop_limit,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
            "path": self.path,
        }


class Packet(ABC):
    """
    Abstract base class for all QNet packets.
    
    Provides common functionality for packet creation,
    serialization, and routing information.
    """
    
    HEADER_SIZE = 128
    
    def __init__(
        self,
        header: PacketHeader,
        payload: Optional[bytes] = None,
        qubits: Optional[List[Qubit]] = None,
        entangled_pairs: Optional[List[EntangledPair]] = None,
    ):
        """
        Initialize packet.
        
        Args:
            header: Packet header with routing info
            payload: Classical data payload
            qubits: Quantum data (qubits to transmit)
            entangled_pairs: Entangled pairs to share
        """
        self.header = header
        self.payload = payload or b''
        self.qubits = qubits or []
        self.entangled_pairs = entangled_pairs or []
        self.state = PacketState.PENDING
        self.created_at = time.time()
        self.delivered_at: Optional[float] = None
        self.attempts = 0
        self.path_history: List[str] = []
    
    @property
    def size(self) -> int:
        """Total packet size in bytes."""
        return self.HEADER_SIZE + len(self.payload)
    
    @property
    def is_quantum(self) -> bool:
        """Check if packet contains quantum data."""
        return bool(self.qubits or self.entangled_pairs)
    
    @property
    def is_expired(self) -> bool:
        """Check if packet TTL has expired."""
        return self.header.ttl <= 0
    
    @property
    def is_hop_expired(self) -> bool:
        """Check if hop limit has expired."""
        return self.header.hop_limit <= 0
    
    def decrement_ttl(self) -> bool:
        """Decrement TTL and return False if expired."""
        self.header.ttl -= 1
        return self.header.ttl > 0
    
    def decrement_hops(self) -> bool:
        """Decrement hop limit and return False if expired."""
        self.header.hop_limit -= 1
        return self.header.hop_limit > 0
    
    def add_to_path(self, node_id: str) -> None:
        """Record node visit."""
        self.path_history.append(node_id)
        self.header.path.append(node_id)
    
    @abstractmethod
    def to_bytes(self) -> bytes:
        """Serialize packet to bytes."""
        pass
    
    @abstractmethod
    def get_estimated_delay(self) -> float:
        """Estimate transmission delay."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize packet to dictionary."""
        return {
            "header": self.header.to_dict(),
            "payload_size": len(self.payload),
            "qubit_count": len(self.qubits),
            "entangled_pair_count": len(self.entangled_pairs),
            "state": self.state.value,
            "size": self.size,
            "is_quantum": self.is_quantum,
            "path_history": self.path_history,
        }


@dataclass
class QuantumPacket(Packet):
    """
    Packet carrying quantum information (qubits).
    
    Used for quantum state transfer and teleportation protocols.
    """
    
    def __init__(
        self,
        header: PacketHeader,
        qubits: List[Qubit],
        teleportation_required: bool = False,
        fidelity_requirement: float = 0.9,
    ):
        """
        Initialize quantum packet.
        
        Args:
            header: Packet header
            qubits: List of qubits to transmit
            teleportation_required: Whether teleportation is needed
            fidelity_requirement: Minimum fidelity for delivery
        """
        super().__init__(header, qubits=qubits)
        self.teleportation_required = teleportation_required
        self.fidelity_requirement = fidelity_requirement
        self.average_fidelity = sum(q.fidelity for q in qubits) / len(qubits) if qubits else 1.0
        self.requires_entanglement = teleportation_required or len(qubits) > 0
    
    def to_bytes(self) -> bytes:
        """Serialize quantum packet."""
        header_bytes = self.header.to_bytes()
        qubit_data = b''
        for q in self.qubits:
            qubit_data += struct.pack('!dd', q.alpha.real, q.beta.real)
            qubit_data += struct.pack('!dd', q.alpha.imag, q.beta.imag)
        return header_bytes + self.payload + qubit_data
    
    def get_estimated_delay(self) -> float:
        """Quantum packets have variable delay based on teleportation."""
        base_delay = 0.1
        if self.teleportation_required:
            base_delay += 0.5
        base_delay += len(self.qubits) * 0.01
        return base_delay * (1 / max(0.1, self.average_fidelity))
    
    @property
    def delivery_probability(self) -> float:
        """Probability of successful delivery."""
        return self.average_fidelity * (1.0 if not self.teleportation_required else 0.8)


@dataclass
class ClassicalPacket(Packet):
    """
    Packet carrying classical information.
    
    Used for routing updates, acknowledgments, and control messages.
    """
    
    def __init__(
        self,
        header: PacketHeader,
        payload: bytes,
        ack_requested: bool = False,
        reliability_required: bool = False,
    ):
        """
        Initialize classical packet.
        
        Args:
            header: Packet header
            payload: Data payload
            ack_requested: Whether acknowledgment is needed
            reliability_required: Whether reliable delivery is required
        """
        super().__init__(header, payload=payload)
        self.ack_requested = ack_requested
        self.reliability_required = reliability_required
    
    def to_bytes(self) -> bytes:
        """Serialize classical packet."""
        header_bytes = self.header.to_bytes()
        return header_bytes + self.payload
    
    def get_estimated_delay(self) -> float:
        """Classical packets have predictable delay."""
        bandwidth_factor = max(1, len(self.payload) / 1024)
        return 0.001 * bandwidth_factor


@dataclass
class EntanglementPacket(Packet):
    """
    Packet for entanglement distribution and management.
    
    Contains entangled pairs for sharing between nodes.
    """
    
    def __init__(
        self,
        header: PacketHeader,
        entangled_pairs: List[EntangledPair],
        bell_state: BellState = BellState.PHI_PLUS,
        purification_enabled: bool = False,
    ):
        """
        Initialize entanglement packet.
        
        Args:
            header: Packet header
            entangled_pairs: List of entangled pairs to share
            bell_state: Desired Bell state
            purification_enabled: Whether purification should be attempted
        """
        super().__init__(header, entangled_pairs=entangled_pairs)
        self.bell_state = bell_state
        self.purification_enabled = purification_enabled
        self.pair_fidelities = [p.fidelity for p in entangled_pairs]
    
    def to_bytes(self) -> bytes:
        """Serialize entanglement packet."""
        header_bytes = self.header.to_bytes()
        pair_data = b''
        for p in self.entangled_pairs:
            pair_data += struct.pack('!B', p.bell_state.value.value)
            pair_data += struct.pack('!d', p.fidelity)
        return header_bytes + self.payload + pair_data
    
    def get_estimated_delay(self) -> float:
        """Entanglement packets have significant setup delay."""
        base_delay = 0.2
        base_delay += len(self.entangled_pairs) * 0.05
        if self.purification_enabled:
            base_delay *= 2
        return base_delay


@dataclass
class KeyExchangePacket(Packet):
    """
    Packet for quantum key distribution (QKD).
    
    Carries key bits and reconciliation data.
    """
    
    def __init__(
        self,
        header: PacketHeader,
        key_bits: List[int],
        basis: List[str],
        key_id: str,
        protocol: str = "bb84",
    ):
        """
        Initialize key exchange packet.
        
        Args:
            header: Packet header
            key_bits: List of key bits (0 or 1)
            basis: Measurement bases for each bit
            key_id: Unique identifier for this key
            protocol: QKD protocol name
        """
        super().__init__(header, payload=bytes(key_bits))
        self.key_bits = key_bits
        self.basis = basis
        self.key_id = key_id
        self.protocol = protocol
        self.check_bits: List[Tuple[int, int]] = []
    
    def to_bytes(self) -> bytes:
        """Serialize key exchange packet."""
        header_bytes = self.header.to_bytes()
        key_bytes = bytes(self.key_bits)
        basis_bytes = ','.join(self.basis).encode('utf-8')
        return header_bytes + key_bytes + basis_bytes
    
    def add_check_bits(self, positions: List[int], values: List[int]) -> None:
        """Add check bits for eavesdropping detection."""
        self.check_bits = list(zip(positions, values))
    
    def get_key_bits_remaining(self) -> int:
        """Get number of key bits excluding check bits."""
        check_positions = set(p for p, _ in self.check_bits)
        return len(self.key_bits) - len(check_positions)


class PacketBuilder:
    """
    Builder class for constructing packets with fluent interface.
    
    Simplifies packet creation with method chaining.
    """
    
    def __init__(self, packet_type: PacketType):
        """Initialize builder with packet type."""
        self._type = packet_type
        self._header = PacketHeader(packet_type=packet_type)
        self._payload: Optional[bytes] = None
        self._qubits: List[Qubit] = []
        self._pairs: List[EntangledPair] = []
        self._priority = PacketPriority.NORMAL
    
    def source(self, node_id: str) -> PacketBuilder:
        """Set source node."""
        self._header.source_id = node_id
        return self
    
    def destination(self, node_id: str) -> PacketBuilder:
        """Set destination node."""
        self._header.destination_id = node_id
        return self
    
    def priority(self, priority: PacketPriority) -> PacketBuilder:
        """Set packet priority."""
        self._priority = priority
        self._header.priority = priority
        return self
    
    def ttl(self, ttl: int) -> PacketBuilder:
        """Set TTL."""
        self._header.ttl = ttl
        self._header.hop_limit = ttl
        return self
    
    def payload(self, data: bytes) -> PacketBuilder:
        """Set payload."""
        self._payload = data
        return self
    
    def qubits(self, qubits: List[Qubit]) -> PacketBuilder:
        """Add qubits."""
        self._qubits = qubits
        return self
    
    def entangled_pairs(self, pairs: List[EntangledPair]) -> PacketBuilder:
        """Add entangled pairs."""
        self._pairs = pairs
        return self
    
    def build(self) -> Packet:
        """Build and return appropriate packet type."""
        if self._type == PacketType.QUANTUM_DATA:
            return QuantumPacket(self._header, self._qubits)
        elif self._type == PacketType.ENTANGLEMENT_REQUEST:
            return EntanglementPacket(self._header, self._pairs)
        elif self._type in [PacketType.KEY_BIT, PacketType.KEY_AGREEMENT]:
            return KeyExchangePacket(
                self._header,
                list(self._payload) if self._payload else [],
                [],
                self._header.packet_id
            )
        else:
            return ClassicalPacket(self._header, self._payload or b'')


def create_packet(
    packet_type: PacketType,
    source: str,
    destination: str,
    **kwargs
) -> Packet:
    """
    Factory function to create packets.
    
    Args:
        packet_type: Type of packet to create
        source: Source node ID
        destination: Destination node ID
        **kwargs: Additional packet-specific arguments
        
    Returns:
        Configured Packet instance
    """
    builder = PacketBuilder(packet_type).source(source).destination(destination)
    
    if 'priority' in kwargs:
        builder = builder.priority(kwargs['priority'])
    if 'ttl' in kwargs:
        builder = builder.ttl(kwargs['ttl'])
    if 'payload' in kwargs:
        builder = builder.payload(kwargs['payload'])
    if 'qubits' in kwargs:
        builder = builder.qubits(kwargs['qubits'])
    if 'entangled_pairs' in kwargs:
        builder = builder.entangled_pairs(kwargs['entangled_pairs'])
    
    return builder.build()
