"""
Unified Scenario Orchestrator for Swedish Energy Digital Twin.

Coordinates all subsystems on load:
- Timeline simulation
- Multi-agent analysis
- System overview

Aggregates results into a unified summary for Riksbanken economists.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Debug mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")


# =============================================================================
# DATA MODELS
# =============================================================================

class SystemStatus(str, Enum):
    """Status of a subsystem."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SubsystemResult(BaseModel):
    """Result from a single subsystem."""
    name: str
    status: SystemStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Key metrics
    primary_metric: str = ""
    primary_value: float = 0.0
    secondary_metrics: dict[str, float] = Field(default_factory=dict)
    
    # Risk assessment
    risk_level: Severity = Severity.LOW
    risk_factors: list[str] = Field(default_factory=list)
    
    # Findings
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    
    # Raw data for detailed views
    raw_data: dict = Field(default_factory=dict)
    
    error_message: Optional[str] = None


class UnifiedScenarioResult(BaseModel):
    """Unified result aggregating all subsystems."""
    scenario_name: str
    trigger_event: str
    trigger_magnitude: float = 1.0
    duration_hours: int = 24
    
    # Timing
    orchestration_start: datetime
    orchestration_end: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    
    # Subsystem results
    timeline_result: Optional[SubsystemResult] = None
    multiagent_result: Optional[SubsystemResult] = None
    system_result: Optional[SubsystemResult] = None
    
    # Aggregated metrics
    overall_risk_level: Severity = Severity.LOW
    total_cpi_impact_bps: float = 0.0
    price_change_percent: float = 0.0
    supply_demand_balance_mw: float = 0.0
    
    # Synthesis
    executive_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    critical_breakpoints: list[dict] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    
    # Status
    is_complete: bool = False
    is_debug_mode: bool = False
    errors: list[str] = Field(default_factory=list)


class ScenarioConfig(BaseModel):
    """Configuration for a scenario run."""
    name: str
    trigger_event: str
    trigger_magnitude: float = 1.0
    duration_hours: int = 24
    
    # Run flags
    run_timeline: bool = True
    run_multiagent: bool = True
    run_system: bool = True
    
    # Display
    icon: str = "⚡"
    description: str = ""


# =============================================================================
# PREDEFINED SCENARIOS
# =============================================================================

SCENARIOS: dict[str, ScenarioConfig] = {
    "nordic_drought": ScenarioConfig(
        name="Nordic Drought Scenario",
        trigger_event="nordic_drought",
        trigger_magnitude=0.8,
        duration_hours=48,
        icon="🏜️",
        description="Extended drought affecting Nordic hydro reservoirs"
    ),
    "extreme_cold": ScenarioConfig(
        name="Extreme Cold Wave",
        trigger_event="extreme_cold",
        trigger_magnitude=0.9,
        duration_hours=72,
        icon="❄️",
        description="Severe cold wave increasing heating demand"
    ),
    "nuclear_outage": ScenarioConfig(
        name="Nuclear Reactor Outage",
        trigger_event="nuclear_shutdown",
        trigger_magnitude=0.7,
        duration_hours=24,
        icon="☢️",
        description="Unplanned nuclear reactor shutdown"
    ),
    "energy_crisis": ScenarioConfig(
        name="European Energy Crisis",
        trigger_event="energy_crisis",
        trigger_magnitude=1.0,
        duration_hours=96,
        icon="🔥",
        description="Cascading European energy supply disruption"
    ),
    "grid_failure": ScenarioConfig(
        name="Interconnection Failure",
        trigger_event="grid_failure",
        trigger_magnitude=0.6,
        duration_hours=12,
        icon="🔌",
        description="Major interconnection cable failure"
    ),
}


# =============================================================================
# UNIFIED ORCHESTRATOR
# =============================================================================

