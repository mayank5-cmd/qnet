"""
QNet API - FastAPI REST and WebSocket endpoints.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import time

from qnet.core.simulation.engine import SimulationEngine, SimulationConfig, SimulationState
from qnet.core.network.topology import TopologyType
from qnet.security.qkd import QKDManager, QKDProtocolType
from qnet.security.attacks import AttackSimulator


app = FastAPI(
    title="QNet API",
    description="Quantum-Decentralized Network Protocol & Simulator API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


simulation_engine: Optional[SimulationEngine] = None
qkd_manager = QKDManager()
attack_simulator = AttackSimulator()


class NetworkCreateRequest(BaseModel):
    nodes: int = 100
    topology: str = "scale_free"
    duration: float = 60.0
    seed: Optional[int] = 42


class PacketSendRequest(BaseModel):
    source: str
    destination: str
    packet_type: str = "QUANTUM_DATA"
    payload: Optional[str] = None


class QKDRequest(BaseModel):
    node_a: str
    node_b: str
    protocol: str = "BB84"
    bits: int = 1024


class AttackRequest(BaseModel):
    attack_type: str
    target: Optional[str] = None
    intensity: float = 0.5


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


ws_manager = WebSocketManager()


@app.get("/")
async def root():
    return {
        "name": "QNet API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/network/create")
async def create_network(request: NetworkCreateRequest):
    global simulation_engine
    
    topo_map = {
        "mesh": TopologyType.MESH,
        "star": TopologyType.STAR,
        "ring": TopologyType.RING,
        "scale_free": TopologyType.SCALE_FREE,
        "random": TopologyType.RANDOM,
        "small_world": TopologyType.WATTS_STROGATZ,
    }
    
    config = SimulationConfig(
        node_count=request.nodes,
        duration=request.duration,
        topology_type=topo_map.get(request.topology, TopologyType.SCALE_FREE),
        seed=request.seed or 42,
    )
    
    simulation_engine = SimulationEngine(config)
    success = simulation_engine.initialize()
    
    if success:
        return {
            "status": "success",
            "nodes": request.nodes,
            "links": len(simulation_engine.topology.link_manager.links),
            "message": f"Network created with {request.nodes} nodes",
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to create network")


@app.get("/network/status")
async def network_status():
    if not simulation_engine or not simulation_engine.topology:
        raise HTTPException(status_code=404, detail="Network not initialized")
    
    return simulation_engine.get_network_state()


@app.get("/network/topology")
async def network_topology():
    if not simulation_engine or not simulation_engine.topology:
        raise HTTPException(status_code=404, detail="Network not initialized")
    
    return simulation_engine.topology.to_dict()


@app.post("/simulation/start")
async def start_simulation():
    global simulation_engine
    
    if not simulation_engine:
        raise HTTPException(status_code=404, detail="Network not initialized")
    
    success = simulation_engine.start()
    
    return {"status": "success" if success else "failed"}


@app.post("/simulation/stop")
async def stop_simulation():
    global simulation_engine
    
    if not simulation_engine:
        raise HTTPException(status_code=404, detail="Network not initialized")
    
    success = simulation_engine.stop()
    
    return {"status": "success" if success else "failed"}


@app.post("/simulation/pause")
async def pause_simulation():
    global simulation_engine
    
    if not simulation_engine:
        raise HTTPException(status_code=404, detail="Network not initialized")
    
    success = simulation_engine.pause()
    
    return {"status": "success" if success else "failed"}


@app.get("/simulation/stats")
async def simulation_stats():
    if not simulation_engine:
        raise HTTPException(status_code=404, detail="Network not initialized")
    
    return simulation_engine.get_statistics()


@app.post("/packet/send")
async def send_packet(request: PacketSendRequest):
    if not simulation_engine:
        raise HTTPException(status_code=404, detail="Network not initialized")
    
    from qnet.core.transport.packet import PacketType
    
    packet_types = {
        "QUANTUM_DATA": PacketType.QUANTUM_DATA,
        "CONTROL_MESSAGE": PacketType.CONTROL_MESSAGE,
        "ROUTING_UPDATE": PacketType.ROUTING_UPDATE,
        "ENTANGLEMENT_REQUEST": PacketType.ENTANGLEMENT_REQUEST,
    }
    
    packet_type = packet_types.get(request.packet_type, PacketType.QUANTUM_DATA)
    payload = request.payload.encode() if request.payload else b""
    
    packet = simulation_engine.send_packet(
        source=request.source,
        destination=request.destination,
        packet_type=packet_type,
        payload=payload,
    )
    
    return {
        "status": "success" if packet else "failed",
        "packet_id": packet.header.packet_id if packet else None,
    }


@app.post("/qkd/generate")
async def generate_key(request: QKDRequest):
    protocol_map = {
        "BB84": QKDProtocolType.BB84,
        "E91": QKDProtocolType.E91,
    }
    
    protocol = protocol_map.get(request.protocol, QKDProtocolType.BB84)
    
    result = qkd_manager.generate_key(
        node_a=request.node_a,
        node_b=request.node_b,
        protocol=protocol,
        num_bits=request.bits,
    )
    
    return result.to_dict()


@app.get("/qkd/stats")
async def qkd_stats():
    return qkd_manager.get_statistics()


@app.post("/attack/simulate")
async def simulate_attack(request: AttackRequest):
    result = attack_simulator.simulate_dos(
        target_node=request.target or "node_0",
        duration=10.0,
        intensity=request.intensity,
    )
    
    return {
        "attack_id": result.attack.attack_id,
        "attack_type": result.attack.attack_type.value,
        "success": result.attack.success,
        "detected": result.attack.detected,
        "message": result.message,
    }


@app.get("/attack/stats")
async def attack_stats():
    return attack_simulator.get_attack_statistics()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe":
                pass
            
            elif message.get("type") == "get_status":
                if simulation_engine:
                    await websocket.send_json(simulation_engine.get_network_state())
            
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": time.time()})
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


async def broadcast_updates():
    while True:
        if simulation_engine and simulation_engine.state == SimulationState.RUNNING:
            state = simulation_engine.get_network_state()
            await ws_manager.broadcast({
                "type": "update",
                "timestamp": time.time(),
                "data": state,
            })
        
        await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_updates())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
