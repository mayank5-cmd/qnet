"""
Simulation Engine - Core simulation loop and management.

Implements event-driven simulation for quantum networks with support
for large-scale networks (10-10,000+ nodes).
"""

from __future__ import annotations

import time
import threading
import logging
import asyncio
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Set, Tuple
from enum import Enum
from collections import deque
import random

from qnet.core.network.topology import NetworkTopology, TopologyConfig, TopologyType
from qnet.core.network.node import QuantumNode, NodeState
from qnet.core.network.link import QuantumLink
from qnet.core.transport.packet import Packet, PacketType, PacketState, create_packet
from qnet.core.transport.buffer import PacketBuffer
from qnet.core.simulation.scheduler import EventScheduler, SimulationEvent, EventType
from qnet.core.simulation.monitor import SimulationMonitor, Alert, AlertType


logger = logging.getLogger(__name__)


class SimulationState(Enum):
    """State of the simulation."""
    STOPPED = "stopped"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SimulationConfig:
    """Configuration for simulation."""
    node_count: int = 100
    duration: float = 60.0
    time_step: float = 0.01
    real_time: bool = False
    seed: Optional[int] = None
    topology_type: TopologyType = TopologyType.SCALE_FREE
    avg_connections: int = 4
    quantum_link_ratio: float = 0.3
    packet_rate: float = 10.0
    attack_simulation: bool = False
    ai_enabled: bool = True
    checkpoint_interval: float = 30.0
    log_interval: float = 5.0


