"""
Packet Buffer - Queue management for packets in transit.

Implements priority queues, overflow handling, and buffer
management for quantum network packets.
"""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Iterator, Callable
from enum import Enum
from queue import PriorityQueue, Empty
import threading
import asyncio

from qnet.core.transport.packet import Packet, PacketPriority, PacketState


class BufferOverflowError(Exception):
    """Raised when buffer exceeds capacity."""
    pass


class BufferFullError(Exception):
    """Raised when trying to add to full buffer."""
    pass


class BufferEmptyError(Exception):
    """Raised when trying to get from empty buffer."""
    pass


class BufferStrategy(Enum):
    """Buffer overflow handling strategies."""
    DROP_TAIL = "drop_tail"
    DROP_HEAD = "drop_head"
    DROP_PRIORITY = "drop_priority"
    BLOCK = "block"
    OVERWRITE = "overwrite"


@dataclass
class BufferedPacket:
    """
    Packet with buffer-specific metadata.
    
    Wraps a packet with timing and priority information
    for buffer management.
    """
    packet: Packet
    priority: int
    enqueued_at: float = field(default_factory=time.time)
    attempts: int = 0
    max_attempts: int = 3
    
    def __lt__(self, other: BufferedPacket) -> bool:
        """Compare for priority queue ordering."""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.enqueued_at < other.enqueued_at


@dataclass
class BufferMetrics:
    """Metrics for buffer performance monitoring."""
    packets_added: int = 0
    packets_removed: int = 0
    packets_dropped: int = 0
    packets_overwritten: int = 0
    overflow_count: int = 0
    average_wait_time: float = 0.0
    total_wait_time: float = 0.0
    peak_usage: int = 0
    
    @property
    def current_usage(self) -> int:
        """Estimate current buffer usage."""
        return self.packets_added - self.packets_removed - self.packets_dropped
    
    @property
    def drop_rate(self) -> float:
        """Packet drop rate."""
        total = self.packets_added + self.packets_dropped
        return self.packets_dropped / total if total > 0 else 0.0


