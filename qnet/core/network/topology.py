"""
Network Topology - Network structure and generation algorithms.

Implements various network topologies (mesh, scale-free, etc.)
and provides tools for topology analysis and visualization.
"""

from __future__ import annotations

import uuid
import random
import math
import networkx as nx
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Set, Callable
from enum import Enum
from abc import ABC, abstractmethod

from qnet.core.network.node import QuantumNode, NodeType, NodeState
from qnet.core.network.link import QuantumLink, LinkType, LinkManager


class TopologyType(Enum):
    """Types of network topologies."""
    MESH = "mesh"
    STAR = "star"
    RING = "ring"
    TREE = "tree"
    SCALE_FREE = "scale_free"
    RANDOM = "random"
    BARABASI_ALBERT = "barabasi_albert"
    WATTS_STROGATZ = "watts_strogatz"
    HIERARCHICAL = "hierarchical"
    HYBRID = "hybrid"
    CUSTOM = "custom"


@dataclass
class TopologyConfig:
    """Configuration for topology generation."""
    node_count: int = 100
    topology_type: TopologyType = TopologyType.SCALE_FREE
    avg_connections: int = 4
    max_connections: int = 10
    quantum_link_ratio: float = 0.3
    node_type_distribution: Dict[NodeType, float] = field(default_factory=lambda: {
        NodeType.ENDPOINT: 0.7,
        NodeType.RELAY: 0.2,
        NodeType.REPEATER: 0.1,
    })
    seed: Optional[int] = None
    spatial_range: float = 100.0
    connection_distance_threshold: float = 50.0


class TopologyGenerator(ABC):
    """
    Abstract base class for topology generators.
    
    Subclasses implement specific topology generation algorithms.
    """
    
    def __init__(self, config: TopologyConfig):
        """
        Initialize topology generator.
        
        Args:
            config: Topology configuration
        """
        self.config = config
        if config.seed is not None:
            random.seed(config.seed)
            nx.seed = config.seed
    
    @abstractmethod
    def generate(self) -> nx.Graph:
        """
        Generate network topology graph.
        
        Returns:
            NetworkX graph representing topology
        """
        pass


class MeshTopology(TopologyGenerator):
    """Generate fully or partially connected mesh topology."""
    
    def generate(self) -> nx.Graph:
        """Generate mesh topology."""
        n = self.config.node_count
        p = self.config.avg_connections / n
        
        if p >= 0.5:
            G = nx.grid_2d_graph(int(math.sqrt(n)), int(math.sqrt(n)))
        else:
            G = nx.watts_strogatz_graph(n, self.config.avg_connections, 0.0)
        
        G = nx.convert_node_labels_to_integers(G)
        return G


class ScaleFreeTopology(TopologyGenerator):
    """Generate scale-free network using Barabasi-Albert model."""
    
    def generate(self) -> nx.Graph:
        """Generate scale-free topology."""
        G = nx.barabasi_albert_graph(
            self.config.node_count,
            self.config.avg_connections // 2,
            seed=self.config.seed
        )
        return G


class RandomTopology(TopologyGenerator):
    """Generate random Erdős–Rényi graph."""
    
    def generate(self) -> nx.Graph:
        """Generate random topology."""
        p = self.config.avg_connections / self.config.node_count
        G = nx.erdos_renyi_graph(
            self.config.node_count,
            p,
            seed=self.config.seed
        )
        return G


class SmallWorldTopology(TopologyGenerator):
    """Generate small-world network using Watts-Strogatz model."""
    
    def generate(self) -> nx.Graph:
        """Generate small-world topology."""
        G = nx.watts_strogatz_graph(
            self.config.node_count,
            self.config.avg_connections,
            0.1,
            seed=self.config.seed
        )
        return G


class RingTopology(TopologyGenerator):
    """Generate ring topology with optional chords."""
    
    def generate(self) -> nx.Graph:
        """Generate ring topology."""
        G = nx.cycle_graph(self.config.node_count)
        
        chords = self.config.avg_connections - 2
        if chords > 0:
            for i in range(self.config.node_count):
                target = (i + random.randint(2, 4)) % self.config.node_count
                if not G.has_edge(i, target):
                    G.add_edge(i, target)
        
        return G


class StarTopology(TopologyGenerator):
    """Generate star topology with central hub."""
    
    def generate(self) -> nx.Graph:
        """Generate star topology."""
        G = nx.star_graph(self.config.node_count - 1)
        return G


class HierarchicalTopology(TopologyGenerator):
    """Generate hierarchical/tree topology."""
    
    def generate(self) -> nx.Graph:
        """Generate hierarchical topology."""
        branches = max(2, self.config.avg_connections)
        G = nx.generators.nary_tree(self.config.node_count, branching_factor=branches)
        return G


