"""
Event Scheduler - Event-driven simulation scheduling.

Implements priority queue-based event scheduling for
efficient simulation event management.
"""

from __future__ import annotations

import time
import heapq
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Tuple
from enum import Enum
from queue import PriorityQueue
import threading


class EventType(Enum):
    """Types of simulation events."""
    PACKET_GENERATION = "packet_generation"
    PACKET_ARRIVAL = "packet_arrival"
    PACKET_DELIVERY = "packet_delivery"
    DECOHERENCE = "decoherence"
    ENTANGLEMENT_CREATE = "entanglement_create"
    ENTANGLEMENT_PURIFY = "entanglement_purify"
    TELEPORTATION = "teleportation"
    ROUTING_UPDATE = "routing_update"
    NODE_FAILURE = "node_failure"
    LINK_FAILURE = "link_failure"
    AI_OPTIMIZATION = "ai_optimization"
    METRICS_COLLECTION = "metrics_collection"
    ATTACK = "attack"
    ATTACK_DETECTED = "attack_detected"
    CUSTOM = "custom"


@dataclass
class SimulationEvent:
    """
    Discrete simulation event.
    
    Represents a timed action to be executed during simulation.
    """
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.CUSTOM
    scheduled_time: float = 0.0
    priority: int = 0
    callback: Optional[Callable] = None
    data: Any = None
    repeatable: bool = False
    interval: float = 0.0
    created_at: float = field(default_factory=time.time)
    source_node: Optional[str] = None
    target_node: Optional[str] = None
    
    def __lt__(self, other: SimulationEvent) -> bool:
        """Compare events for priority queue ordering."""
        if self.scheduled_time != other.scheduled_time:
            return self.scheduled_time < other.scheduled_time
        return self.priority < other.priority
    
    def __repr__(self) -> str:
        return f"Event({self.event_type.value}, t={self.scheduled_time:.3f})"


@dataclass
class ScheduledEvent:
    """Wrapper for heap-based scheduling."""
    event: SimulationEvent
    insertion_order: int = 0
    
    def __lt__(self, other: ScheduledEvent) -> bool:
        if self.event.scheduled_time != other.event.scheduled_time:
            return self.event.scheduled_time < other.event.scheduled_time
        return self.insertion_order < other.insertion_order


