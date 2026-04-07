"""
Unit tests for QNet core components.
"""

import pytest
import time
import math
from qnet.core.quantum.qubit import Qubit, QubitState, GateType
from qnet.core.quantum.entanglement import EntangledPair, BellState, EntanglementManager
from qnet.core.quantum.teleportation import QuantumTeleportation
from qnet.core.quantum.decoherence import DecoherenceSimulator, ExponentialDecoherence
from qnet.core.transport.packet import Packet, PacketType, PacketHeader, create_packet
from qnet.core.transport.buffer import PacketBuffer, BufferStrategy
from qnet.core.network.node import QuantumNode, NodeType
from qnet.core.network.link import QuantumLink, LinkType
from qnet.core.network.topology import NetworkTopology, TopologyType, TopologyConfig
from qnet.core.simulation.engine import SimulationEngine, SimulationConfig
from qnet.security.qkd import BB84Protocol, E91Protocol
from qnet.security.attacks import AttackSimulator, AttackType
from qnet.ai.router import AIQuantumRouter, RoutingAlgorithm
from qnet.ai.predictor import TrafficPredictor, TrafficSample, PredictionModel
from qnet.ai.healer import SelfHealingManager, FailureType


class TestQubit:
    """Test quantum bit operations."""
    
    def test_qubit_creation(self):
        """Test basic qubit creation."""
        qubit = Qubit.zero()
        assert qubit.state == QubitState.ZERO
        assert abs(abs(qubit.alpha)**2 - 1) < 1e-6
        
        qubit = Qubit.one()
        assert qubit.state == QubitState.ONE
    
    def test_qubit_normalization(self):
        """Test qubit state normalization."""
        qubit = Qubit(alpha=complex(2, 0), beta=complex(1, 0))
        assert abs(abs(qubit.alpha)**2 + abs(qubit.beta)**2 - 1) < 1e-6
    
    def test_hadamard_gate(self):
        """Test Hadamard gate operation."""
        qubit = Qubit.zero()
        new_qubit = qubit.apply_gate(GateType.HADAMARD)
        
        assert abs(abs(new_qubit.alpha)**2 - 0.5) < 1e-6
        assert abs(abs(new_qubit.beta)**2 - 0.5) < 1e-6
    
    def test_qubit_measurement(self):
        """Test qubit measurement."""
        qubit = Qubit.plus()
        results = [qubit.measure() for _ in range(100)]
        
        assert all(r in [0, 1] for r in results)
        assert 40 < sum(results) < 60


class TestEntanglement:
    """Test quantum entanglement."""
    
    def test_entangled_pair_creation(self):
        """Test entangled pair creation."""
        pair = EntangledPair.create_pair("node_a", "node_b")
        
        assert pair.node_a == "node_a"
        assert pair.node_b == "node_b"
        assert pair.bell_state == BellState.PHI_PLUS
        assert pair.fidelity > 0.9
    
    def test_entanglement_purification(self):
        """Test entanglement purification."""
        pair1 = EntangledPair.create_pair("A", "B")
        pair2 = EntangledPair.create_pair("A", "B")
        
        pair1.fidelity = 0.9
        pair2.fidelity = 0.9
        
        result = pair1.purify(pair2)
        
        assert isinstance(result, bool)


class TestTeleportation:
    """Test quantum teleportation."""
    
    def test_teleportation_basic(self):
        """Test basic teleportation."""
        tele = QuantumTeleportation()
        
        state = Qubit.plus()
        pair = EntangledPair.create_pair("A", "B")
        
        result = tele.teleport(state, pair, "A", "B")
        
        assert hasattr(result, 'success')


class TestDecoherence:
    """Test decoherence models."""
    
    def test_exponential_decay(self):
        """Test exponential decoherence."""
        model = ExponentialDecoherence(decay_rate=0.1)
        
        fidelity = model.calculate_fidelity(1.0, 1.0)
        
        assert 0 < fidelity < 1.0
        assert fidelity < 1.0
    
    def test_decoherence_result(self):
        """Test decoherence result."""
        sim = DecoherenceSimulator("exponential")
        result = sim.simulate(1.0, 1.0)
        
        assert result.initial_fidelity == 1.0
        assert result.final_fidelity < 1.0


