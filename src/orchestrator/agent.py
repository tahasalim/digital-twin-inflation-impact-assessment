"""
Orchestrator Agent - Compares simulated vs actual data and produces unified insights.

This is the "third agent" that:
1. Runs simulations based on potential events
2. Compares simulation predictions with actual incoming data
3. Identifies divergences and their implications
4. Produces orchestrated output for Riksbank economists
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from src.models.energy import (
    ZoneId,
    EnergySystemState,
    DominoEffect,
    SimulationEvent,
)
from src.twin.engine import DigitalTwinEngine, get_twin_engine
from src.agents.energy_agents import EnergyMarketModel
from src.simulation.scenarios import ScenarioBuilder, get_all_scenarios


class InsightSeverity(str, Enum):
    """Severity level of insights."""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


class InsightCategory(str, Enum):
    """Category of economic insight."""
    PRICE_ANOMALY = "price_anomaly"
    SUPPLY_RISK = "supply_risk"
    DEMAND_SHIFT = "demand_shift"
    CPI_PRESSURE = "cpi_pressure"
    GRID_STRESS = "grid_stress"
    DIVERGENCE = "divergence"  # Simulation vs reality mismatch


class EconomicInsight(BaseModel):
    """An insight produced by the orchestrator for Riksbank economists."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    category: InsightCategory
    severity: InsightSeverity
    
    title: str
    description: str
    
    # Affected areas
    affected_zones: list[ZoneId] = Field(default_factory=list)
    is_national: bool = False
    is_global: bool = False
    
    # Quantitative metrics
    metrics: dict[str, float] = Field(default_factory=dict)
    
    # CPI relevance
    estimated_cpi_impact_bps: Optional[float] = None
    cpi_transmission_lag_days: Optional[int] = None
    
    # Confidence
    confidence: float = Field(ge=0, le=1, default=0.5)
    
    # Source
    source_simulation: Optional[str] = None
    source_actual: bool = False
    
    # Recommendations
    recommendations: list[str] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    """Result of comparing simulation vs actual data."""
    
    timestamp: datetime
    simulation_name: str
    
    # Alignment score (1 = perfect match, 0 = complete divergence)
    alignment_score: float = Field(ge=0, le=1)
    
    # Zone-level divergences
    zone_divergences: dict[str, dict] = Field(default_factory=dict)
    
    # Key differences
    price_divergence_pct: float
    production_divergence_pct: float
    demand_divergence_pct: float
    
    # Interpretation
    interpretation: str
    
    # Whether reality is worse than simulation predicted
    reality_worse: bool = False