class EventScheduler:
    """
    Priority queue-based event scheduler.
    
    Manages simulation events with O(log n) insertion and
    extraction, supporting both one-time and periodic events.
    
    Features:
    - Priority-based event ordering
    - Periodic event scheduling
    - Event cancellation
    - Thread-safe operations
    """
    
    def __init__(self):
        """Initialize event scheduler."""
        self._events: List[ScheduledEvent] = []
        self._event_map: Dict[str, SimulationEvent] = {}
        self._lock = threading.RLock()
        self._current_time: float = 0.0
        self._event_counter: int = 0
        self._callbacks: Dict[EventType, List[Callable]] = {}
        self._stats = {
            "total_scheduled": 0,
            "total_processed": 0,
            "total_cancelled": 0,
        }
    
    @property
    def current_time(self) -> float:
        """Current simulation time."""
        return self._current_time
    
    @current_time.setter
    def current_time(self, value: float) -> None:
        """Set simulation time."""
        self._current_time = value
    
    @property
    def queue_size(self) -> int:
        """Number of events in queue."""
        return len(self._events)
    
    @property
    def statistics(self) -> Dict[str, Any]:
        """Scheduler statistics."""
        return {
            **self._stats,
            "queue_size": self.queue_size,
            "current_time": self._current_time,
        }
    
    def schedule_event(
        self,
        event_type: EventType,
        delay: float,
        callback: Optional[Callable] = None,
        data: Any = None,
        priority: int = 0,
        repeatable: bool = False,
        interval: float = 0.0,
        at_time: Optional[float] = None,
    ) -> str:
        """
        Schedule a new event.
        
        Args:
            event_type: Type of event
            delay: Delay from current time
            callback: Function to call when event fires
            data: Event data
            priority: Event priority (lower = higher priority)
            repeatable: Whether event should repeat
            interval: Repeat interval (if repeatable)
            at_time: Absolute time to fire (overrides delay)
            
        Returns:
            Event ID
        """
        with self._lock:
            event = SimulationEvent(
                event_type=event_type,
                scheduled_time=at_time if at_time is not None else self._current_time + delay,
                priority=priority,
                callback=callback,
                data=data,
                repeatable=repeatable,
                interval=interval,
            )
            
            self._event_counter += 1
            scheduled = ScheduledEvent(event=event, insertion_order=self._event_counter)
            
            heapq.heappush(self._events, scheduled)
            self._event_map[event.event_id] = event
            self._stats["total_scheduled"] += 1
            
            if event_type in self._callbacks:
                self._callbacks[event_type].append(callback)
            
            return event.event_id
    
    def schedule_at(
        self,
        event_type: EventType,
        time: float,
        callback: Optional[Callable] = None,
        data: Any = None,
        priority: int = 0,
    ) -> str:
        """Schedule event at specific time."""
        return self.schedule_event(
            event_type, delay=0, callback=callback, data=data,
            priority=priority, at_time=time
        )
    
    def cancel_event(self, event_id: str) -> bool:
        """
        Cancel a scheduled event.
        
        Note: Events already processed cannot be cancelled.
        
        Args:
            event_id: ID of event to cancel
            
        Returns:
            True if event was found and cancelled
        """
        with self._lock:
            if event_id not in self._event_map:
                return False
            
            event = self._event_map[event_id]
            event.data = None
            
            self._stats["total_cancelled"] += 1
            return True
    
    def get_next_event(self) -> Optional[SimulationEvent]:
        """
        Peek at next event without removing it.
        
        Returns:
            Next event or None if queue is empty
        """
        with self._lock:
            if not self._events:
                return None
            return self._events[0].event
    
    def get_due_events(self, current_time: Optional[float] = None) -> List[SimulationEvent]:
        """
        Get all events due at current time.
        
        Args:
            current_time: Current simulation time (uses internal if None)
            
        Returns:
            List of due events
        """
        with self._lock:
            if current_time is None:
                current_time = self._current_time
            
            due_events = []
            
            while self._events and self._events[0].event.scheduled_time <= current_time:
                scheduled = heapq.heappop(self._events)
                event = scheduled.event
                
                if event.data is None:
                    continue
                
                due_events.append(event)
                self._event_map.pop(event.event_id, None)
                self._stats["total_processed"] += 1
                
                if event.repeatable and event.interval > 0:
                    new_event = SimulationEvent(
                        event_type=event.event_type,
                        scheduled_time=current_time + event.interval,
                        priority=event.priority,
                        callback=event.callback,
                        data=event.data,
                        repeatable=True,
                        interval=event.interval,
                    )
                    
                    self._event_counter += 1
                    new_scheduled = ScheduledEvent(event=new_event, insertion_order=self._event_counter)
                    heapq.heappush(self._events, new_scheduled)
                    self._event_map[new_event.event_id] = new_event
            
            return due_events
    
    def get_events_by_type(self, event_type: EventType) -> List[SimulationEvent]:
        """Get all events of a specific type."""
        with self._lock:
            return [
                e for e in self._event_map.values()
                if e.event_type == event_type
            ]
    
    def get_events_in_range(
        self,
        start_time: float,
        end_time: float
    ) -> List[SimulationEvent]:
        """Get all events in time range."""
        with self._lock:
            return [
                e for e in self._event_map.values()
                if start_time <= e.scheduled_time <= end_time
            ]
    
    def clear(self) -> int:
        """
        Clear all scheduled events.
        
        Returns:
            Number of events cleared
        """
        with self._lock:
            count = len(self._events)
            self._events.clear()
            self._event_map.clear()
            return count
    
    def register_type_callback(self, event_type: EventType, callback: Callable) -> None:
        """Register global callback for event type."""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
    
    def advance_time(self, delta: float) -> None:
        """Advance simulation time."""
        self._current_time += delta
    
    def set_time(self, time: float) -> None:
        """Set simulation time directly."""
        self._current_time = time
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize scheduler state."""
        return {
            "current_time": self._current_time,
            "queue_size": self.queue_size,
            "statistics": self._stats,
            "next_event": str(self.get_next_event()) if self.get_next_event() else None,
        }
    
    def __len__(self) -> int:
        return len(self._events)
    
    def __repr__(self) -> str:
        return f"EventScheduler(t={self._current_time:.3f}, queue={self.queue_size})"


class HierarchicalScheduler:
    """
    Hierarchical scheduler for multi-level event processing.
    
    Organizes events into priority levels for more
    efficient processing of high-priority events.
    """
    
    def __init__(self, levels: int = 3):
        """
        Initialize hierarchical scheduler.
        
        Args:
            levels: Number of priority levels
        """
        self.level_schedulers: List[EventScheduler] = [
            EventScheduler() for _ in range(levels)
        ]
        self.levels = levels
        self._global_time: float = 0.0
    
    def schedule_event(
        self,
        event_type: EventType,
        delay: float,
        level: int,
        **kwargs
    ) -> str:
        """Schedule event at specific level."""
        if 0 <= level < self.levels:
            return self.level_schedulers[level].schedule_event(
                event_type, delay, **kwargs
            )
        return ""
    
    def get_due_events(self) -> List[SimulationEvent]:
        """Get due events from all levels (highest priority first)."""
        events = []
        for scheduler in self.level_schedulers:
            events.extend(scheduler.get_due_events(self._global_time))
        return events
    
    def advance_time(self, delta: float) -> None:
        """Advance global time."""
        self._global_time += delta
        for scheduler in self.level_schedulers:
            scheduler.advance_time(delta)
    
    @property
    def queue_size(self) -> int:
        """Total events across all levels."""
        return sum(s.queue_size for s in self.level_schedulers)