class NetworkTopology:
    """
    Quantum network topology manager.
    
    Manages network structure, generates topologies,
    and provides topology analysis tools.
    
    Attributes:
        graph: NetworkX graph representation
        nodes: Dictionary of quantum nodes
        link_manager: Manages quantum links
    """
    
    def __init__(self, config: Optional[TopologyConfig] = None):
        """
        Initialize network topology.
        
        Args:
            config: Optional topology configuration
        """
        self.config = config or TopologyConfig()
        self.graph: nx.Graph = nx.Graph()
        self.nodes: Dict[str, QuantumNode] = {}
        self.link_manager = LinkManager()
        self._node_positions: Dict[str, Tuple[float, float, float]] = {}
    
    def generate(
        self,
        topology_type: Optional[TopologyType] = None,
        **kwargs
    ) -> nx.Graph:
        """
        Generate network topology.
        
        Args:
            topology_type: Type of topology to generate
            **kwargs: Additional configuration overrides
            
        Returns:
            Generated NetworkX graph
        """
        if kwargs:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        
        if topology_type:
            self.config.topology_type = topology_type
        
        generators = {
            TopologyType.MESH: MeshTopology,
            TopologyType.SCALE_FREE: ScaleFreeTopology,
            TopologyType.RANDOM: RandomTopology,
            TopologyType.WATTS_STROGATZ: SmallWorldTopology,
            TopologyType.RING: RingTopology,
            TopologyType.STAR: StarTopology,
            TopologyType.HIERARCHICAL: HierarchicalTopology,
            TopologyType.BARABASI_ALBERT: ScaleFreeTopology,
        }
        
        generator_class = generators.get(self.config.topology_type, ScaleFreeTopology)
        generator = generator_class(self.config)
        
        self.graph = generator.generate()
        return self.graph
    
    def create_nodes(
        self,
        node_type: Optional[NodeType] = None,
        position_generator: Optional[Callable[[int], Tuple[float, float, float]]] = None
    ) -> Dict[str, QuantumNode]:
        """
        Create quantum nodes from graph.
        
        Args:
            node_type: Override node type
            position_generator: Function to generate positions
            
        Returns:
            Dictionary of created nodes
        """
        self.nodes.clear()
        
        if position_generator is None:
            position_generator = self._default_position_generator
        
        for i, node_id in enumerate(self.graph.nodes()):
            node_str = f"node_{node_id}"
            
            if node_type is None:
                node_type = self._assign_node_type(node_id)
            
            position = position_generator(node_id)
            
            node = QuantumNode(
                node_id=node_str,
                node_type=node_type,
                position=position,
            )
            
            self.nodes[node_str] = node
            self._node_positions[node_str] = position
            
            nx.set_node_attributes(self.graph, {node_id: node_str}, 'node_id')
        
        return self.nodes
    
    def _default_position_generator(self, node_id: int) -> Tuple[float, float, float]:
        """Generate 3D position for node (circular layout)."""
        n = len(self.graph.nodes())
        angle = 2 * math.pi * node_id / n
        radius = self.config.spatial_range * math.sqrt(node_id / n) if n > 1 else 1
        
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        z = random.uniform(-10, 10)
        
        return (x, y, z)
    
    def _assign_node_type(self, node_id: int) -> NodeType:
        """Assign node type based on degree and configuration."""
        degree = self.graph.degree(node_id)
        
        if degree == 0:
            return NodeType.ENDPOINT
        elif degree >= self.config.max_connections * 0.8:
            return NodeType.ROUTER
        elif degree >= self.config.avg_connections:
            return NodeType.RELAY
        elif random.random() < 0.1:
            return NodeType.REPEATER
        else:
            return NodeType.ENDPOINT
    
    def create_links(self) -> List[QuantumLink]:
        """
        Create quantum links from graph edges.
        
        Returns:
            List of created links
        """
        self.link_manager.links.clear()
        links = []
        
        for u, v in self.graph.edges():
            node_a = f"node_{u}"
            node_b = f"node_{v}"
            
            pos_a = self._node_positions.get(node_a, (0, 0, 0))
            pos_b = self._node_positions.get(node_b, (0, 0, 0))
            
            distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(pos_a, pos_b)))
            
            link_type = LinkType.QUANTUM_ENTANGLED
            is_quantum = random.random() < self.config.quantum_link_ratio
            
            if not is_quantum:
                link_type = LinkType.CLASSICAL
            
            link = self.link_manager.create_link(
                node_a=node_a,
                node_b=node_b,
                link_type=link_type,
                distance=distance,
                latency=5.0 + distance * 0.1,
            )
            
            links.append(link)
            
            if node_a in self.nodes:
                self.nodes[node_a].add_neighbor(node_b, link)
            if node_b in self.nodes:
                self.nodes[node_b].add_neighbor(node_a, link)
        
        return links
    
    def add_node(
        self,
        node_id: str,
        position: Tuple[float, float, float],
        node_type: NodeType = NodeType.ENDPOINT,
        connect_to: Optional[List[str]] = None
    ) -> QuantumNode:
        """
        Add new node to topology.
        
        Args:
            node_id: Node identifier
            position: 3D position
            node_type: Type of node
            connect_to: List of nodes to connect to
            
        Returns:
            Created node
        """
        node = QuantumNode(
            node_id=node_id,
            node_type=node_type,
            position=position,
        )
        
        self.nodes[node_id] = node
        self._node_positions[node_id] = position
        
        nx_node = len(self.graph.nodes())
        self.graph.add_node(nx_node, node_id=node_id)
        
        if connect_to:
            for target in connect_to:
                if target in self.nodes:
                    self.add_link(node_id, target)
        
        return node
    
    def remove_node(self, node_id: str) -> bool:
        """Remove node from topology."""
        if node_id not in self.nodes:
            return False
        
        for link_id in list(self.link_manager.node_links.get(node_id, [])):
            self.link_manager.remove_link(link_id)
        
        self.graph.remove_node(node_id)
        del self.nodes[node_id]
        del self._node_positions[node_id]
        
        return True
    
    def add_link(
        self,
        node_a: str,
        node_b: str,
        link_type: LinkType = LinkType.QUANTUM_ENTANGLED
    ) -> Optional[QuantumLink]:
        """Add link between nodes."""
        if node_a not in self.nodes or node_b not in self.nodes:
            return None
        
        pos_a = self._node_positions.get(node_a, (0, 0, 0))
        pos_b = self._node_positions.get(node_b, (0, 0, 0))
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(pos_a, pos_b)))
        
        nx_a = self._get_nx_node(node_a)
        nx_b = self._get_nx_node(node_b)
        
        if nx_a is not None and nx_b is not None:
            self.graph.add_edge(nx_a, nx_b)
        
        link = self.link_manager.create_link(
            node_a=node_a,
            node_b=node_b,
            link_type=link_type,
            distance=distance,
        )
        
        self.nodes[node_a].add_neighbor(node_b, link)
        self.nodes[node_b].add_neighbor(node_a, link)
        
        return link
    
    def _get_nx_node(self, node_id: str) -> Optional[int]:
        """Get NetworkX node index from node ID."""
        for nx_id, attrs in self.graph.nodes(data=True):
            if attrs.get('node_id') == node_id:
                return nx_id
        return None
    
    def get_shortest_path(self, source: str, destination: str) -> List[str]:
        """Get shortest path between nodes."""
        try:
            nx_source = self._get_nx_node(source)
            nx_dest = self._get_nx_node(destination)
            
            if nx_source is None or nx_dest is None:
                return []
            
            path = nx.shortest_path(self.graph, nx_source, nx_dest)
            return [self.graph.nodes[n].get('node_id', f'node_{n}') for n in path]
        except nx.NetworkXNoPath:
            return []
    
    def get_node_degree(self, node_id: str) -> int:
        """Get node degree."""
        nx_node = self._get_nx_node(node_id)
        if nx_node is None:
            return 0
        return self.graph.degree(nx_node)
    
    def get_centrality(self, node_id: str) -> float:
        """Get node betweenness centrality."""
        nx_node = self._get_nx_node(node_id)
        if nx_node is None:
            return 0.0
        return nx.betweenness_centrality(self.graph).get(nx_node, 0.0)
    
    def get_clustering_coefficient(self, node_id: str) -> float:
        """Get node clustering coefficient."""
        nx_node = self._get_nx_node(node_id)
        if nx_node is None:
            return 0.0
        return nx.clustering(self.graph, nx_node)
    
    def analyze_topology(self) -> Dict[str, Any]:
        """Analyze topology properties."""
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "average_degree": sum(dict(self.graph.degree()).values()) / max(1, len(self.graph)),
            "density": nx.density(self.graph),
            "is_connected": nx.is_connected(self.graph),
            "components": nx.number_connected_components(self.graph),
            "diameter": nx.diameter(self.graph) if nx.is_connected(self.graph) else None,
            "average_path_length": nx.average_shortest_path_length(self.graph) if nx.is_connected(self.graph) else None,
            "clustering_coefficient": nx.average_clustering(self.graph),
            "degree_assortativity": nx.degree_assortativity_coefficient(self.graph),
            "node_types": {
                nt.value: sum(1 for n in self.nodes.values() if n.node_type == nt)
                for nt in NodeType
            },
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize topology to dictionary."""
        return {
            "config": {
                "node_count": self.config.node_count,
                "topology_type": self.config.topology_type.value,
                "avg_connections": self.config.avg_connections,
                "quantum_link_ratio": self.config.quantum_link_ratio,
            },
            "analysis": self.analyze_topology(),
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "links": {
                lid: link.to_dict()
                for lid, link in self.link_manager.links.items()
            },
            "positions": {nid: list(pos) for nid, pos in self._node_positions.items()},
        }
    
    def __repr__(self) -> str:
        return f"NetworkTopology({len(self.nodes)} nodes, {len(self.link_manager.links)} links)"