@dataclass
class SimulationStats:
    """Running statistics for simulation."""
    events_processed: int = 0
    packets_generated: int = 0
    packets_delivered: int = 0
    packets_failed: int = 0
    qubits_teleported: int = 0
    entanglements_created: int = 0
    attacks_detected: int = 0
    total_latency: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    
    @property
    def packet_delivery_rate(self) -> float:
        """Packets delivered / total attempted."""
        total = self.packets_delivered + self.packets_failed
        return self.packets_delivered / total if total > 0 else 0.0
    
    @property
    def average_latency(self) -> float:
        """Average packet latency."""
        return self.total_latency / self.packets_delivered if self.packets_delivered > 0 else 0.0
    
    @property
    def elapsed_time(self) -> float:
        """Simulation elapsed time."""
        if self.start_time == 0:
            return 0.0
        end = self.end_time if self.end_time > 0 else time.time()
        return end - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize stats to dictionary."""
        return {
            "events_processed": self.events_processed,
            "packets_generated": self.packets_generated,
            "packets_delivered": self.packets_delivered,
            "packets_failed": self.packets_failed,
            "packet_delivery_rate": self.packet_delivery_rate,
            "qubits_teleported": self.qubits_teleported,
            "entanglements_created": self.entanglements_created,
            "attacks_detected": self.attacks_detected,
            "average_latency": self.average_latency,
            "elapsed_time": self.elapsed_time,
        }


class SimulationEngine:
    """
    Core simulation engine for quantum networks.
    
    Manages simulation lifecycle, event processing, and
    coordination of network components.
    
    Features:
    - Event-driven simulation
    - Support for 10-10,000+ nodes
    - Real-time and accelerated modes
    - Checkpoint/resume capability
    - Comprehensive metrics collection
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize simulation engine.
        
        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()
        self.state = SimulationState.STOPPED
        
        self.topology: Optional[NetworkTopology] = None
        self.scheduler: EventScheduler = EventScheduler()
        self.monitor: SimulationMonitor = SimulationMonitor()
        
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._paused = threading.Event()
        self._lock = threading.RLock()
        
        self._stats = SimulationStats()
        self._callbacks: Dict[str, List[Callable]] = {
            'tick': [],
            'packet_sent': [],
            'packet_received': [],
            'alert': [],
            'checkpoint': [],
        }
        
        self._packet_sources: Set[str] = set()
        self._packet_destinations: Set[str] = set()
        
        if self.config.seed is not None:
            random.seed(self.config.seed)
    
    def initialize(self) -> bool:
        """
        Initialize simulation.
        
        Returns:
            True if initialization successful
        """
        with self._lock:
            if self.state != SimulationState.STOPPED:
                return False
            
            self.state = SimulationState.INITIALIZING
            
            try:
                topo_config = TopologyConfig(
                    node_count=self.config.node_count,
                    topology_type=self.config.topology_type,
                    avg_connections=self.config.avg_connections,
                    quantum_link_ratio=self.config.quantum_link_ratio,
                    seed=self.config.seed,
                )
                
                self.topology = NetworkTopology(topo_config)
                self.topology.generate()
                self.topology.create_nodes()
                self.topology.create_links()
                
                for node in self.topology.nodes.values():
                    node.state = NodeState.ONLINE
                
                node_ids = list(self.topology.nodes.keys())
                self._packet_sources = set(random.sample(node_ids, min(10, len(node_ids))))
                self._packet_destinations = set(random.sample(
                    [n for n in node_ids if n not in self._packet_sources],
                    min(10, len(node_ids) - len(self._packet_sources))
                ))
                
                self._schedule_periodic_events()
                
                self.state = SimulationState.STOPPED
                logger.info(f"Simulation initialized: {len(self.topology.nodes)} nodes, "
                           f"{len(self.topology.link_manager.links)} links")
                return True
                
            except Exception as e:
                logger.error(f"Initialization failed: {e}")
                self.state = SimulationState.ERROR
                return False
    
    def _schedule_periodic_events(self) -> None:
        """Schedule periodic simulation events."""
        self.scheduler.schedule_event(
            event_type=EventType.DECOHERENCE,
            delay=self.config.time_step,
            callback=self._process_decoherence
        )
        
        self.scheduler.schedule_event(
            event_type=EventType.ROUTING_UPDATE,
            delay=1.0,
            callback=self._update_routing
        )
        
        if self.config.ai_enabled:
            self.scheduler.schedule_event(
                event_type=EventType.AI_OPTIMIZATION,
                delay=0.5,
                callback=self._ai_optimization
            )
        
        self.scheduler.schedule_event(
            event_type=EventType.PACKET_GENERATION,
            delay=1.0 / self.config.packet_rate,
            callback=self._generate_packet
        )
        
        self.scheduler.schedule_event(
            event_type=EventType.METRICS_COLLECTION,
            delay=self.config.log_interval,
            callback=self._collect_metrics
        )
    
    def start(self) -> bool:
        """
        Start simulation.
        
        Returns:
            True if started successfully
        """
        with self._lock:
            if self.state == SimulationState.RUNNING:
                return False
            
            if self.state == SimulationState.STOPPED:
                if not self.initialize():
                    return False
            
            self._running.set()
            self._paused.set()
            self.state = SimulationState.RUNNING
            self._stats.start_time = time.time()
            
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            
            logger.info("Simulation started")
            return True
    
    def pause(self) -> bool:
        """Pause simulation."""
        if self.state != SimulationState.RUNNING:
            return False
        self._paused.clear()
        self.state = SimulationState.PAUSED
        logger.info("Simulation paused")
        return True
    
    def resume(self) -> bool:
        """Resume simulation."""
        if self.state != SimulationState.PAUSED:
            return False
        self._paused.set()
        self.state = SimulationState.RUNNING
        logger.info("Simulation resumed")
        return True
    
    def stop(self) -> bool:
        """Stop simulation."""
        self._running.clear()
        self._paused.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        self.state = SimulationState.STOPPED
        self._stats.end_time = time.time()
        
        logger.info("Simulation stopped")
        return True
    
    def _run_loop(self) -> None:
        """Main simulation loop."""
        last_time = time.time()
        
        while self._running.is_set():
            self._paused.wait()
            
            current_time = time.time()
            if not self.config.real_time:
                elapsed = current_time - last_time
                simulation_step = self.config.time_step * 10
                current_time = self.topology.config.seed + simulation_step if hasattr(self, 'sim_time') else current_time
            
            last_time = current_time
            
            self._process_events()
            
            self._emit_callbacks('tick', self._stats.to_dict())
            
            time.sleep(self.config.time_step if self.config.real_time else 0.001)
            
            if self.config.duration > 0:
                if self._stats.elapsed_time >= self.config.duration:
                    self.stop()
                    self.state = SimulationState.COMPLETED
                    break
        
        self._stats.end_time = time.time()
        self.state = SimulationState.COMPLETED
    
    def _process_events(self) -> None:
        """Process scheduled events."""
        events = self.scheduler.get_due_events()
        
        for event in events:
            try:
                if event.callback:
                    event.callback(event.data)
                self._stats.events_processed += 1
            except Exception as e:
                logger.error(f"Event processing error: {e}")
    
    def _process_decoherence(self, data: Any) -> None:
        """Apply decoherence to network."""
        if not self.topology:
            return
        
        for node in self.topology.nodes.values():
            node.apply_decoherence(self.config.time_step)
        
        for link in self.topology.link_manager.links.values():
            link.apply_decoherence(self.config.time_step)
    
    def _update_routing(self, data: Any) -> None:
        """Update routing tables."""
        if not self.topology:
            return
        
        for node_id, node in self.topology.nodes.items():
            for dest_id in self.topology.nodes.keys():
                if dest_id != node_id:
                    path = self.topology.get_shortest_path(node_id, dest_id)
                    if path:
                        node.update_routing_table(dest_id, path[1:], 1.0)
    
    def _ai_optimization(self, data: Any) -> None:
        """Run AI optimization."""
        pass
    
    def _generate_packet(self, data: Any) -> None:
        """Generate random packet."""
        if not self.topology or not self._packet_sources or not self._packet_destinations:
            return
        
        source = random.choice(list(self._packet_sources))
        destination = random.choice(list(self._packet_destinations))
        
        packet = create_packet(
            PacketType.QUANTUM_DATA if random.random() < 0.3 else PacketType.CONTROL_MESSAGE,
            source=source,
            destination=destination,
            payload=random.randbytes(64),
        )
        
        if source in self.topology.nodes:
            self.topology.nodes[source].send_packet(packet)
            self._stats.packets_generated += 1
    
    def _collect_metrics(self, data: Any) -> None:
        """Collect and log metrics."""
        if not self.topology:
            return
        
        stats = {
            "timestamp": time.time(),
            "nodes_online": sum(1 for n in self.topology.nodes.values() if n.state == NodeState.ONLINE),
            "active_links": self.topology.link_manager.active_links,
            "total_entanglements": self.topology.link_manager.total_entangled_pairs,
            "simulation": self._stats.to_dict(),
        }
        
        self.monitor.record_metrics(stats)
        
        logger.info(f"[{self._stats.elapsed_time:.1f}s] "
                   f"Nodes: {stats['nodes_online']}, "
                   f"Links: {stats['active_links']}, "
                   f"Packets: {self._stats.packets_generated}/{self._stats.packets_delivered}")
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _emit_callbacks(self, event: str, data: Any) -> None:
        """Emit callbacks for event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def send_packet(
        self,
        source: str,
        destination: str,
        packet_type: PacketType = PacketType.QUANTUM_DATA,
        payload: Optional[bytes] = None
    ) -> Optional[Packet]:
        """
        Send packet through network.
        
        Args:
            source: Source node ID
            destination: Destination node ID
            packet_type: Type of packet
            payload: Optional payload data
            
        Returns:
            Created packet or None
        """
        if not self.topology or source not in self.topology.nodes:
            return None
        
        packet = create_packet(
            packet_type,
            source,
            destination,
            payload=payload or b''
        )
        
        self.topology.nodes[source].send_packet(packet)
        self._stats.packets_generated += 1
        
        return packet
    
    def get_network_state(self) -> Dict[str, Any]:
        """Get current network state."""
        if not self.topology:
            return {}
        
        return {
            "state": self.state.value,
            "elapsed_time": self._stats.elapsed_time,
            "topology": self.topology.analyze_topology(),
            "stats": self._stats.to_dict(),
            "node_states": {
                nid: {
                    "state": node.state.value,
                    "qubits": node.qubit_count,
                    "fidelity": node.average_fidelity,
                    "neighbors": len(node.neighbors),
                }
                for nid, node in self.topology.nodes.items()
            },
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation statistics."""
        return {
            "simulation": self._stats.to_dict(),
            "topology": self.topology.analyze_topology() if self.topology else {},
            "links": self.topology.link_manager.get_statistics() if self.topology else {},
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize engine state to dictionary."""
        return {
            "state": self.state.value,
            "config": {
                "node_count": self.config.node_count,
                "duration": self.config.duration,
                "real_time": self.config.real_time,
            },
            "stats": self._stats.to_dict(),
            "topology_summary": self.topology.analyze_topology() if self.topology else {},
        }


class DistributedSimulationEngine(SimulationEngine):
    """
    Distributed simulation engine for very large networks.
    
    Supports sharding network across multiple processes
    for handling 10,000+ nodes efficiently.
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None, shards: int = 4):
        """
        Initialize distributed simulation.
        
        Args:
            config: Simulation configuration
            shards: Number of process shards
        """
        super().__init__(config)
        self.shards = shards
        self._shard_engines: List[SimulationEngine] = []
    
    def initialize(self) -> bool:
        """Initialize distributed simulation."""
        nodes_per_shard = self.config.node_count // self.shards
        
        for i in range(self.shards):
            shard_config = SimulationConfig(
                node_count=nodes_per_shard,
                duration=self.config.duration,
                seed=self.config.seed + i if self.config.seed else None,
            )
            shard_engine = SimulationEngine(shard_config)
            shard_engine.initialize()
            self._shard_engines.append(shard_engine)
        
        return True
