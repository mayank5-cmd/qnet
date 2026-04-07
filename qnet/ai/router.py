"""
AI Quantum Router - Machine learning-based routing optimization.

Implements Q-learning and other AI techniques for intelligent
routing decisions in quantum networks.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import numpy as np


class RoutingAlgorithm(Enum):
    """Available routing algorithms."""
    DIJKSTRA = "dijkstra"
    A_STAR = "a_star"
    Q_LEARNING = "q_learning"
    GENETIC = "genetic"
    ADAPTIVE = "adaptive"


@dataclass
class QRoutingTable:
    """
    Q-learning routing table.
    
    Stores Q-values for routing decisions.
    """
    q_table: Dict[Tuple[str, str], Dict[str, float]] = field(default_factory=dict)
    learning_rate: float = 0.1
    discount_factor: float = 0.9
    exploration_rate: float = 0.2
    
    def get_q_value(self, state: str, action: str, next_state: str) -> float:
        """Get Q-value for state-action-next_state."""
        key = (state, next_state)
        if key not in self.q_table:
            self.q_table[key] = {}
        return self.q_table[key].get(action, 0.0)
    
    def update_q_value(
        self,
        state: str,
        action: str,
        next_state: str,
        reward: float,
        max_future_q: float
    ) -> None:
        """Update Q-value using Q-learning formula."""
        key = (state, next_state)
        if key not in self.q_table:
            self.q_table[key] = {}
        
        current_q = self.q_table[key].get(action, 0.0)
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_future_q - current_q
        )
        self.q_table[key][action] = new_q
    
    def get_best_action(self, state: str, neighbors: List[str], metrics: Dict[str, float]) -> Optional[str]:
        """Get best routing action based on Q-values and metrics."""
        if not neighbors:
            return None
        
        if random.random() < self.exploration_rate:
            return random.choice(neighbors)
        
        best_action = None
        best_q = float('-inf')
        
        for neighbor in neighbors:
            q_value = metrics.get(f"q_{neighbor}", 0.0)
            
            latency = metrics.get(f"latency_{neighbor}", 100)
            fidelity = metrics.get(f"fidelity_{neighbor}", 1.0)
            
            combined_score = q_value * 0.5 + (1.0 / latency) * 0.3 + fidelity * 0.2
            
            if combined_score > best_q:
                best_q = combined_score
                best_action = neighbor
        
        return best_action or random.choice(neighbors)


@dataclass
class RoutingDecision:
    """Represents a routing decision."""
    source: str
    destination: str
    path: List[str]
    cost: float
    algorithm: RoutingAlgorithm
    confidence: float
    metrics: Dict[str, float]


class AIQuantumRouter:
    """
    AI-powered quantum network router.
    
    Uses Q-learning and other AI techniques to optimize
    routing decisions for quantum networks.
    
    Features:
    - Q-learning based path selection
    - Multi-metric optimization
    - Adaptive routing
    - Self-learning from past decisions
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        exploration_rate: float = 0.2,
        algorithm: RoutingAlgorithm = RoutingAlgorithm.Q_LEARNING
    ):
        """
        Initialize AI router.
        
        Args:
            learning_rate: Q-learning alpha parameter
            discount_factor: Q-learning gamma parameter
            exploration_rate: Epsilon for epsilon-greedy
            algorithm: Primary routing algorithm
        """
        self.algorithm = algorithm
        self.q_table = QRoutingTable(
            learning_rate=learning_rate,
            discount_factor=discount_factor,
            exploration_rate=exploration_rate
        )
        self.routing_history: List[RoutingDecision] = []
        self.link_metrics: Dict[str, Dict[str, float]] = {}
        self.failure_history: List[Dict[str, Any]] = []
    
    def update_link_metrics(
        self,
        node_a: str,
        node_b: str,
        latency: float,
        fidelity: float,
        throughput: float,
        packet_loss: float
    ) -> None:
        """Update link metrics for routing decisions."""
        link_key = f"{min(node_a, node_b)}_{max(node_a, node_b)}"
        
        self.link_metrics[link_key] = {
            'latency': latency,
            'fidelity': fidelity,
            'throughput': throughput,
            'packet_loss': packet_loss,
            'stability': 1.0 - packet_loss,
        }
    
    def calculate_link_cost(self, link_key: str) -> float:
        """Calculate cost for a link."""
        if link_key not in self.link_metrics:
            return 100.0
        
        m = self.link_metrics[link_key]
        
        latency_cost = m.get('latency', 100) / 10
        fidelity_cost = (1 - m.get('fidelity', 1.0)) * 50
        loss_cost = m.get('packet_loss', 0) * 100
        
        return latency_cost + fidelity_cost + loss_cost
    
    def dijkstra_route(
        self,
        source: str,
        destination: str,
        graph: Dict[str, List[str]],
        exclude_nodes: Optional[List[str]] = None
    ) -> Tuple[List[str], float]:
        """
        Dijkstra's shortest path algorithm.
        
        Args:
            source: Source node ID
            destination: Destination node ID
            graph: Adjacency list representation
            exclude_nodes: Nodes to exclude from path
            
        Returns:
            Tuple of (path, cost)
        """
        if exclude_nodes is None:
            exclude_nodes = []
        
        distances = {source: 0}
        previous = {}
        unvisited = set(graph.keys())
        
        while unvisited:
            current = min(unvisited, key=lambda n: distances.get(n, float('inf')))
            
            if current == destination:
                break
            
            unvisited.remove(current)
            
            if current in exclude_nodes:
                continue
            
            for neighbor in graph.get(current, []):
                if neighbor in exclude_nodes:
                    continue
                
                link_key = f"{min(current, neighbor)}_{max(current, neighbor)}"
                cost = self.calculate_link_cost(link_key)
                
                alt = distances.get(current, float('inf')) + cost
                
                if alt < distances.get(neighbor, float('inf')):
                    distances[neighbor] = alt
                    previous[neighbor] = current
        
        if destination not in previous and destination != source:
            return [], float('inf')
        
        path = []
        current = destination
        while current is not None:
            path.append(current)
            current = previous.get(current)
        
        path.reverse()
        return path, distances.get(destination, float('inf'))
    
    def q_learning_route(
        self,
        source: str,
        destination: str,
        graph: Dict[str, List[str]],
        max_hops: int = 50
    ) -> Tuple[List[str], float]:
        """
        Q-learning based routing.
        
        Args:
            source: Source node ID
            destination: Destination node ID
            graph: Adjacency list
            max_hops: Maximum path length
            
        Returns:
            Tuple of (path, cost)
        """
        path = [source]
        current = source
        visited = {source}
        total_cost = 0.0
        
        for _ in range(max_hops):
            if current == destination:
                return path, total_cost
            
            neighbors = [n for n in graph.get(current, []) if n not in visited]
            
            if not neighbors:
                return path, total_cost
            
            metrics = {}
            for neighbor in neighbors:
                link_key = f"{min(current, neighbor)}_{max(current, neighbor)}"
                link_cost = self.calculate_link_cost(link_key)
                metrics[f"q_{neighbor}"] = -link_cost
                metrics[f"latency_{neighbor}"] = self.link_metrics.get(link_key, {}).get('latency', 100)
                metrics[f"fidelity_{neighbor}"] = self.link_metrics.get(link_key, {}).get('fidelity', 1.0)
            
            next_node = self.q_table.get_best_action(current, neighbors, metrics)
            
            if next_node is None:
                return path, total_cost
            
            path.append(next_node)
            visited.add(next_node)
            
            link_key = f"{min(current, next_node)}_{max(current, next_node)}"
            cost = self.calculate_link_cost(link_key)
            total_cost += cost
            
            current = next_node
        
        return path, total_cost
    
    def adaptive_route(
        self,
        source: str,
        destination: str,
        graph: Dict[str, List[str]],
        requirements: Dict[str, float]
    ) -> RoutingDecision:
        """
        Adaptive routing based on requirements.
        
        Args:
            source: Source node
            destination: Destination node
            graph: Network graph
            requirements: Routing requirements (fidelity, latency, etc.)
            
        Returns:
            RoutingDecision with optimal path
        """
        required_fidelity = requirements.get('fidelity', 0.9)
        max_latency = requirements.get('latency', 100)
        
        dijkstra_path, dijkstra_cost = self.dijkstra_route(source, destination, graph)
        
        qlearning_path, qlearning_cost = self.q_learning_route(source, destination, graph)
        
        dijkstra_meets = True
        qlearning_meets = True
        
        for i in range(len(dijkstra_path) - 1):
            link_key = f"{min(dijkstra_path[i], dijkstra_path[i+1])}_{max(dijkstra_path[i], dijkstra_path[i+1])}"
            if link_key in self.link_metrics:
                if self.link_metrics[link_key].get('fidelity', 1.0) < required_fidelity:
                    dijkstra_meets = False
        
        for i in range(len(qlearning_path) - 1):
            link_key = f"{min(qlearning_path[i], qlearning_path[i+1])}_{max(qlearning_path[i], qlearning_path[i+1])}"
            if link_key in self.link_metrics:
                if self.link_metrics[link_key].get('fidelity', 1.0) < required_fidelity:
                    qlearning_meets = False
        
        if dijkstra_meets and not qlearning_meets:
            best_path, best_cost = dijkstra_path, dijkstra_cost
            algorithm = RoutingAlgorithm.DIJKSTRA
        elif qlearning_meets and not dijkstra_meets:
            best_path, best_cost = qlearning_path, qlearning_cost
            algorithm = RoutingAlgorithm.Q_LEARNING
        else:
            if dijkstra_cost <= qlearning_cost:
                best_path, best_cost = dijkstra_path, dijkstra_cost
                algorithm = RoutingAlgorithm.DIJKSTRA
            else:
                best_path, best_cost = qlearning_path, qlearning_cost
                algorithm = RoutingAlgorithm.Q_LEARNING
        
        decision = RoutingDecision(
            source=source,
            destination=destination,
            path=best_path,
            cost=best_cost,
            algorithm=algorithm,
            confidence=0.8 if best_path else 0.0,
            metrics={'fidelity': required_fidelity, 'latency': max_latency}
        )
        
        self.routing_history.append(decision)
        return decision
    
    def route(
        self,
        source: str,
        destination: str,
        graph: Dict[str, List[str]],
        **kwargs
    ) -> RoutingDecision:
        """
        Main routing interface.
        
        Args:
            source: Source node
            destination: Destination node
            graph: Network graph
            **kwargs: Additional routing parameters
            
        Returns:
            RoutingDecision with optimal path
        """
        if self.algorithm == RoutingAlgorithm.Q_LEARNING:
            path, cost = self.q_learning_route(source, destination, graph)
            algorithm = RoutingAlgorithm.Q_LEARNING
        elif self.algorithm == RoutingAlgorithm.ADAPTIVE:
            return self.adaptive_route(source, destination, graph, kwargs.get('requirements', {}))
        else:
            path, cost = self.dijkstra_route(source, destination, graph)
            algorithm = RoutingAlgorithm.DIJKSTRA
        
        return RoutingDecision(
            source=source,
            destination=destination,
            path=path,
            cost=cost,
            algorithm=algorithm,
            confidence=0.9 if path else 0.0,
            metrics=kwargs
        )
    
    def learn_from_outcome(
        self,
        path: List[str],
        actual_cost: float,
        expected_cost: float
    ) -> None:
        """
        Update Q-table based on routing outcome.
        
        Args:
            path: Taken path
            actual_cost: Actual cost incurred
            expected_cost: Expected cost from routing decision
        """
        reward = -actual_cost
        
        if actual_cost < expected_cost:
            reward += (expected_cost - actual_cost) * 0.5
        
        for i in range(len(path) - 1):
            current = path[i]
            next_node = path[i + 1]
            
            future_rewards = 0.0
            if i < len(path) - 2:
                future_link = f"{min(path[i+1], path[i+2])}_{max(path[i+1], path[i+2])}"
                future_rewards = -self.calculate_link_cost(future_link)
            
            self.q_table.update_q_value(
                current,
                next_node,
                path[-1] if len(path) > 1 else current,
                reward,
                future_rewards
            )
        
        if actual_cost > expected_cost * 1.5:
            self.failure_history.append({
                'path': path,
                'actual_cost': actual_cost,
                'expected_cost': expected_cost,
            })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "algorithm": self.algorithm.value,
            "routing_decisions": len(self.routing_history),
            "q_table_size": len(self.q_table.q_table),
            "exploration_rate": self.q_table.exploration_rate,
            "failures": len(self.failure_history),
            "average_cost": sum(d.cost for d in self.routing_history) / max(1, len(self.routing_history)),
        }
