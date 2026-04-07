"""
QNet CLI - Command-line interface with hacker aesthetic.

A powerful terminal interface for QNet operations including
simulation control, attack simulation, and network visualization.
"""

import click
import asyncio
import sys
import time
import json
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


console = Console() if RICH_AVAILABLE else None


def print_banner():
    """Print ASCII art banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███████╗██╗  ██╗██╗   ██╗████████╗██╗   ██╗ ██████╗ ██████╗ ██████╗  ║
    ║   ██╔════╝██║ ██╔╝╚██╗ ██╔╝╚══██╔══╝╚██╗ ██╔╝██╔═══██╗██╔══██╗██╔══██╗ ║
    ║   ███████╗█████╔╝  ╚████╔╝    ██║    ╚████╔╝ ██║   ██║██████╔╝██║  ██║ ║
    ║   ╚════██║██╔═██╗   ╚██╔╝     ██║     ╚██╔╝  ██║   ██║██╔══██╗██║  ██║ ║
    ║   ███████║██║  ██╗   ██║      ██║      ██║   ╚██████╔╝██║  ██║██████╔╝ ║
    ║   ╚══════╝╚═╝  ╚═╝   ╚═╝      ╚═╝      ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═════╝  ║
    ║                                                               ║
    ║          Quantum-Decentralized Networking Protocol & Simulator  ║
    ║                         Version 1.0.0                          ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    if console:
        console.print(banner, style="cyan bold")
    else:
        print(banner)


def print_success(msg: str):
    """Print success message."""
    if console:
        console.print(f"[green]✓[/green] {msg}")
    else:
        print(f"[SUCCESS] {msg}")


def print_error(msg: str):
    """Print error message."""
    if console:
        console.print(f"[red]✗[/red] {msg}")
    else:
        print(f"[ERROR] {msg}")


def print_warning(msg: str):
    """Print warning message."""
    if console:
        console.print(f"[yellow]![/yellow] {msg}")
    else:
        print(f"[WARNING] {msg}")


def print_info(msg: str):
    """Print info message."""
    if console:
        console.print(f"[blue]ℹ[/blue] {msg}")
    else:
        print(f"[INFO] {msg}")


class QNetCLI:
    """QNet Command Line Interface."""
    
    def __init__(self):
        """Initialize CLI."""
        self.engine = None
        self.running = False
    
    def create_network(self, nodes: int = 100, topology: str = "scale_free"):
        """Create quantum network."""
        from qnet.core.simulation.engine import SimulationEngine, SimulationConfig
        from qnet.core.network.topology import TopologyType
        
        topo_map = {
            "mesh": TopologyType.MESH,
            "star": TopologyType.STAR,
            "ring": TopologyType.RING,
            "scale_free": TopologyType.SCALE_FREE,
            "random": TopologyType.RANDOM,
            "small_world": TopologyType.WATTS_STROGATZ,
        }
        
        config = SimulationConfig(
            node_count=nodes,
            topology_type=topo_map.get(topology, TopologyType.SCALE_FREE),
            seed=42,
        )
        
        self.engine = SimulationEngine(config)
        
        if console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Initializing quantum network...", total=None)
                success = self.engine.initialize()
                progress.update(task, completed=True)
        else:
            success = self.engine.initialize()
        
        if success:
            print_success(f"Network created with {nodes} nodes")
            return True
        else:
            print_error("Failed to create network")
            return False
    
    def show_network_map(self, max_nodes: int = 50):
        """Display ASCII network topology map."""
        if not self.engine or not self.engine.topology:
            print_error("Network not initialized")
            return
        
        nodes = list(self.engine.topology.nodes.items())[:max_nodes]
        
        if console:
            table = Table(title="QNet Network Topology", box=box.DOUBLE_EDGE)
            table.add_column("Node ID", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Qubits", style="green")
            table.add_column("Fidelity", style="yellow")
            table.add_column("Neighbors", style="blue")
            
            for node_id, node in nodes:
                table.add_row(
                    node_id,
                    node.node_type.value,
                    str(node.qubit_count),
                    f"{node.average_fidelity:.3f}",
                    str(len(node.neighbors))
                )
            
            console.print(table)
        else:
            print("╔══════════════════════════════════════════════════════════╗")
            print("║           QNET NETWORK TOPOLOGY                          ║")
            print("╠══════════════════════════════════════════════════════════╣")
            for node_id, node in nodes:
                fidelity_bar = "█" * int(node.average_fidelity * 10)
                print(f"║ [{node.node_type.value[:3]}] {node_id:12} Q:{node.qubit_count:3} │{fidelity_bar}│ N:{len(node.neighbors):2} ║")
            print("╚══════════════════════════════════════════════════════════╝")
    
    def show_metrics(self):
        """Display network metrics."""
        if not self.engine:
            print_error("Network not initialized")
            return
        
        stats = self.engine.get_network_state()
        
        if console:
            panel = Panel(
                f"[cyan]Nodes Online:[/cyan] {stats.get('node_states', {}).values().__len__()}\n"
                f"[green]Active Links:[/green] {stats.get('topology', {}).get('edge_count', 0)}\n"
                f"[yellow]Elapsed:[/yellow] {stats.get('elapsed_time', 0):.1f}s",
                title="Network Metrics",
                border_style="blue"
            )
            console.print(panel)
        else:
            print("┌─────────────────────────────────────┐")
            print("│        NETWORK METRICS              │")
            print("├─────────────────────────────────────┤")
            print("│ Nodes Online:                       │")
            print("│ Active Links:                       │")
            print("│ Elapsed Time:                       │")
            print("└─────────────────────────────────────┘")
    
    def run_simulation(self, duration: float = 60.0):
        """Run simulation."""
        if not self.engine:
            print_error("Network not initialized")
            return
        
        self.engine.config.duration = duration
        
        if console:
            console.print("[bold cyan]Starting simulation...[/bold cyan]")
            self.engine.start()
            
            with Progress(console=console) as progress:
                task = progress.add_task("[cyan]Simulating...", total=int(duration))
                for i in range(int(duration)):
                    if not self.engine.state.value == "running":
                        break
                    progress.update(task, advance=1)
                    time.sleep(0.1)
        else:
            print("Starting simulation...")
            self.engine.start()
            time.sleep(min(duration, 5))
    
    def simulate_attack(self, attack_type: str, target: Optional[str] = None):
        """Simulate network attack."""
        from qnet.security.attacks import AttackSimulator, AttackType
        
        simulator = AttackSimulator()
        
        attack_map = {
            "mitm": AttackType.MITM,
            "eavesdrop": AttackType.EAVESDROPPING,
            "dos": AttackType.DOS,
            "compromise": AttackType.NODE_COMPROMISE,
        }
        
        atype = attack_map.get(attack_type.lower(), AttackType.EAVESDROPPING)
        
        if console:
            with console.status(f"[red]Simulating {attack_type} attack...[/red]"):
                time.sleep(1)
                
                if atype == AttackType.MITM:
                    result = simulator.simulate_mitm("node_0", target or "node_1")
                elif atype == AttackType.DOS:
                    result = simulator.simulate_dos(target or "node_0")
                else:
                    result = simulator.simulate_eavesdropping(None)
                
                console.print(Panel(
                    f"[red]Attack Type:[/red] {result.attack.attack_type.value}\n"
                    f"[yellow]Success:[/yellow] {result.attack.success}\n"
                    f"[blue]Message:[/blue] {result.message}",
                    title="Attack Result",
                    border_style="red"
                ))
        else:
            print(f"[*] Simulating {attack_type} attack on {target or 'random node'}...")
            time.sleep(1)
            print("[!] Attack simulation completed")


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """QNet - Quantum-Decentralized Networking Protocol & Simulator."""
    pass


@cli.command()
@click.option("--nodes", "-n", default=100, help="Number of nodes")
@click.option("--topology", "-t", default="scale_free", 
               type=click.Choice(["mesh", "star", "ring", "scale_free", "random", "small_world"]),
               help="Network topology")
def init(nodes, topology):
    """Initialize QNet network."""
    print_banner()
    cli_instance = QNetCLI()
    
    if console:
        console.print(f"[cyan]Creating network with {nodes} nodes...[/cyan]")
    else:
        print(f"Creating network with {nodes} nodes...")
    
    cli_instance.create_network(nodes, topology)
    cli_instance.show_network_map()


@cli.command()
@click.option("--nodes", "-n", default=100, help="Number of nodes")
@click.option("--duration", "-d", default=60.0, help="Simulation duration in seconds")
@click.option("--attack", "-a", help="Attack type to simulate")
def simulate(nodes, duration, attack):
    """Run network simulation."""
    print_banner()
    cli_instance = QNetCLI()
    
    cli_instance.create_network(nodes)
    cli_instance.run_simulation(duration)
    
    if attack:
        cli_instance.simulate_attack(attack)


@cli.command()
@click.option("--nodes", "-n", default=50, help="Maximum nodes to display")
def map(nodes):
    """Display network topology map."""
    cli_instance = QNetCLI()
    cli_instance.create_network(nodes)
    cli_instance.show_network_map(nodes)


@cli.command()
def status():
    """Show network status."""
    cli_instance = QNetCLI()
    cli_instance.create_network(100)
    cli_instance.show_metrics()


@cli.command()
@click.argument("attack_type", type=click.Choice(["mitm", "eavesdrop", "dos", "compromise"]))
@click.option("--target", "-t", help="Target node ID")
def attack(attack_type, target):
    """Simulate network attack."""
    print_banner()
    cli_instance = QNetCLI()
    cli_instance.create_network(100)
    cli_instance.simulate_attack(attack_type, target)


@cli.command()
@click.option("--port", "-p", default=8000, help="API server port")
@click.option("--host", "-h", default="0.0.0.0", help="API server host")
def api(port, host):
    """Start QNet API server."""
    print_banner()
    
    if console:
        console.print(f"[cyan]Starting API server on {host}:{port}...[/cyan]")
        console.print("[yellow]Note: Run 'pip install qnet[dashboard]' for full dashboard support[/yellow]")
    else:
        print(f"Starting API server on {host}:{port}...")
    
    from qnet.api.rest import app
    import uvicorn
    uvicorn.run(app, host=host, port=port)


@cli.command()
def benchmark():
    """Run network performance benchmark."""
    print_banner()
    
    if console:
        console.print("[cyan]Running performance benchmarks...[/cyan]")
    else:
        print("Running performance benchmarks...")
    
    from qnet.core.simulation.engine import SimulationEngine, SimulationConfig
    from qnet.core.network.topology import TopologyType
    
    results = []
    
    for node_count in [100, 500, 1000, 5000]:
        config = SimulationConfig(
            node_count=node_count,
            topology_type=TopologyType.SCALE_FREE,
            seed=42,
        )
        
        engine = SimulationEngine(config)
        
        start = time.time()
        engine.initialize()
        elapsed = time.time() - start
        
        results.append({
            "nodes": node_count,
            "init_time": elapsed,
            "links": len(engine.topology.link_manager.links) if engine.topology else 0,
        })
        
        if console:
            console.print(f"[green]✓[/green] {node_count:5} nodes: {elapsed:.3f}s")
        else:
            print(f"[*] {node_count} nodes: {elapsed:.3f}s")
    
    if console:
        table = Table(title="Benchmark Results", box=box.DOUBLE_EDGE)
        table.add_column("Nodes", style="cyan")
        table.add_column("Init Time (s)", style="green")
        table.add_column("Links", style="yellow")
        
        for r in results:
            table.add_row(str(r["nodes"]), f"{r['init_time']:.3f}", str(r["links"]))
        
        console.print(table)


@cli.command()
def visualize():
    """Open visualization dashboard."""
    print_banner()
    
    if console:
        console.print("[cyan]Launching visualization dashboard...[/cyan]")
        console.print("[yellow]Make sure the API server is running: qnet api[/yellow]")
    else:
        print("Launching visualization dashboard...")
    
    import webbrowser
    webbrowser.open("http://localhost:3000")


@cli.command()
@click.argument("config_file", type=click.Path(exists=True), required=False)
def config(config_file):
    """Show or set configuration."""
    import yaml
    
    if config_file:
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        if console:
            console.print(Panel(
                f"[cyan]Configuration loaded from {config_file}[/cyan]\n"
                f"[yellow]Nodes:[/yellow] {config.get('simulation', {}).get('node_count', 100)}\n"
                f"[green]Topology:[/green] {config.get('network', {}).get('topology', 'scale_free')}",
                title="Config"
            ))
    else:
        default_config = """
simulation:
  node_count: 100
  duration: 60

network:
  topology: scale_free
  avg_connections: 4
  quantum_links_enabled: true
  quantum_link_ratio: 0.3

routing:
  algorithm: q_learning
  adaptive_routing: true

security:
  qkd_enabled: true
  qkd_protocol: bb84
  attack_simulation: false

ai:
  ai_enabled: true
  learning_rate: 0.1
  self_healing: true
"""
        if console:
            console.print(Panel(default_config, title="Default Configuration", border_style="blue"))
        else:
            print(default_config)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
