"""
CLI for the Swedish Energy Digital Twin.

Commands:
- twin init: Initialize the digital twin
- twin run <scenario>: Run a simulation scenario
- twin dashboard: Launch the Streamlit dashboard
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

app = typer.Typer(
    name="twin",
    help="🇸🇪 Swedish Energy Digital Twin CLI",
    add_completion=False,
)

console = Console()


@app.command()
def init():
    """Initialize the digital twin engine."""
    from src.twin.engine import get_twin_engine
    from src.orchestrator.agent import get_orchestrator
    
    with console.status("[bold green]Initializing Digital Twin..."):
        twin = get_twin_engine()
        state = twin.initialize()
        
        orchestrator = get_orchestrator()
        orchestrator.initialize()
    
    console.print(Panel.fit(
        f"[green]✓ Digital Twin Initialized[/green]\n\n"
        f"Zones: {len(state.zones)}\n"
        f"Connections: {len(state.connections)}\n"
        f"Total Production: {state.total_production_mw:,.0f} MW\n"
        f"Total Consumption: {state.total_consumption_mw:,.0f} MW",
        title="🇸🇪 Swedish Energy System",
    ))


@app.command()
def scenarios():
    """List available simulation scenarios."""
    from src.agents.energy_agents import EnergyMarketModel
    from src.simulation.scenarios import get_all_scenarios
    
    model = EnergyMarketModel()
    all_scenarios = get_all_scenarios(model)
    
    table = Table(title="Available Scenarios")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Severity", style="red")
    table.add_column("Duration", style="green")
    table.add_column("Scope", style="magenta")
    
    for name, scenario in all_scenarios.items():
        scope = "🌍 Global" if scenario.is_global else "🇸🇪 Sweden"
        severity_bar = "█" * int(scenario.severity * 10) + "░" * (10 - int(scenario.severity * 10))
        
        table.add_row(
            name,
            scenario.event_type.value,
            f"{severity_bar} {scenario.severity:.0%}",
            f"{scenario.duration_hours:.0f}h",
            scope,
        )
    
    console.print(table)


@app.command()
def run(scenario: str):
    """Run a simulation scenario and display domino effects."""
    from src.twin.engine import get_twin_engine
    from src.orchestrator.agent import get_orchestrator
    
    # Initialize
    twin = get_twin_engine()
    if not twin._initialized:
        twin.initialize()
    
    orchestrator = get_orchestrator()
    orchestrator.initialize()
    
    console.print(f"\n[bold yellow]💥 Running scenario: {scenario}[/bold yellow]\n")
    
    try:
        results = orchestrator.run_scenario_analysis(scenario)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    # Display results
    console.print(Panel.fit(
        f"[bold]{results['scenario']['name']}[/bold]\n"
        f"Type: {results['scenario']['type']}\n"
        f"Severity: {results['scenario']['severity']:.0%}\n"
        f"Duration: {results['scenario']['duration_hours']}h",
        title="Scenario",
    ))
    
    # Domino effects
    console.print(f"\n[bold cyan]🎯 Domino Effects ({results['domino_effects']['count']} total)[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Step")
    table.add_column("Source → Target")
    table.add_column("Effect")
    table.add_column("Magnitude")
    table.add_column("CPI Impact")
    
    for effect in results['domino_effects']['effects'][:15]:
        cpi = f"+{effect['cpi_impact_bps']:.0f} bps" if effect.get('cpi_impact_bps') else "-"
        table.add_row(
            str(effect['step']),
            f"{effect['source']} → {effect['target']}",
            effect['type'],
            f"{effect['magnitude']:.1f} {effect['unit']}",
            cpi,
        )
    
    console.print(table)
    
    # Total impact
    console.print(f"\n[bold green]💰 Total Cost Impact: €{results['domino_effects']['total_cost_eur']:,.0f}[/bold green]")
    
    # Insights
    if results['insights']:
        console.print("\n[bold yellow]💡 Economic Insights[/bold yellow]\n")
        for insight in results['insights']:
            severity_emoji = {"info": "ℹ️", "warning": "⚠️", "alert": "🚨", "critical": "🔴"}
            emoji = severity_emoji.get(insight['severity'], "ℹ️")
            console.print(f"{emoji} [bold]{insight['title']}[/bold]")
            console.print(f"   {insight['description'][:200]}...")
            if insight.get('cpi_impact_bps'):
                console.print(f"   [red]CPI Impact: +{insight['cpi_impact_bps']:.0f} basis points[/red]")
            console.print()


@app.command()
def dashboard():
    """Launch the Streamlit dashboard."""
    import subprocess
    import sys
    from pathlib import Path
    
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    
    console.print("[bold green]🚀 Launching Dashboard...[/bold green]")
    console.print(f"Open: [cyan]http://localhost:8501[/cyan]")
    
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)])


@app.command()
def compare(scenario_a: str, scenario_b: str = None):
    """Compare two scenarios or a scenario vs reality."""
    from src.twin.engine import get_twin_engine
    from src.orchestrator.agent import get_orchestrator
    
    twin = get_twin_engine()
    if not twin._initialized:
        twin.initialize()
    
    orchestrator = get_orchestrator()
    orchestrator.initialize()
    
    # Run first scenario
    console.print(f"[yellow]Running {scenario_a}...[/yellow]")
    results_a = orchestrator.run_scenario_analysis(scenario_a)
    
    if scenario_b:
        console.print(f"[yellow]Running {scenario_b}...[/yellow]")
        results_b = orchestrator.run_scenario_analysis(scenario_b)
        
        console.print(f"\n[bold]Comparing {scenario_a} vs {scenario_b}[/bold]\n")
    else:
        console.print(f"\n[bold]Comparing {scenario_a} vs Reality[/bold]\n")
    
    # Display comparison
    comparison = results_a['comparison']
    
    table = Table(title="Comparison Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Alignment Score", f"{comparison['alignment_score']:.0%}")
    table.add_row("Price Divergence", f"{comparison['price_divergence_pct']:.1f}%")
    table.add_row("Production Divergence", f"{comparison['production_divergence_pct']:.1f}%")
    table.add_row("Demand Divergence", f"{comparison['demand_divergence_pct']:.1f}%")
    
    console.print(table)
    console.print(f"\n[italic]{comparison['interpretation']}[/italic]")


if __name__ == "__main__":
    app()