class UnifiedOrchestrator:
    """
    Orchestrates all subsystems for unified scenario analysis.
    
    On load:
    1. Triggers timeline simulation
    2. Runs multi-agent analysis  
    3. Gathers system overview
    4. Aggregates into unified summary
    """
    
    _instance: Optional['UnifiedOrchestrator'] = None
    
    def __init__(self):
        self.initialized = False
        self.current_result: Optional[UnifiedScenarioResult] = None
        self.is_running = False
        
        # Subsystem references (lazy loaded)
        self._timeline_simulator = None
        self._multiagent_system = None
        self._twin_engine = None
    
    @classmethod
    def get_instance(cls) -> 'UnifiedOrchestrator':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize(self) -> None:
        """Initialize the orchestrator and all subsystems."""
        if self.initialized:
            return
        
        logger.info("🎯 Initializing Unified Orchestrator...")
        
        try:
            # Import and initialize subsystems
            from src.twin.engine import get_twin_engine
            from src.agents.streamlined_agents import get_streamlined_system
            from src.simulation.timeline import TimelineSimulator
            from src.agents.energy_agents import EnergyMarketModel
            
            self._twin_engine = get_twin_engine()
            self._twin_engine.initialize()
            
            self._multiagent_system = get_streamlined_system()
            self._multiagent_system.initialize()
            
            self._timeline_simulator = TimelineSimulator
            
            self.initialized = True
            logger.success("✅ Unified Orchestrator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def run_scenario(
        self,
        scenario_id: str = "nordic_drought",
        custom_config: Optional[ScenarioConfig] = None
    ) -> UnifiedScenarioResult:
        """
        Run a complete scenario analysis across all subsystems.
        
        Args:
            scenario_id: ID of predefined scenario
            custom_config: Optional custom configuration
        """
        if not self.initialized:
            self.initialize()
        
        if self.is_running:
            logger.warning("Scenario already running, waiting...")
            while self.is_running:
                await asyncio.sleep(0.1)
        
        self.is_running = True
        config = custom_config or SCENARIOS.get(scenario_id, SCENARIOS["nordic_drought"])
        
        logger.info(f"🚀 Starting unified scenario: {config.name}")
        logger.info(f"   Trigger: {config.trigger_event} | Magnitude: {config.trigger_magnitude}")
        logger.info(f"   Duration: {config.duration_hours}h | Debug: {DEBUG_MODE}")
        
        start_time = datetime.utcnow()
        
        self.current_result = UnifiedScenarioResult(
            scenario_name=config.name,
            trigger_event=config.trigger_event,
            trigger_magnitude=config.trigger_magnitude,
            duration_hours=config.duration_hours,
            orchestration_start=start_time,
            is_debug_mode=DEBUG_MODE
        )
        
        try:
            # Run subsystems (can be parallelized in future)
            if config.run_timeline:
                self.current_result.timeline_result = await self._run_timeline(config)
            
            if config.run_multiagent:
                self.current_result.multiagent_result = await self._run_multiagent(config)
            
            if config.run_system:
                self.current_result.system_result = await self._run_system_overview(config)
            
            # Aggregate results
            self._aggregate_results()
            
            self.current_result.orchestration_end = datetime.utcnow()
            self.current_result.total_duration_seconds = (
                self.current_result.orchestration_end - start_time
            ).total_seconds()
            self.current_result.is_complete = True
            
            logger.success(f"✅ Unified scenario complete in {self.current_result.total_duration_seconds:.1f}s")
            
        except Exception as e:
            logger.error(f"Scenario failed: {e}")
            self.current_result.errors.append(str(e))
            
        finally:
            self.is_running = False
        
        return self.current_result
    
    async def _run_timeline(self, config: ScenarioConfig) -> SubsystemResult:
        """Run timeline simulation subsystem."""
        result = SubsystemResult(
            name="Timeline Simulation",
            status=SystemStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        
        try:
            from src.simulation.timeline import TimelineSimulator
            from src.agents.energy_agents import EnergyMarketModel
            
            # Create model and simulator
            model = EnergyMarketModel()
            simulator = TimelineSimulator(model)
            
            # Map trigger to event
            event_mapping = {
                "nordic_drought": "nordic_drought",
                "extreme_cold": "cold_snap",
                "nuclear_shutdown": "nuclear_outage",
                "energy_crisis": "gas_crisis",
                "grid_failure": "interconnector_failure",
            }
            event_type = event_mapping.get(config.trigger_event, "nordic_drought")
            
            # Run simulation
            summary = simulator.run_simulation(
                duration_hours=min(config.duration_hours, 72),  # Cap at 72h
                events=[{"type": event_type, "hour": 6, "magnitude": config.trigger_magnitude}],
                name=config.name
            )
            
            # Extract key metrics
            result.primary_metric = "avg_price_eur_mwh"
            result.primary_value = summary.metrics.get("avg_price", 50.0)
            result.secondary_metrics = {
                "max_price": summary.metrics.get("max_price", 100.0),
                "min_price": summary.metrics.get("min_price", 20.0),
                "total_production_mwh": summary.metrics.get("total_production", 0),
                "checkpoints": len(summary.checkpoints)
            }
            
            # Risk assessment from timeline
            price_spike = summary.metrics.get("max_price", 50) / 50.0
            if price_spike > 3:
                result.risk_level = Severity.CRITICAL
            elif price_spike > 2:
                result.risk_level = Severity.HIGH
            elif price_spike > 1.5:
                result.risk_level = Severity.MEDIUM
            
            # Key findings from key moments
            for moment in summary.key_moments[:3]:
                result.key_findings.append(f"Hour {moment.hour}: {moment.title}")
            
            # Store raw data
            result.raw_data = {
                "checkpoints": len(summary.checkpoints),
                "key_moments": [m.model_dump() for m in summary.key_moments[:5]],
                "metrics": summary.metrics
            }
            
            result.status = SystemStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Timeline simulation failed: {e}")
            result.status = SystemStatus.ERROR
            result.error_message = str(e)
        
        result.end_time = datetime.utcnow()
        result.duration_seconds = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def _run_multiagent(self, config: ScenarioConfig) -> SubsystemResult:
        """Run multi-agent analysis subsystem."""
        result = SubsystemResult(
            name="Multi-Agent Analysis",
            status=SystemStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        
        try:
            ma_result = await self._multiagent_system.run_scenario(
                scenario_name=config.name,
                trigger_event=config.trigger_event,
                duration_hours=config.duration_hours,
                trigger_magnitude=config.trigger_magnitude
            )
            
            # Extract key metrics
            result.primary_metric = "cpi_impact_bps"
            result.primary_value = ma_result.total_cpi_impact_bps
            result.secondary_metrics = {
                "total_agents": ma_result.total_agents,
                "api_calls": ma_result.api_calls_made,
                "breakpoints": len(ma_result.breakpoints),
                "outputs": len(ma_result.all_outputs)
            }
            
            # Risk level
            result.risk_level = Severity(ma_result.overall_risk_level.value)
            result.risk_factors = [
                f"{bp.title} ({bp.severity.value})"
                for bp in ma_result.breakpoints[:5]
            ]
            
            # Key findings
            result.key_findings = ma_result.key_findings.copy()
            
            # Warnings from critical breakpoints
            for bp in ma_result.breakpoints:
                if bp.severity.value in ["critical", "high"]:
                    result.warnings.append(bp.description)
            
            # Store raw data
            result.raw_data = {
                "executive_summary": ma_result.executive_summary,
                "recommendations": ma_result.recommendations,
                "breakpoints": [bp.model_dump() for bp in ma_result.breakpoints[:10]],
                "domain_summaries": {
                    "supply": ma_result.supply_summary.model_dump() if ma_result.supply_summary else None,
                    "demand": ma_result.demand_summary.model_dump() if ma_result.demand_summary else None,
                    "external": ma_result.external_summary.model_dump() if ma_result.external_summary else None,
                }
            }
            
            result.status = SystemStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Multi-agent analysis failed: {e}")
            result.status = SystemStatus.ERROR
            result.error_message = str(e)
        
        result.end_time = datetime.utcnow()
        result.duration_seconds = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def _run_system_overview(self, config: ScenarioConfig) -> SubsystemResult:
        """Run system overview subsystem."""
        result = SubsystemResult(
            name="System Overview",
            status=SystemStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        
        try:
            reality = self._twin_engine.get_reality()
            
            # Calculate current system state
            total_production = sum(z.current_production_mw for z in reality.zones.values())
            total_consumption = sum(z.current_consumption_mw for z in reality.zones.values())
            avg_price = sum(z.spot_price_eur_mwh for z in reality.zones.values()) / 4
            
            result.primary_metric = "supply_demand_balance_mw"
            result.primary_value = total_production - total_consumption
            result.secondary_metrics = {
                "total_production_mw": total_production,
                "total_consumption_mw": total_consumption,
                "avg_price_eur_mwh": avg_price,
                "zone_count": len(reality.zones)
            }
            
            # Risk assessment
            balance_ratio = total_production / max(total_consumption, 1)
            if balance_ratio < 0.9:
                result.risk_level = Severity.CRITICAL
                result.risk_factors.append("Supply deficit detected")
            elif balance_ratio < 0.95:
                result.risk_level = Severity.HIGH
                result.risk_factors.append("Tight supply margin")
            elif balance_ratio > 1.2:
                result.risk_level = Severity.MEDIUM
                result.risk_factors.append("Excess supply - export opportunities")
            
            # Zone-specific findings
            for zone_id, zone in reality.zones.items():
                if zone.spot_price_eur_mwh > 80:
                    result.key_findings.append(f"{zone_id.value}: High price €{zone.spot_price_eur_mwh:.0f}/MWh")
            
            # Store zone data
            result.raw_data = {
                "zones": {
                    zone_id.value: {
                        "production_mw": zone.current_production_mw,
                        "consumption_mw": zone.current_consumption_mw,
                        "price_eur_mwh": zone.spot_price_eur_mwh,
                        "balance_mw": zone.current_production_mw - zone.current_consumption_mw
                    }
                    for zone_id, zone in reality.zones.items()
                }
            }
            
            result.status = SystemStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"System overview failed: {e}")
            result.status = SystemStatus.ERROR
            result.error_message = str(e)
        
        result.end_time = datetime.utcnow()
        result.duration_seconds = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    def _aggregate_results(self) -> None:
        """Aggregate results from all subsystems into unified summary."""
        result = self.current_result
        if not result:
            return
        
        # Collect all risk levels
        risk_levels = []
        all_findings = []
        all_warnings = []
        all_recommendations = []
        
        # Process timeline result
        if result.timeline_result and result.timeline_result.status == SystemStatus.COMPLETED:
            risk_levels.append(result.timeline_result.risk_level)
            all_findings.extend(result.timeline_result.key_findings)
            result.price_change_percent = (
                (result.timeline_result.primary_value - 50) / 50 * 100
            )
        
        # Process multi-agent result
        if result.multiagent_result and result.multiagent_result.status == SystemStatus.COMPLETED:
            risk_levels.append(result.multiagent_result.risk_level)
            all_findings.extend(result.multiagent_result.key_findings)
            all_warnings.extend(result.multiagent_result.warnings[:5])
            result.total_cpi_impact_bps = result.multiagent_result.primary_value
            
            # Get recommendations from raw data
            if "recommendations" in result.multiagent_result.raw_data:
                all_recommendations.extend(result.multiagent_result.raw_data["recommendations"])
            
            # Get breakpoints
            if "breakpoints" in result.multiagent_result.raw_data:
                result.critical_breakpoints = result.multiagent_result.raw_data["breakpoints"][:5]
        
        # Process system result
        if result.system_result and result.system_result.status == SystemStatus.COMPLETED:
            risk_levels.append(result.system_result.risk_level)
            all_findings.extend(result.system_result.key_findings)
            result.supply_demand_balance_mw = result.system_result.primary_value
        
        # Determine overall risk level
        if risk_levels:
            result.overall_risk_level = max(
                risk_levels, 
                key=lambda x: list(Severity).index(x)
            )
        
        # Deduplicate and limit findings
        result.key_findings = list(dict.fromkeys(all_findings))[:10]
        result.recommendations = list(dict.fromkeys(all_recommendations))[:5]
        
        # Generate executive summary
        result.executive_summary = self._generate_executive_summary(result)
    
    def _generate_executive_summary(self, result: UnifiedScenarioResult) -> str:
        """Generate executive summary for Riksbanken economist."""
        risk_desc = {
            Severity.LOW: "within normal parameters",
            Severity.MEDIUM: "requires monitoring",
            Severity.HIGH: "demands attention",
            Severity.CRITICAL: "requires immediate action"
        }
        
        subsystem_status = []
        if result.timeline_result:
            subsystem_status.append(f"Timeline: {result.timeline_result.status.value}")
        if result.multiagent_result:
            subsystem_status.append(f"Multi-Agent: {result.multiagent_result.status.value}")
        if result.system_result:
            subsystem_status.append(f"System: {result.system_result.status.value}")
        
        return (
            f"## Scenario Analysis: {result.scenario_name}\n\n"
            f"**Trigger:** {result.trigger_event} (magnitude: {result.trigger_magnitude})\n\n"
            f"**Duration:** {result.duration_hours} hours\n\n"
            f"**Overall Assessment:** Risk level is **{result.overall_risk_level.value}** - "
            f"{risk_desc[result.overall_risk_level]}.\n\n"
            f"**Key Metrics:**\n"
            f"- Estimated CPI Impact: {result.total_cpi_impact_bps:.1f} basis points\n"
            f"- Price Change: {result.price_change_percent:+.1f}%\n"
            f"- Supply-Demand Balance: {result.supply_demand_balance_mw:+.0f} MW\n\n"
            f"**Subsystem Status:** {', '.join(subsystem_status)}\n\n"
            f"*Analysis completed in {result.total_duration_seconds:.1f} seconds.*"
        )
    
    def get_available_scenarios(self) -> dict[str, ScenarioConfig]:
        """Get all available predefined scenarios."""
        return SCENARIOS.copy()
    
    def get_current_result(self) -> Optional[UnifiedScenarioResult]:
        """Get the most recent result."""
        return self.current_result
    
    def get_status(self) -> dict:
        """Get orchestrator status."""
        return {
            "initialized": self.initialized,
            "is_running": self.is_running,
            "has_result": self.current_result is not None,
            "debug_mode": DEBUG_MODE,
            "available_scenarios": list(SCENARIOS.keys())
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_unified_orchestrator() -> UnifiedOrchestrator:
    """Get the unified orchestrator singleton."""
    return UnifiedOrchestrator.get_instance()


async def run_unified_scenario(scenario_id: str = "nordic_drought") -> UnifiedScenarioResult:
    """Convenience function to run a unified scenario."""
    orchestrator = get_unified_orchestrator()
    return await orchestrator.run_scenario(scenario_id)


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("UNIFIED ORCHESTRATOR TEST")
        print("=" * 60)
        
        orchestrator = get_unified_orchestrator()
        orchestrator.initialize()
        
        print(f"\nStatus: {orchestrator.get_status()}")
        print(f"Available scenarios: {list(orchestrator.get_available_scenarios().keys())}")
        
        # Run scenario
        result = await orchestrator.run_scenario("nordic_drought")
        
        print(f"\n{'='*60}")
        print("UNIFIED RESULTS")
        print(f"{'='*60}")
        print(f"Scenario: {result.scenario_name}")
        print(f"Duration: {result.total_duration_seconds:.1f}s")
        print(f"Risk Level: {result.overall_risk_level.value}")
        print(f"CPI Impact: {result.total_cpi_impact_bps:.2f} bps")
        
        print(f"\n{result.executive_summary}")
        
        print(f"\nKey Findings ({len(result.key_findings)}):")
        for finding in result.key_findings[:5]:
            print(f"  • {finding}")
        
        print(f"\nRecommendations ({len(result.recommendations)}):")
        for rec in result.recommendations:
            print(f"  → {rec}")
    
    asyncio.run(test())
