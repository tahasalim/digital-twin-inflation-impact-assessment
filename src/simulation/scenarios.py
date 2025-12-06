"""
Simulation Scenarios - Pre-built shock scenarios for the energy digital twin.

Includes national (Swedish) and global events that cascade through the system.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from loguru import logger

from src.models.energy import (
    EventType,
    ZoneId,
    CountryCode,
    SimulationEvent,
    DominoEffect,
)
from src.agents.energy_agents import EnergyMarketModel


class ScenarioBuilder:
    """Builder for creating complex simulation scenarios."""
    
    def __init__(self, model: EnergyMarketModel):
        self.model = model
        self.scenarios: dict[str, SimulationEvent] = {}
        
    def create_scenario(
        self,
        name: str,
        event_type: EventType,
        severity: float,
        description: str = "",
        duration_hours: float = 24,
        target_zones: Optional[list[ZoneId]] = None,
        is_global: bool = False,
    ) -> SimulationEvent:
        """Create a new simulation scenario."""
        
        scenario = SimulationEvent(
            event_id=str(uuid4())[:8],
            event_type=event_type,
            name=name,
            description=description or f"{event_type.value} scenario",
            start_time=datetime.utcnow(),
            duration_hours=duration_hours,
            affected_zones=target_zones or list(ZoneId),
            is_global=is_global,
            severity=severity,
        )
        
        self.scenarios[scenario.event_id] = scenario
        return scenario
    
    def run_scenario(self, scenario_id: str) -> SimulationEvent:
        """Run a scenario and collect all domino effects."""
        
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        logger.info(f"🎬 Running scenario: {scenario.name}")
        
        # Inject shock and get domino effects
        effects = self.model.inject_shock(
            scenario.event_type,
            scenario.severity,
            scenario.affected_zones if scenario.affected_zones else None,
        )
        
        scenario.domino_effects = effects
        
        # Run simulation forward
        results = self.model.run_simulation(steps=int(scenario.duration_hours))
        
        # Calculate totals
        scenario.total_cost_impact_eur = sum(
            e.cost_impact_eur or 0 for e in effects
        )
        
        if effects:
            price_effects = [e for e in effects if "price" in e.effect_type]
            if price_effects:
                scenario.peak_price_impact_pct = max(
                    e.magnitude for e in price_effects
                ) / 50 * 100  # Relative to 50 EUR/MWh baseline
        
        logger.success(f"Scenario complete: {len(effects)} effects, {scenario.total_cost_impact_eur:.0f} EUR total impact")
        
        return scenario


# ============================================================================
# PRE-BUILT SCENARIOS: Swedish National Events
# ============================================================================

class SwedishScenarios:
    """Pre-built scenarios for Swedish national events."""
    
    @staticmethod
    def nordic_drought(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Severe drought affecting Nordic hydro production.
        
        Impact: SE1, SE2 hydro production drops 40-60%
        Duration: 2-3 months (simulated as 72 hours)
        """
        return builder.create_scenario(
            name="Nordic Drought 2024",
            event_type=EventType.DROUGHT,
            severity=0.5,
            description="""
            Severe drought conditions across Scandinavia reduce reservoir levels.
            - Hydro production in SE1/SE2 drops 50%
            - Prices spike in all zones
            - Increased imports from continental Europe
            - Industrial load shedding possible
            """,
            duration_hours=72,
            target_zones=[ZoneId.SE1, ZoneId.SE2],
        )
    
    @staticmethod
    def nuclear_outage(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Unplanned nuclear reactor outage in SE3.
        
        Impact: 1-2 GW immediate capacity loss
        Duration: 2-4 weeks
        """
        return builder.create_scenario(
            name="Forsmark Reactor Trip",
            event_type=EventType.NUCLEAR_OUTAGE,
            severity=0.4,
            description="""
            Unplanned shutdown at Forsmark nuclear plant.
            - 1.4 GW capacity offline
            - SE3 prices surge
            - North-South flows reverse
            - Reserve margins tight
            """,
            duration_hours=168,  # 1 week
            target_zones=[ZoneId.SE3],
        )
    
    @staticmethod
    def winter_cold_wave(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Extreme cold wave hitting Sweden.
        
        Impact: Heating demand surges 40-60%
        Duration: 1-2 weeks
        """
        return builder.create_scenario(
            name="Arctic Cold Wave",
            event_type=EventType.COLD_WAVE,
            severity=0.7,
            description="""
            Temperatures drop to -30°C across Sweden.
            - Residential heating demand +50%
            - All zones affected
            - Gas peakers run at max
            - Import cables at capacity
            """,
            duration_hours=168,
            target_zones=None,  # All zones
        )
    
    @staticmethod
    def baltic_cable_failure(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Damage to NordBalt or SwePol cables.
        
        Impact: 600-700 MW import capacity lost
        Duration: Weeks to months
        """
        return builder.create_scenario(
            name="Baltic Cable Sabotage",
            event_type=EventType.CABLE_FAILURE,
            severity=0.8,
            description="""
            Suspected sabotage of undersea cables in Baltic Sea.
            - NordBalt (SE4-LT) offline
            - SwePol (SE4-PL) damaged
            - SE4 isolated from Eastern Europe
            - Security concerns
            """,
            duration_hours=336,  # 2 weeks
            target_zones=[ZoneId.SE4],
        )
    
    @staticmethod
    def wind_lull(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Extended period of low wind across Scandinavia.
        
        Impact: Wind production drops 80%
        Duration: 3-7 days
        """
        return builder.create_scenario(
            name="Scandinavian Wind Lull",
            event_type=EventType.WIND_CALM,
            severity=0.8,
            description="""
            High pressure system causes wind drought.
            - Wind production at 10% of capacity
            - All zones affected
            - Gas and imports fill gap
            - Prices elevated
            """,
            duration_hours=120,  # 5 days
            target_zones=None,
        )


# ============================================================================
# PRE-BUILT SCENARIOS: Global Events
# ============================================================================

class GlobalScenarios:
    """Pre-built scenarios for global events affecting Sweden."""
    
    @staticmethod
    def european_gas_crisis(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Major disruption to European gas supply.
        
        Impact: Gas prices triple, ripple through electricity markets
        Duration: Months
        """
        return builder.create_scenario(
            name="European Gas Supply Crisis",
            event_type=EventType.GAS_PRICE_SPIKE,
            severity=0.9,
            description="""
            Russian gas flows cut, LNG terminals at capacity.
            - TTF gas price triples
            - Electricity prices surge across Europe
            - Sweden imports expensive German power
            - Industrial demand destruction
            - CPI impact: +0.5-1.0%
            """,
            duration_hours=720,  # 30 days
            is_global=True,
        )
    
    @staticmethod
    def continental_heatwave(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Record heatwave across Europe.
        
        Impact: Nuclear cooling issues, hydro depletion, demand surge
        Duration: 2-3 weeks
        """
        return builder.create_scenario(
            name="European Mega-Heatwave",
            event_type=EventType.HEAT_WAVE,
            severity=0.6,
            description="""
            Record temperatures across Europe (45°C+ in south).
            - French nuclear output cut 30% (river cooling)
            - Alpine/Scandinavian hydro stressed
            - Cross-border flows reduced
            - Cooling demand surge
            - Grid stability concerns
            """,
            duration_hours=336,
            is_global=True,
        )
    
    @staticmethod
    def trade_war_rare_earths(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Trade restrictions on rare earth metals.
        
        Impact: Wind turbine/solar panel supply chain disruption
        Duration: Long-term
        """
        return builder.create_scenario(
            name="Rare Earth Trade War",
            event_type=EventType.TRADE_RESTRICTION,
            severity=0.5,
            description="""
            China restricts rare earth exports.
            - Wind turbine production slowed
            - Solar panel costs increase
            - Battery storage delayed
            - Renewable expansion stalled
            - Long-term capacity concerns
            """,
            duration_hours=2160,  # 90 days
            is_global=True,
        )
    
    @staticmethod
    def oil_price_shock(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Major oil price spike (war, OPEC action).
        
        Impact: Ripple through entire energy complex
        Duration: Varies
        """
        return builder.create_scenario(
            name="Oil Price Shock",
            event_type=EventType.OIL_CRISIS,
            severity=0.7,
            description="""
            Middle East conflict disrupts oil supply.
            - Brent crude doubles
            - Gas prices follow
            - Transport costs surge
            - Electricity prices up 30-50%
            - CPI impact: +1-2%
            """,
            duration_hours=720,
            is_global=True,
        )
    
    @staticmethod
    def carbon_price_surge(builder: ScenarioBuilder) -> SimulationEvent:
        """
        Rapid increase in EU carbon prices.
        
        Impact: Fossil generation costs spike
        Duration: Permanent
        """
        return builder.create_scenario(
            name="Carbon Price Surge",
            event_type=EventType.CARBON_TAX_INCREASE,
            severity=0.4,
            description="""
            EU ETS carbon price jumps from €80 to €150/ton.
            - Coal generation uneconomic
            - Gas generation costs +€30/MWh
            - Clean power premium rises
            - Industrial relocation pressure
            """,
            duration_hours=8760,  # 1 year
            is_global=True,
        )


def get_all_scenarios(model: EnergyMarketModel) -> dict[str, SimulationEvent]:
    """Get all available pre-built scenarios."""
    
    builder = ScenarioBuilder(model)
    scenarios = {}
    
    # Swedish scenarios
    for name, method in [
        ("nordic_drought", SwedishScenarios.nordic_drought),
        ("nuclear_outage", SwedishScenarios.nuclear_outage),
        ("winter_cold_wave", SwedishScenarios.winter_cold_wave),
        ("baltic_cable_failure", SwedishScenarios.baltic_cable_failure),
        ("wind_lull", SwedishScenarios.wind_lull),
    ]:
        scenario = method(builder)
        scenarios[name] = scenario
    
    # Global scenarios
    for name, method in [
        ("european_gas_crisis", GlobalScenarios.european_gas_crisis),
        ("continental_heatwave", GlobalScenarios.continental_heatwave),
        ("trade_war_rare_earths", GlobalScenarios.trade_war_rare_earths),
        ("oil_price_shock", GlobalScenarios.oil_price_shock),
        ("carbon_price_surge", GlobalScenarios.carbon_price_surge),
    ]:
        scenario = method(builder)
        scenarios[name] = scenario
    
    return scenarios