class TestPackets:
    """Test packet operations."""
    
    def test_packet_creation(self):
        """Test packet creation."""
        header = PacketHeader(
            packet_type=PacketType.QUANTUM_DATA,
            source_id="node_0",
            destination_id="node_1"
        )
        
        packet = create_packet(
            PacketType.QUANTUM_DATA,
            "node_0",
            "node_1"
        )
        
        assert packet.header.source_id == "node_0"
        assert packet.header.destination_id == "node_1"
    
    def test_packet_ttl(self):
        """Test packet TTL decrement."""
        packet = create_packet(PacketType.CONTROL_MESSAGE, "A", "B")
        packet.header.ttl = 10
        
        assert packet.decrement_ttl() == True
        assert packet.header.ttl == 9


class TestBuffer:
    """Test packet buffer."""
    
    def test_buffer_add_get(self):
        """Test buffer add and get."""
        buffer = PacketBuffer(capacity=10)
        
        packet = create_packet(PacketType.CONTROL_MESSAGE, "A", "B")
        buffer.add(packet)
        
        assert len(buffer) == 1
        
        retrieved = buffer.get(block=False)
        assert retrieved.header.packet_id == packet.header.packet_id
    
    def test_buffer_overflow(self):
        """Test buffer overflow handling."""
        buffer = PacketBuffer(capacity=2, strategy=BufferStrategy.DROP_TAIL)
        
        for i in range(5):
            packet = create_packet(PacketType.CONTROL_MESSAGE, "A", "B")
            try:
                buffer.add(packet)
            except Exception:
                pass
        
        assert len(buffer) <= 2


class TestNode:
    """Test quantum node."""
    
    def test_node_creation(self):
        """Test node creation."""
        node = QuantumNode(
            node_id="test_node",
            node_type=NodeType.ENDPOINT
        )
        
        assert node.node_id == "test_node"
        assert node.node_type == NodeType.ENDPOINT
        assert node.state.value == "online"
    
    def test_qubit_creation(self):
        """Test qubit creation in node."""
        node = QuantumNode(node_id="test")
        
        qubit = node.create_qubit()
        
        assert qubit is not None
        assert node.qubit_count == 1
    
    def test_entanglement_creation(self):
        """Test entanglement creation."""
        node = QuantumNode(node_id="test")
        
        pair = node.create_entanglement("other_node")
        
        assert pair is not None
        assert node.active_entanglements == 1


class TestLink:
    """Test quantum link."""
    
    def test_link_creation(self):
        """Test link creation."""
        link = QuantumLink(
            link_id="link_1",
            node_a="node_a",
            node_b="node_b"
        )
        
        assert link.link_id == "link_1"
        assert link.is_active == False
    
    def test_entanglement_creation(self):
        """Test entanglement on link."""
        link = QuantumLink(
            link_id="link_1",
            node_a="A",
            node_b="B"
        )
        link.establish()
        
        assert link.is_active


class TestTopology:
    """Test network topology."""
    
    def test_topology_creation(self):
        """Test topology generation."""
        config = TopologyConfig(node_count=50, seed=42)
        topo = NetworkTopology(config)
        
        topo.generate(TopologyType.SCALE_FREE)
        topo.create_nodes()
        topo.create_links()
        
        assert len(topo.nodes) == 50
    
    def test_shortest_path(self):
        """Test shortest path calculation."""
        config = TopologyConfig(node_count=20, seed=42)
        topo = NetworkTopology(config)
        
        topo.generate(TopologyType.MESH)
        topo.create_nodes()
        topo.create_links()
        
        path = topo.get_shortest_path("node_0", "node_19")
        
        assert isinstance(path, list)