class OrchestratorAgent:
    """
    Orchestrator Agent for the Digital Twin.
    
    Runs parallel simulations, compares with reality, and produces
    unified insights for Riksbank economists.
    """
    
    def __init__(self, twin_engine: Optional[DigitalTwinEngine] = None):
        self.twin = twin_engine or get_twin_engine()
        self.active_simulations: dict[str, EnergyMarketModel] = {}
        self.insights: list[EconomicInsight] = []
        self.comparisons: list[ComparisonResult] = []
        
    def initialize(self):
        """Initialize the orchestrator with the digital twin."""
        if not self.twin._initialized:
            self.twin.initialize()
        logger.info("Orchestrator initialized")
        
    def run_parallel_simulations(self, scenario_names: Optional[list[str]] = None) -> dict[str, SimulationEvent]:
        """
        Run multiple simulation scenarios in parallel.
        
        If no scenario names provided, runs all available scenarios.
        """
        results = {}
        
        for name in (scenario_names or []):
            model = EnergyMarketModel(seed=42)
            builder = ScenarioBuilder(model)
            scenarios = get_all_scenarios(model)
            
            if name in scenarios:
                scenario = scenarios[name]
                builder.scenarios[scenario.event_id] = scenario
                completed = builder.run_scenario(scenario.event_id)
                results[name] = completed
                self.active_simulations[name] = model
                
        return results
    
    def compare_with_reality(self, simulation_name: str) -> ComparisonResult:
        """
        Compare a simulation's predictions with current reality.
        
        Returns divergence analysis.
        """
        reality = self.twin.get_reality()
        
        if simulation_name not in self.active_simulations:
            raise ValueError(f"Simulation {simulation_name} not found")
        
        sim_model = self.active_simulations[simulation_name]
        
        # Build comparison
        zone_divergences = {}
        total_price_div = 0
        total_prod_div = 0
        total_demand_div = 0
        
        for zone_id in ZoneId:
            real_zone = reality.zones[zone_id]
            
            # Get simulated producer outputs for this zone
            sim_production = sum(
                p.current_output_mw for p in sim_model.producers 
                if p.zone == zone_id
            )
            sim_demand = sum(
                c.current_demand_mw for c in sim_model.industrials 
                if c.zone == zone_id
            ) + sum(
                h.current_demand_mw for h in sim_model.households 
                if h.zone == zone_id
            )
            
            # Calculate divergences
            price_div = 0  # Would need price in sim model
            prod_div = abs(sim_production - real_zone.current_production_mw) / max(real_zone.current_production_mw, 1) * 100
            demand_div = abs(sim_demand - real_zone.current_consumption_mw) / max(real_zone.current_consumption_mw, 1) * 100
            
            zone_divergences[zone_id.value] = {
                "production_divergence_pct": prod_div,
                "demand_divergence_pct": demand_div,
                "simulated_production_mw": sim_production,
                "actual_production_mw": real_zone.current_production_mw,
                "simulated_demand_mw": sim_demand,
                "actual_demand_mw": real_zone.current_consumption_mw,
            }
            
            total_price_div += price_div
            total_prod_div += prod_div
            total_demand_div += demand_div
        
        avg_price_div = total_price_div / len(ZoneId)
        avg_prod_div = total_prod_div / len(ZoneId)
        avg_demand_div = total_demand_div / len(ZoneId)
        
        # Calculate alignment score
        alignment = 1 - (avg_price_div + avg_prod_div + avg_demand_div) / 300
        alignment = max(0, min(1, alignment))
        
        # Interpret
        if alignment > 0.8:
            interpretation = "Simulation closely matches reality - scenario may be unfolding as predicted"
        elif alignment > 0.5:
            interpretation = "Moderate divergence - some aspects of scenario visible but not fully materialized"
        else:
            interpretation = "Significant divergence - reality differs substantially from simulation"
        
        result = ComparisonResult(
            timestamp=datetime.utcnow(),
            simulation_name=simulation_name,
            alignment_score=alignment,
            zone_divergences=zone_divergences,
            price_divergence_pct=avg_price_div,
            production_divergence_pct=avg_prod_div,
            demand_divergence_pct=avg_demand_div,
            interpretation=interpretation,
            reality_worse=False,  # Would need more analysis
        )
        
        self.comparisons.append(result)
        return result
    
    def generate_insight(
        self,
        category: InsightCategory,
        title: str,
        description: str,
        severity: InsightSeverity = InsightSeverity.INFO,
        affected_zones: Optional[list[ZoneId]] = None,
        metrics: Optional[dict] = None,
        cpi_impact_bps: Optional[float] = None,
    ) -> EconomicInsight:
        """Generate an economic insight."""
        
        insight = EconomicInsight(
            category=category,
            severity=severity,
            title=title,
            description=description,
            affected_zones=affected_zones or [],
            is_national=len(affected_zones or []) == len(ZoneId),
            metrics=metrics or {},
            estimated_cpi_impact_bps=cpi_impact_bps,
        )
        
        self.insights.append(insight)
        logger.info(f"💡 Insight: [{severity.value}] {title}")
        
        return insight
    
    def analyze_domino_effects(self, scenario: SimulationEvent) -> list[EconomicInsight]:
        """
        Analyze domino effects from a scenario and generate insights.
        
        This is where we identify CPI-relevant cascades.
        """
        insights = []
        
        # Group effects by type
        price_effects = [e for e in scenario.domino_effects if "price" in e.effect_type.lower()]
        production_effects = [e for e in scenario.domino_effects if "production" in e.effect_type.lower()]
        cpi_effects = [e for e in scenario.domino_effects if e.cpi_impact_bps is not None]
        
        # Summarize CPI impact chain
        if cpi_effects:
            total_cpi_bps = sum(e.cpi_impact_bps or 0 for e in cpi_effects)
            
            insight = self.generate_insight(
                category=InsightCategory.CPI_PRESSURE,
                title=f"CPI Pressure from {scenario.name}",
                description=f"""
                Scenario '{scenario.name}' shows potential CPI impact through energy prices.
                
                Transmission chain:
                {chr(10).join(f'  {i+1}. {e.description}' for i, e in enumerate(cpi_effects[:5]))}
                
                Total estimated impact: {total_cpi_bps:.0f} basis points
                """,
                severity=InsightSeverity.ALERT if total_cpi_bps > 50 else InsightSeverity.WARNING,
                cpi_impact_bps=total_cpi_bps,
                metrics={
                    "total_effects": len(scenario.domino_effects),
                    "cpi_relevant_effects": len(cpi_effects),
                    "total_cost_eur": scenario.total_cost_impact_eur or 0,
                },
            )
            insights.append(insight)
        
        # Production impact
        if production_effects:
            total_production_loss = sum(
                e.magnitude for e in production_effects 
                if e.effect_type == "production_reduction"
            )
            if total_production_loss > 500:  # MW threshold
                insight = self.generate_insight(
                    category=InsightCategory.SUPPLY_RISK,
                    title=f"Supply Reduction Risk",
                    description=f"Total production reduction: {total_production_loss:.0f} MW",
                    severity=InsightSeverity.ALERT if total_production_loss > 2000 else InsightSeverity.WARNING,
                    metrics={"production_loss_mw": total_production_loss},
                )
                insights.append(insight)
        
        return insights
    
    def run_scenario_analysis(self, scenario_name: str) -> dict:
        """
        Complete analysis pipeline:
        1. Run simulation
        2. Compare with reality
        3. Generate insights
        4. Return unified output
        """
        # Run simulation
        model = EnergyMarketModel(seed=42)
        scenarios = get_all_scenarios(model)
        
        if scenario_name not in scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = scenarios[scenario_name]
        builder = ScenarioBuilder(model)
        builder.scenarios[scenario.event_id] = scenario
        completed = builder.run_scenario(scenario.event_id)
        self.active_simulations[scenario_name] = model
        
        # Compare with reality
        comparison = self.compare_with_reality(scenario_name)
        
        # Analyze domino effects
        insights = self.analyze_domino_effects(completed)
        
        # Build unified output
        return {
            "scenario": {
                "name": completed.name,
                "type": completed.event_type.value,
                "severity": completed.severity,
                "duration_hours": completed.duration_hours,
            },
            "domino_effects": {
                "count": len(completed.domino_effects),
                "total_cost_eur": completed.total_cost_impact_eur,
                "effects": [
                    {
                        "step": e.step,
                        "source": e.source,
                        "target": e.target,
                        "type": e.effect_type,
                        "magnitude": e.magnitude,
                        "unit": e.unit,
                        "description": e.description,
                        "cpi_impact_bps": e.cpi_impact_bps,
                    }
                    for e in completed.domino_effects
                ],
            },
            "comparison": {
                "alignment_score": comparison.alignment_score,
                "interpretation": comparison.interpretation,
                "zones": comparison.zone_divergences,
            },
            "insights": [
                {
                    "severity": i.severity.value,
                    "category": i.category.value,
                    "title": i.title,
                    "description": i.description.strip(),
                    "cpi_impact_bps": i.estimated_cpi_impact_bps,
                }
                for i in insights
            ],
        }
    
    def get_summary(self) -> dict:
        """Get summary of all orchestrator activity."""
        return {
            "active_simulations": list(self.active_simulations.keys()),
            "total_insights": len(self.insights),
            "total_comparisons": len(self.comparisons),
            "critical_insights": [
                i.title for i in self.insights 
                if i.severity == InsightSeverity.CRITICAL
            ],
            "alert_insights": [
                i.title for i in self.insights 
                if i.severity == InsightSeverity.ALERT
            ],
        }


# Global singleton
_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator
