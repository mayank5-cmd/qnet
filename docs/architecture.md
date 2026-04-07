# QNet Architecture Guide

## System Overview

QNet implements a layered architecture combining quantum communication protocols with traditional networking concepts.

## Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                         QNET SYSTEM                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    PRESENTATION LAYER                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │   │
│  │  │   CLI    │  │  Web UI  │  │ REST API │  │ WebSocket│  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     SERVICE LAYER                        │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐     │   │
│  │  │   QKD      │  │   Router   │  │  Self-Healer   │     │   │
│  │  │  Service   │  │  Service   │  │    Service     │     │   │
│  │  └────────────┘  └────────────┘  └────────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   SIMULATION ENGINE                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │Scheduler │  │ Monitor  │  │ Topology │  │  Events  │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     CORE LAYER                          │   │
│  │  ┌─────────────────────────────────────────────────┐     │   │
│  │  │  QUANTUM LAYER  │  TRANSPORT LAYER  │ NETWORK  │     │   │
│  │  │  ┌───────────┐  │  ┌───────────┐    │  LAYER   │     │   │
│  │  │  │  Qubits   │  │  │  Packets  │    │  ┌─────┐ │     │   │
│  │  │  │ Entangle  │  │  │  Channels │    │  │Node │ │     │   │
│  │  │  │ Teleport  │  │  │  Buffers  │    │  │Link │ │     │   │
│  │  │  │Decoherence│  │  │           │    │  └─────┘ │     │   │
│  │  │  └───────────┘  │  └───────────┘    │           │     │   │
│  │  └─────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Request
     │
     ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│   CLI   │───▶│  API    │───▶│ Engine  │───▶│ Network │
│   Web   │    │ Gateway │    │         │    │ Topology│
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │  Monitoring │
                              │   & Alerts  │
                              └─────────────┘
```

## Key Classes

### Quantum Layer

- `Qubit` - Quantum bit representation
- `EntangledPair` - Bell state management
- `QuantumTeleportation` - State transfer
- `DecoherenceModel` - Noise simulation

### Network Layer

- `QuantumNode` - Network node
- `QuantumLink` - Node connections
- `NetworkTopology` - Network structure

### Simulation Layer

- `SimulationEngine` - Main simulation loop
- `EventScheduler` - Event processing
- `SimulationMonitor` - Metrics collection

## Threading Model

```
Main Thread
    │
    ├── Simulation Thread (event-driven loop)
    │
    ├── API Thread (FastAPI/Uvicorn)
    │
    ├── WebSocket Thread (real-time updates)
    │
    └── Monitor Thread (metrics collection)
```

## State Management

```
SimulationEngine
    │
    ├── topology: NetworkTopology
    │       │
    │       ├── nodes: Dict[str, QuantumNode]
    │       │
    │       └── link_manager: LinkManager
    │               │
    │               └── links: Dict[str, QuantumLink]
    │
    ├── scheduler: EventScheduler
    │
    └── monitor: SimulationMonitor
```

## Performance Considerations

1. **Large Networks** - Use NetworkX for efficient graph operations
2. **Quantum Simulation** - Vectorized numpy operations
3. **Event Processing** - Priority queue for O(log n) scheduling
4. **Memory** - Object pooling for qubits and packets

## Scalability

| Scale | Nodes | Memory | Use Case |
|-------|-------|--------|----------|
| Small | 10-100 | <500MB | Testing |
| Medium | 100-1000 | 1-4GB | Development |
| Large | 1000-10000 | 4-16GB | Production |
| XLarge | 10000+ | 16GB+ | Research |