class TestSimulation:
    """Test simulation engine."""
    
    def test_simulation_initialization(self):
        """Test simulation initialization."""
        config = SimulationConfig(
            node_count=50,
            seed=42,
            duration=10.0
        )
        
        engine = SimulationEngine(config)
        success = engine.initialize()
        
        assert success == True
        assert engine.state.value == "stopped"
    
    def test_simulation_start_stop(self):
        """Test simulation start and stop."""
        config = SimulationConfig(node_count=20, duration=1.0)
        engine = SimulationEngine(config)
        engine.initialize()
        
        engine.start()
        assert engine.state.value == "running"
        
        engine.stop()
        assert engine.state.value == "stopped"


class TestQKD:
    """Test QKD protocols."""
    
    def test_bb84_protocol(self):
        """Test BB84 key generation."""
        bb84 = BB84Protocol()
        result = bb84.execute(num_bits=100)
        
        assert result.protocol == "BB84"
        assert result.key_length >= 0
    
    def test_e91_protocol(self):
        """Test E91 key generation."""
        e91 = E91Protocol()
        result = e91.execute(num_pairs=100)
        
        assert result.protocol == "E91"


class TestAttacks:
    """Test attack simulation."""
    
    def test_eavesdropping(self):
        """Test eavesdropping simulation."""
        sim = AttackSimulator()
        
        result = sim.simulate_eavesdropping(None, interception_strength=0.1)
        
        assert hasattr(result, 'attack')
        assert hasattr(result, 'detection_probability')
    
    def test_dos_attack(self):
        """Test DoS attack simulation."""
        sim = AttackSimulator()
        
        result = sim.simulate_dos("node_0", duration=5.0, intensity=0.8)
        
        assert result.attack.attack_type == AttackType.DOS


class TestRouter:
    """Test AI router."""
    
    def test_router_initialization(self):
        """Test router initialization."""
        router = AIQuantumRouter(algorithm=RoutingAlgorithm.Q_LEARNING)
        
        assert router.algorithm == RoutingAlgorithm.Q_LEARNING
    
    def test_dijkstra_route(self):
        """Test Dijkstra routing."""
        router = AIQuantumRouter(algorithm=RoutingAlgorithm.DIJKSTRA)
        
        graph = {
            "A": ["B", "C"],
            "B": ["A", "D"],
            "C": ["A", "D"],
            "D": ["B", "C"]
        }
        
        path, cost = router.dijkstra_route("A", "D", graph)
        
        assert isinstance(path, list)
        assert cost >= 0


class TestPredictor:
    """Test traffic predictor."""
    
    def test_prediction_basic(self):
        """Test basic prediction."""
        predictor = TrafficPredictor(model=PredictionModel.EMA)
        
        for i in range(10):
            sample = TrafficSample(
                timestamp=float(i),
                packets=100 + i * 10,
                qubits=50 + i * 5,
                latency=10.0,
                throughput=1000.0
            )
            predictor.add_sample(sample)
        
        pred = predictor.predict_next()
        
        assert hasattr(pred, 'predicted_value')
        assert 0 <= pred.confidence <= 1.0
    
    def test_anomaly_detection(self):
        """Test anomaly detection."""
        predictor = TrafficPredictor()
        
        for i in range(20):
            sample = TrafficSample(
                timestamp=float(i),
                packets=100,
                qubits=50,
                latency=10.0,
                throughput=1000.0
            )
            predictor.add_sample(sample)
        
        is_anomaly, score = predictor.detect_anomaly(
            TrafficSample(0, 500, 200, 50.0, 5000.0)
        )
        
        assert isinstance(is_anomaly, bool)


class TestHealer:
    """Test self-healing manager."""
    
    def test_health_check(self):
        """Test node health check."""
        healer = SelfHealingManager()
        
        is_healthy, failure = healer.check_node_health(
            "node_0",
            {'latency': 10, 'fidelity': 0.95, 'error_rate': 0.01}
        )
        
        assert is_healthy == True
    
    def test_failure_detection(self):
        """Test failure detection."""
        healer = SelfHealingManager(failure_threshold=0.1)
        
        is_healthy, failure = healer.check_node_health(
            "node_0",
            {'latency': 200, 'fidelity': 0.5, 'error_rate': 0.3}
        )
        
        assert is_healthy == False
        assert failure is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