class PacketBuffer:
    """
    Priority buffer for network packets.
    
    Implements thread-safe packet queuing with priority support,
    multiple overflow strategies, and comprehensive metrics.
    
    Features:
    - Priority-based packet ordering
    - Multiple overflow strategies
    - Thread-safe operations
    - Packet expiration handling
    - Metrics collection
    """
    
    def __init__(
        self,
        capacity: int = 1000,
        strategy: BufferStrategy = BufferStrategy.DROP_TAIL,
        enable_metrics: bool = True,
        expiration_time: Optional[float] = None,
    ):
        """
        Initialize packet buffer.
        
        Args:
            capacity: Maximum number of packets
            strategy: Overflow handling strategy
            enable_metrics: Whether to collect metrics
            expiration_time: Packet expiration time in seconds
        """
        self.capacity = capacity
        self.strategy = strategy
        self.enable_metrics = enable_metrics
        self.expiration_time = expiration_time
        
        self._buffer: List[BufferedPacket] = []
        self._lock = threading.RLock()
        self._metrics = BufferMetrics() if enable_metrics else None
        self._callbacks: Dict[str, Callable] = {}
        
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
    
    @property
    def size(self) -> int:
        """Current buffer size."""
        with self._lock:
            return len(self._buffer)
    
    @property
    def available(self) -> int:
        """Available slots in buffer."""
        return self.capacity - self.size
    
    @property
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self.size >= self.capacity
    
    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self.size == 0
    
    @property
    def utilization(self) -> float:
        """Buffer utilization percentage."""
        return self.size / self.capacity if self.capacity > 0 else 0.0
    
    def add(
        self,
        packet: Packet,
        priority: Optional[int] = None,
        force: bool = False
    ) -> bool:
        """
        Add packet to buffer.
        
        Args:
            packet: Packet to add
            priority: Override packet priority (lower = higher priority)
            force: Force add even if buffer is full
            
        Returns:
            True if packet was added, False otherwise
            
        Raises:
            BufferFullError: If buffer is full and force is False
        """
        if priority is None:
            priority = packet.header.priority.value
        
        with self._lock:
            if self.is_full:
                if force:
                    self._handle_overflow()
                else:
                    self._increment_metric('overflow_count')
                    raise BufferFullError(f"Buffer full ({self.size}/{self.capacity})")
            
            buffered = BufferedPacket(packet=packet, priority=priority)
            self._buffer.append(buffered)
            self._buffer.sort(key=lambda x: (x.priority, x.enqueued_at))
            
            self._increment_metric('packets_added')
            
            if self.enable_metrics and self._metrics:
                self._metrics.peak_usage = max(self._metrics.peak_usage, self.size)
            
            self._not_full.notify() if self.size >= self.capacity else None
            
            return True
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Packet:
        """
        Get next packet from buffer.
        
        Args:
            block: Whether to block if buffer is empty
            timeout: Maximum time to wait
            
        Returns:
            Next packet from buffer
            
        Raises:
            BufferEmptyError: If buffer is empty and block is False
        """
        with self._not_empty:
            if block:
                if timeout is None:
                    while self.is_empty:
                        self._not_empty.wait()
                else:
                    end_time = time.time() + timeout
                    while self.is_empty:
                        remaining = end_time - time.time()
                        if remaining <= 0:
                            raise BufferEmptyError("Buffer empty, timeout expired")
                        self._not_empty.wait(remaining)
            else:
                if self.is_empty:
                    raise BufferEmptyError("Buffer is empty")
            
            buffered = self._buffer.pop(0)
            self._increment_metric('packets_removed')
            
            if self.enable_metrics and self._metrics:
                wait_time = time.time() - buffered.enqueued_at
                self._metrics.total_wait_time += wait_time
                self._metrics.average_wait_time = (
                    self._metrics.total_wait_time / self._metrics.packets_removed
                )
            
            self._not_full.notify()
            
            return buffered.packet
    
    def peek(self) -> Optional[Packet]:
        """
        View next packet without removing it.
        
        Returns:
            Next packet or None if empty
        """
        with self._lock:
            if self.is_empty:
                return None
            return self._buffer[0].packet
    
    def remove(self, packet_id: str) -> bool:
        """
        Remove specific packet by ID.
        
        Args:
            packet_id: ID of packet to remove
            
        Returns:
            True if packet was found and removed
        """
        with self._lock:
            for i, buffered in enumerate(self._buffer):
                if buffered.packet.header.packet_id == packet_id:
                    self._buffer.pop(i)
                    self._increment_metric('packets_removed')
                    return True
            return False
    
    def clear(self) -> int:
        """
        Clear all packets from buffer.
        
        Returns:
            Number of packets cleared
        """
        with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            return count
    
    def get_expired(self) -> List[Packet]:
        """
        Get and remove expired packets.
        
        Returns:
            List of expired packets
        """
        if self.expiration_time is None:
            return []
        
        expired = []
        current_time = time.time()
        
        with self._lock:
            remaining = []
            for buffered in self._buffer:
                if current_time - buffered.enqueued_at > self.expiration_time:
                    expired.append(buffered.packet)
                    self._increment_metric('packets_dropped')
                else:
                    remaining.append(buffered)
            self._buffer = remaining
        
        return expired
    
    def get_by_priority(self, min_priority: int) -> List[Packet]:
        """
        Get all packets with priority >= min_priority.
        
        Args:
            min_priority: Minimum priority level
            
        Returns:
            List of matching packets
        """
        with self._lock:
            return [
                b.packet for b in self._buffer
                if b.priority >= min_priority
            ]
    
    def _handle_overflow(self) -> None:
        """Handle buffer overflow based on strategy."""
        self._increment_metric('overflow_count')
        
        if self.strategy == BufferStrategy.DROP_TAIL:
            self._buffer.pop()
            self._increment_metric('packets_dropped')
        
        elif self.strategy == BufferStrategy.DROP_HEAD:
            self._buffer.pop(0)
            self._increment_metric('packets_dropped')
        
        elif self.strategy == BufferStrategy.DROP_PRIORITY:
            lowest = max(range(len(self._buffer)), 
                        key=lambda i: self._buffer[i].priority)
            self._buffer.pop(lowest)
            self._increment_metric('packets_dropped')
        
        elif self.strategy == BufferStrategy.OVERWRITE:
            if self._buffer:
                self._buffer.pop(0)
                self._increment_metric('packets_overwritten')
    
    def _increment_metric(self, metric: str) -> None:
        """Increment a metric counter."""
        if self.enable_metrics and self._metrics:
            if hasattr(self._metrics, metric):
                setattr(self._metrics, metric, getattr(self._metrics, metric) + 1)
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Register callback for buffer events.
        
        Args:
            event: Event type ('full', 'empty', 'drop')
            callback: Callback function
        """
        self._callbacks[event] = callback
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get buffer metrics."""
        if not self.enable_metrics or not self._metrics:
            return {}
        
        return {
            "capacity": self.capacity,
            "current_size": self.size,
            "utilization": self.utilization,
            "peak_usage": self._metrics.peak_usage,
            "packets_added": self._metrics.packets_added,
            "packets_removed": self._metrics.packets_removed,
            "packets_dropped": self._metrics.packets_dropped,
            "overflow_count": self._metrics.overflow_count,
            "average_wait_time": self._metrics.average_wait_time,
            "drop_rate": self._metrics.drop_rate,
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        if self.enable_metrics and self._metrics:
            self._metrics = BufferMetrics()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize buffer state to dictionary."""
        return {
            "capacity": self.capacity,
            "current_size": self.size,
            "strategy": self.strategy.value,
            "is_full": self.is_full,
            "is_empty": self.is_empty,
            "utilization": self.utilization,
            "metrics": self.get_metrics(),
        }
    
    def __len__(self) -> int:
        return self.size
    
    def __contains__(self, packet_id: str) -> bool:
        """Check if packet ID is in buffer."""
        return any(
            b.packet.header.packet_id == packet_id
            for b in self._buffer
        )


class MultiQueueBuffer:
    """
    Multi-queue buffer with separate queues per priority level.
    
    Provides better isolation between priority levels and
    more predictable behavior under load.
    """
    
    def __init__(self, capacity_per_queue: int = 100):
        """
        Initialize multi-queue buffer.
        
        Args:
            capacity_per_queue: Capacity for each priority queue
        """
        self.capacity_per_queue = capacity_per_queue
        self.queues: Dict[PacketPriority, PacketBuffer] = {
            priority: PacketBuffer(capacity_per_queue, BufferStrategy.DROP_TAIL)
            for priority in PacketPriority
        }
        self._lock = threading.RLock()
    
    @property
    def size(self) -> int:
        """Total packets across all queues."""
        return sum(q.size for q in self.queues.values())
    
    @property
    def is_full(self) -> bool:
        """Check if all queues are full."""
        return all(q.is_full for q in self.queues.values())
    
    def add(self, packet: Packet) -> bool:
        """Add packet to appropriate queue."""
        priority = packet.header.priority
        queue = self.queues[priority]
        
        try:
            return queue.add(packet)
        except BufferFullError:
            return False
    
    def get(self, min_priority: PacketPriority = PacketPriority.LOW) -> Optional[Packet]:
        """
        Get packet from highest priority non-empty queue.
        
        Args:
            min_priority: Minimum priority level to consider
            
        Returns:
            Next packet or None
        """
        for priority in PacketPriority:
            if priority.value < min_priority.value:
                continue
            queue = self.queues[priority]
            try:
                return queue.get(block=False)
            except BufferEmptyError:
                continue
        return None
    
    def clear(self) -> None:
        """Clear all queues."""
        for queue in self.queues.values():
            queue.clear()
    
    def get_queue_size(self, priority: PacketPriority) -> int:
        """Get size of specific priority queue."""
        return self.queues[priority].size
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for all queues."""
        return {
            "total_size": self.size,
            "queues": {
                priority.name: queue.get_metrics()
                for priority, queue in self.queues.items()
            }
        }
