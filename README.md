# ⚛️ QNet: Quantum-Decentralized Networking Protocol & Simulator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/Build-Passing-success.svg)](#)
[![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)](https://github.com/qnet/qnet)
[![Open Source](https://img.shields.io/badge/Open%20Source-💜-purple.svg)](#)

> A production-grade quantum networking simulation framework combining quantum physics principles with decentralized networking protocols.

```
╔═══════════════════════════════════════════════════════════════╗
║   ███████╗██╗  ██╗██╗   ██╗████████╗██╗   ██╗ ██████╗ ██████╗ ██████╗  ║
║   ██╔════╝██║ ██╔╝╚██╗ ██╔╝╚══██╔══╝╚██╗ ██╔╝██╔═══██╗██╔══██╗██╔══██╗ ║
║   ███████╗█████╔╝  ╚████╔╝    ██║    ╚████╔╝ ██║   ██║██████╔╝██║  ██║ ║
║   ╚════██║██╔═██╗   ╚██╔╝     ██║     ╚██╔╝  ██║   ██║██╔══██╗██║  ██║ ║
║   ███████║██║  ██╗   ██║      ██║      ██║   ╚██████╔╝██║  ██║██████╔╝ ║
║   ╚══════╝╚═╝  ╚═╝   ╚═╝      ╚═╝      ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═════╝  ║
╚═══════════════════════════════════════════════════════════════╝
```

## 🌟 Features

### Core Quantum Features
- **Quantum Entanglement** - Bell state generation and management
- **Quantum Teleportation** - State transfer using entanglement
- **Quantum Superposition** - Multi-qubit state representations (GHZ, W, cluster states)
- **Decoherence Modeling** - Realistic quantum noise simulation

### Network Capabilities
- **Multi-topology Support** - Mesh, scale-free, small-world, random, ring, star
- **Scalable** - 10 to 10,000+ nodes
- **Hybrid Communication** - Quantum and classical channels
- **Real-time Routing** - AI-powered adaptive routing

### Security
- **QKD Protocols** - BB84, E91 implementation
- **Attack Simulation** - MITM, DoS, eavesdropping, node compromise
- **Eavesdropping Detection** - QBER-based detection

### AI Integration
- **Q-Learning Router** - Self-optimizing routing decisions
- **Traffic Prediction** - Pattern recognition and forecasting
- **Self-Healing** - Automatic failure detection and recovery

### Visualization
- **Web Dashboard** - Real-time network visualization
- **CLI Tool** - Hacker-style terminal interface
- **ASCII Maps** - Network topology visualization

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/qnet/qnet.git
cd qnet

# Install dependencies
pip install -e .

# Or with Docker
docker-compose up -d
```

### CLI Usage

```bash
# Initialize network
qnet init --nodes 100 --topology scale_free

# Run simulation
qnet simulate --nodes 100 --duration 60

# View network map
qnet map --nodes 50

# Simulate attack
qnet attack mitm --target node_0

# Check status
qnet status

# Run benchmarks
qnet benchmark
```

### Python API

```python
from qnet.core.simulation.engine import SimulationEngine, SimulationConfig
from qnet.core.network.topology import TopologyType

# Create simulation
config = SimulationConfig(
    node_count=100,
    topology_type=TopologyType.SCALE_FREE,
    seed=42,
)

engine = SimulationEngine(config)
engine.initialize()

# Start simulation
engine.start()

# Get network state
state = engine.get_network_state()
print(f"Nodes: {len(state['node_states'])}")
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      QNET SYSTEM ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    APPLICATION LAYER                       │   │
│  │   CLI Dashboard │ Web UI │ REST API │ WebSocket           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     ROUTING LAYER                         │   │
│  │   AI Router │ Q-Learning │ Dijkstra │ A*                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    TRANSPORT LAYER                        │   │
│  │   Packets │ Channels │ Buffers │ Flow Control            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     QUANTUM LAYER                         │   │
│  │   Qubits │ Entanglement │ Teleportation │ Decoherence     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔬 Quantum Physics Implementation

### Qubit Representation
```
|ψ⟩ = α|0⟩ + β|1⟩  where |α|² + |β|² = 1
```

### Bell States (Entangled Pairs)
```
|Φ+⟩ = (|00⟩ + |11⟩)/√2  ← Most common
|Φ-⟩ = (|00⟩ - |11⟩)/√2
|Ψ+⟩ = (|01⟩ + |10⟩)/√2
|Ψ-⟩ = (|01⟩ - |10⟩)/√2
```

### Decoherence Model
```
F(t) = F₀ × e^(-γt)  where γ = 1/τ (decay rate)
```

## 📁 Project Structure

```
qnet/
├── qnet/                    # Main Python package
│   ├── core/                # Core simulation engine
│   │   ├── quantum/         # Quantum layer
│   │   ├── transport/       # Transport layer
│   │   ├── network/          # Network layer
│   │   └── simulation/       # Simulation engine
│   ├── security/            # Security & QKD
│   ├── ai/                  # AI optimization
│   ├── api/                 # REST/WebSocket API
│   └── cli/                 # CLI interface
├── frontend/                # React dashboard
├── docs/                    # Documentation
├── tests/                   # Unit tests
├── docker/                  # Docker configs
└── config/                 # Configuration files
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=qnet --cov-report=html

# Specific test file
pytest tests/test_quantum.py -v
```

## 🐳 Docker Deployment

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Scale nodes
docker-compose up -d --scale api=3
```

## 📚 Documentation

- [Protocol Specification](docs/rfc-qnet-001.md)
- [Architecture Guide](docs/architecture.md)
- [Quantum Concepts](docs/quantum-concepts.md)
- [Beginner's Guide](docs/guides/beginner.md)
- [Advanced Topics](docs/guides/advanced.md)
- [API Reference](docs/api-reference.md)

## 🎯 Use Cases

1. **Research** - Study quantum networking protocols
2. **Education** - Learn quantum computing concepts
3. **Security Testing** - Test QKD implementations
4. **Algorithm Development** - Develop routing algorithms
5. **Simulation** - Model quantum network behavior

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Quantum physics research community
- Network simulation pioneers
- Open source contributors

---

**Built with 💜 for the quantum future**
