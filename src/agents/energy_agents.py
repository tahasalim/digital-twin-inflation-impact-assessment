"""
Agent-Based Simulation Layer using Mesa 3.x.

Economic agents that react to shocks and propagate domino effects:
- EnergyProducerAgent: Hydro, Nuclear, Wind producers
- IndustrialConsumerAgent: Factories, data centers
- HouseholdAgent: Residential consumers
- RetailerAgent: Energy retailers setting consumer prices
- GridOperatorAgent: Svenska kraftnät managing the grid
"""

from enum import Enum
from typing import Optional
import random

from mesa import Agent, Model
from mesa.datacollection import DataCollector
from loguru import logger

from src.models.energy import (
    ZoneId,
    EnergySourceType,
    ConsumerType,
    EventType,
    DominoEffect,
)


class AgentState(str, Enum):
    """Agent operational state."""
    NORMAL = "normal"
    STRESSED = "stressed"
    CRITICAL = "critical"
    OFFLINE = "offline"


class BaseEnergyAgent(Agent):
    """Base class for all energy sector agents."""
    
    def __init__(self, unique_id: str, model: "EnergyMarketModel", zone: ZoneId):
        super().__init__(model)
        self.unique_id = unique_id
        self.zone = zone
        self.state = AgentState.NORMAL
        self.domino_effects: list[DominoEffect] = []
        
    def receive_shock(self, shock_type: EventType, severity: float) -> list[DominoEffect]:
        """
        Receive and process a shock.
        
        Returns list of domino effects to propagate.
        """
        raise NotImplementedError
    
    def propagate_effect(self, effect: DominoEffect) -> list[DominoEffect]:
        """
        Receive a domino effect from another agent.
        
        Returns list of secondary effects to propagate.
        """
        raise NotImplementedError


class EnergyProducerAgent(BaseEnergyAgent):
    """
    Energy producer agent (power plants).
    
    Reacts to:
    - Resource availability (drought → hydro, wind calm → wind)
    - Fuel prices (gas price spike → gas plants)
    - Demand signals from grid operator
    """
    
    def __init__(
        self,
        unique_id: str,
        model: "EnergyMarketModel",
        zone: ZoneId,
        source_type: EnergySourceType,
        capacity_mw: float,
        marginal_cost: float,
    ):
        super().__init__(unique_id, model, zone)
        self.source_type = source_type
        self.capacity_mw = capacity_mw
        self.current_output_mw = capacity_mw * 0.7  # 70% baseline
        self.marginal_cost = marginal_cost  # EUR/MWh
        self.base_marginal_cost = marginal_cost
        
        # Sensitivity factors
        self.sensitivities = {
            EventType.DROUGHT: 0.9 if source_type == EnergySourceType.HYDRO else 0.0,
            EventType.WIND_CALM: 0.95 if source_type == EnergySourceType.WIND else 0.0,
            EventType.NUCLEAR_OUTAGE: 0.8 if source_type == EnergySourceType.NUCLEAR else 0.0,
            EventType.GAS_PRICE_SPIKE: 0.7 if source_type == EnergySourceType.GAS else 0.1,
        }
    
    def receive_shock(self, shock_type: EventType, severity: float) -> list[DominoEffect]:
        effects = []
        sensitivity = self.sensitivities.get(shock_type, 0.0)
        
        if sensitivity == 0:
            return effects
        
        impact = sensitivity * severity
        
        # Production reduction
        old_output = self.current_output_mw
        self.current_output_mw = max(0, self.current_output_mw * (1 - impact))
        production_loss = old_output - self.current_output_mw
        
        # Cost increase (scarcity)
        if production_loss > 0:
            cost_multiplier = 1 + (impact * 2)  # Up to 3x cost
            self.marginal_cost = self.base_marginal_cost * cost_multiplier
        
        # Update state
        if impact > 0.7:
            self.state = AgentState.CRITICAL
        elif impact > 0.3:
            self.state = AgentState.STRESSED
        
        # Create domino effect
        if production_loss > 0:
            effect = DominoEffect(
                step=1,
                source=self.unique_id,
                target=f"zone_{self.zone.value}",
                effect_type="production_reduction",
                magnitude=production_loss,
                unit="MW",
                description=f"{self.source_type.value} producer {self.unique_id} reduced output by {production_loss:.0f} MW due to {shock_type.value}",
                delay_hours=0.5,
                cost_impact_eur=production_loss * self.marginal_cost,
            )
            effects.append(effect)
            self.domino_effects.append(effect)
            logger.info(f"⚡ {self.unique_id}: Production ↓{production_loss:.0f}MW, Cost ↑{self.marginal_cost:.1f} EUR/MWh")
        
        return effects
    
    def propagate_effect(self, effect: DominoEffect) -> list[DominoEffect]:
        # Producers respond to grid price signals
        if effect.effect_type == "price_increase" and effect.target == f"zone_{self.zone.value}":
            # Increase output if profitable
            price_increase = effect.magnitude
            if self.marginal_cost < price_increase:
                additional_output = min(
                    self.capacity_mw - self.current_output_mw,
                    self.capacity_mw * 0.2
                )
                if additional_output > 0:
                    self.current_output_mw += additional_output
                    return [DominoEffect(
                        step=effect.step + 1,
                        source=self.unique_id,
                        target=f"zone_{self.zone.value}",
                        effect_type="production_increase",
                        magnitude=additional_output,
                        unit="MW",
                        description=f"Producer {self.unique_id} increased output by {additional_output:.0f} MW in response to price signal",
                        delay_hours=effect.delay_hours + 1,
                    )]
        return []
    
    def step(self):
        """Mesa step function - called each simulation tick."""
        # Natural recovery towards baseline
        if self.state != AgentState.NORMAL:
            recovery_rate = 0.05
            baseline_output = self.capacity_mw * 0.7
            self.current_output_mw += (baseline_output - self.current_output_mw) * recovery_rate
            self.marginal_cost += (self.base_marginal_cost - self.marginal_cost) * recovery_rate


class IndustrialConsumerAgent(BaseEnergyAgent):
    """
    Industrial consumer agent (factories, data centers).
    
    Reacts to:
    - Price increases (demand destruction)
    - Supply shortages (forced curtailment)
    - Economic conditions
    """
    
    def __init__(
        self,
        unique_id: str,
        model: "EnergyMarketModel",
        zone: ZoneId,
        industry_type: str,
        base_demand_mw: float,
        price_elasticity: float = -0.3,
    ):
        super().__init__(unique_id, model, zone)
        self.industry_type = industry_type
        self.base_demand_mw = base_demand_mw
        self.current_demand_mw = base_demand_mw
        self.price_elasticity = price_elasticity  # Negative = reduces demand as price rises
        
        # Economic output (used for GDP impact calculation)
        self.output_per_mwh_eur = 500  # Economic output per MWh consumed
        
    def receive_shock(self, shock_type: EventType, severity: float) -> list[DominoEffect]:
        effects = []
        
        # Industrial shocks
        if shock_type == EventType.INDUSTRIAL_SURGE:
            # Increase demand
            demand_increase = self.base_demand_mw * severity * 0.5
            self.current_demand_mw += demand_increase
            effects.append(DominoEffect(
                step=1,
                source=self.unique_id,
                target=f"zone_{self.zone.value}",
                effect_type="demand_increase",
                magnitude=demand_increase,
                unit="MW",
                description=f"Industrial surge at {self.unique_id}: demand +{demand_increase:.0f} MW",
                delay_hours=0,
            ))
        
        return effects
    
    def propagate_effect(self, effect: DominoEffect) -> list[DominoEffect]:
        secondary = []
        
        # React to price increases
        if effect.effect_type == "price_increase" and effect.target == f"zone_{self.zone.value}":
            price_change_pct = effect.magnitude / 50 * 100  # Assume 50 EUR/MWh baseline
            demand_change_pct = price_change_pct * self.price_elasticity
            demand_reduction = self.current_demand_mw * abs(demand_change_pct) / 100
            
            if demand_reduction > 0:
                self.current_demand_mw -= demand_reduction
                
                # Economic impact
                lost_output = demand_reduction * self.output_per_mwh_eur
                
                secondary.append(DominoEffect(
                    step=effect.step + 1,
                    source=self.unique_id,
                    target="economy",
                    effect_type="output_reduction",
                    magnitude=lost_output,
                    unit="EUR",
                    description=f"Industrial demand destruction at {self.unique_id}: -{demand_reduction:.0f} MW, economic loss {lost_output:.0f} EUR/h",
                    delay_hours=effect.delay_hours + 2,
                    cost_impact_eur=lost_output,
                ))
                self.state = AgentState.STRESSED
        
        # React to supply shortage
        if effect.effect_type == "supply_shortage" and effect.target == f"zone_{self.zone.value}":
            curtailment = min(effect.magnitude, self.current_demand_mw * 0.3)
            if curtailment > 0:
                self.current_demand_mw -= curtailment
                self.state = AgentState.CRITICAL
                secondary.append(DominoEffect(
                    step=effect.step + 1,
                    source=self.unique_id,
                    target="economy",
                    effect_type="forced_curtailment",
                    magnitude=curtailment * self.output_per_mwh_eur,
                    unit="EUR",
                    description=f"Forced curtailment at {self.unique_id}: -{curtailment:.0f} MW",
                    delay_hours=effect.delay_hours + 0.5,
                    cost_impact_eur=curtailment * self.output_per_mwh_eur * 2,  # Higher cost due to disruption
                ))
        
        return secondary
    
    def step(self):
        # Recovery towards baseline
        recovery_rate = 0.02
        self.current_demand_mw += (self.base_demand_mw - self.current_demand_mw) * recovery_rate
        if abs(self.current_demand_mw - self.base_demand_mw) < self.base_demand_mw * 0.1:
            self.state = AgentState.NORMAL


class HouseholdAgent(BaseEnergyAgent):
    """
    Household/residential consumer agent.
    
    Reacts to:
    - Temperature (heating/cooling demand)
    - Prices (limited elasticity)
    - CPI impacts
    """
    
    def __init__(
        self,
        unique_id: str,
        model: "EnergyMarketModel",
        zone: ZoneId,
        num_households: int,
        base_demand_mw: float,
    ):
        super().__init__(unique_id, model, zone)
        self.num_households = num_households
        self.base_demand_mw = base_demand_mw
        self.current_demand_mw = base_demand_mw
        self.price_elasticity = -0.1  # Households are less elastic
        
        # CPI tracking
        self.energy_cost_per_household_eur = 0.0
        
    def receive_shock(self, shock_type: EventType, severity: float) -> list[DominoEffect]:
        effects = []
        
        if shock_type == EventType.COLD_WAVE:
            # Heating demand surge
            demand_increase = self.base_demand_mw * severity * 0.6
            self.current_demand_mw += demand_increase
            effects.append(DominoEffect(
                step=1,
                source=self.unique_id,
                target=f"zone_{self.zone.value}",
                effect_type="demand_increase",
                magnitude=demand_increase,
                unit="MW",
                description=f"Cold wave: residential heating demand +{demand_increase:.0f} MW in {self.zone.value}",
                delay_hours=0,
            ))
            
        elif shock_type == EventType.HEAT_WAVE:
            # Cooling demand (less significant in Sweden but growing)
            demand_increase = self.base_demand_mw * severity * 0.3
            self.current_demand_mw += demand_increase
            effects.append(DominoEffect(
                step=1,
                source=self.unique_id,
                target=f"zone_{self.zone.value}",
                effect_type="demand_increase",
                magnitude=demand_increase,
                unit="MW",
                description=f"Heat wave: residential cooling demand +{demand_increase:.0f} MW in {self.zone.value}",
                delay_hours=0,
            ))
        
        return effects
    
    def propagate_effect(self, effect: DominoEffect) -> list[DominoEffect]:
        secondary = []
        
        # React to price increases - impacts CPI
        if effect.effect_type == "price_increase" and effect.target == f"zone_{self.zone.value}":
            price_increase = effect.magnitude
            
            # Calculate household impact
            hourly_consumption_mwh = self.current_demand_mw / self.num_households
            additional_cost = hourly_consumption_mwh * price_increase * 24 * 30  # Monthly
            self.energy_cost_per_household_eur += additional_cost
            
            # CPI impact (energy is ~10% of Swedish CPI basket)
            # Rough calculation: if energy costs rise X%, CPI rises ~0.1*X%
            cpi_impact_bps = (price_increase / 50) * 10 * 100  # Basis points
            
            secondary.append(DominoEffect(
                step=effect.step + 1,
                source=self.unique_id,
                target="cpi",
                effect_type="household_energy_cost",
                magnitude=additional_cost * self.num_households,
                unit="EUR",
                description=f"Household energy cost increase: +{additional_cost:.0f} EUR/month per household, CPI impact +{cpi_impact_bps:.0f} bps",
                delay_hours=effect.delay_hours + 720,  # Shows up in next month's CPI
                cpi_impact_bps=cpi_impact_bps,
            ))
        
        return secondary
    
    def step(self):
        recovery_rate = 0.05
        self.current_demand_mw += (self.base_demand_mw - self.current_demand_mw) * recovery_rate


class RetailerAgent(BaseEnergyAgent):
    """
    Energy retailer agent.
    
    Buys wholesale, sells to consumers.
    Sets consumer prices (affects CPI directly).
    """
    
    def __init__(
        self,
        unique_id: str,
        model: "EnergyMarketModel",
        zone: ZoneId,
        market_share: float,
    ):
        super().__init__(unique_id, model, zone)
        self.market_share = market_share
        self.wholesale_cost_eur_mwh = 50.0
        self.retail_price_eur_mwh = 80.0  # Includes margin, taxes, fees
        self.margin_pct = 0.15
        
    def receive_shock(self, shock_type: EventType, severity: float) -> list[DominoEffect]:
        return []  # Retailers don't receive primary shocks
    
    def propagate_effect(self, effect: DominoEffect) -> list[DominoEffect]:
        secondary = []
        
        # React to wholesale price changes
        if effect.effect_type in ["price_increase", "supply_shortage"]:
            if effect.target == f"zone_{self.zone.value}":
                wholesale_increase = effect.magnitude
                self.wholesale_cost_eur_mwh += wholesale_increase
                
                # Pass through to consumers (with delay and partial pass-through)
                pass_through_rate = 0.8
                retail_increase = wholesale_increase * pass_through_rate
                self.retail_price_eur_mwh += retail_increase
                
                secondary.append(DominoEffect(
                    step=effect.step + 1,
                    source=self.unique_id,
                    target="consumers",
                    effect_type="retail_price_increase",
                    magnitude=retail_increase,
                    unit="EUR/MWh",
                    description=f"Retailer {self.unique_id} raised prices by {retail_increase:.1f} EUR/MWh",
                    delay_hours=effect.delay_hours + 168,  # ~1 week delay
                    cpi_impact_bps=retail_increase / 50 * 10 * 100 * self.market_share,
                ))
        
        return secondary
    
    def step(self):
        pass


class GridOperatorAgent(BaseEnergyAgent):
    """
    Grid operator agent (Svenska kraftnät).
    
    Balances supply and demand across zones.
    Manages interconnections.
    Triggers emergency measures.
    """
    
    def __init__(self, unique_id: str, model: "EnergyMarketModel"):
        super().__init__(unique_id, model, ZoneId.SE3)  # HQ in Stockholm area
        self.system_balance_mw = 0.0
        self.reserve_margin_mw = 1500.0
        self.current_reserves_mw = 1500.0
        self.alert_level = 0  # 0=normal, 1=elevated, 2=emergency
        
    def receive_shock(self, shock_type: EventType, severity: float) -> list[DominoEffect]:
        effects = []
        
        if shock_type == EventType.CABLE_FAILURE:
            # Interconnection failure
            capacity_loss = 1000 * severity  # MW
            effects.append(DominoEffect(
                step=1,
                source=self.unique_id,
                target="grid",
                effect_type="capacity_reduction",
                magnitude=capacity_loss,
                unit="MW",
                description=f"Interconnection failure: -{capacity_loss:.0f} MW transfer capacity",
                delay_hours=0,
            ))
            self.alert_level = 2 if severity > 0.5 else 1
        
        return effects
    
    def propagate_effect(self, effect: DominoEffect) -> list[DominoEffect]:
        secondary = []
        
        # React to production/demand imbalances
        if effect.effect_type == "production_reduction":
            self.system_balance_mw -= effect.magnitude
        elif effect.effect_type in ["demand_increase", "production_increase"]:
            self.system_balance_mw += effect.magnitude if "production" in effect.effect_type else -effect.magnitude
        
        # Check if reserves needed
        if abs(self.system_balance_mw) > self.reserve_margin_mw * 0.5:
            self.alert_level = 1
            
            if abs(self.system_balance_mw) > self.reserve_margin_mw:
                self.alert_level = 2
                # Emergency measures
                shortage = abs(self.system_balance_mw) - self.reserve_margin_mw
                
                secondary.append(DominoEffect(
                    step=effect.step + 1,
                    source=self.unique_id,
                    target="all_zones",
                    effect_type="supply_shortage" if self.system_balance_mw < 0 else "surplus",
                    magnitude=shortage,
                    unit="MW",
                    description=f"Grid operator declares {'shortage' if self.system_balance_mw < 0 else 'surplus'}: {shortage:.0f} MW",
                    delay_hours=effect.delay_hours + 0.1,
                ))
                
                # Trigger price spike
                secondary.append(DominoEffect(
                    step=effect.step + 1,
                    source=self.unique_id,
                    target="all_zones",
                    effect_type="price_increase",
                    magnitude=shortage / 10,  # EUR/MWh increase
                    unit="EUR/MWh",
                    description=f"Emergency price spike: +{shortage/10:.1f} EUR/MWh",
                    delay_hours=effect.delay_hours + 0.1,
                ))
        
        return secondary
    
    def step(self):
        # Gradual recovery
        recovery_rate = 0.1
        self.system_balance_mw *= (1 - recovery_rate)
        if abs(self.system_balance_mw) < self.reserve_margin_mw * 0.3:
            self.alert_level = 0


class EnergyMarketModel(Model):
    """
    Mesa model representing the Swedish energy market.
    
    Orchestrates all agents and propagates domino effects.
    """
    
    def __init__(self, seed: Optional[int] = None):
        super().__init__(seed=seed)
        
        self.current_step = 0
        self.domino_chain: list[DominoEffect] = []
        
        # Initialize agents
        self._create_agents()
        
        # Data collection
        self.datacollector = DataCollector(
            model_reporters={
                "Total_Production_MW": self._get_total_production,
                "Total_Demand_MW": self._get_total_demand,
                "System_Balance_MW": lambda m: m.grid_operator.system_balance_mw,
                "Alert_Level": lambda m: m.grid_operator.alert_level,
                "Domino_Effects_Count": lambda m: len(m.domino_chain),
            },
            agent_reporters={
                "State": "state",
                "Zone": lambda a: a.zone.value if hasattr(a, 'zone') else "grid",
            }
        )
        
    def _create_agents(self):
        """Create all agents in the system."""
        agent_id = 0
        
        # Create producers for each zone
        producer_configs = [
            # SE1 - Hydro dominant
            (ZoneId.SE1, EnergySourceType.HYDRO, 6000, 15),
            (ZoneId.SE1, EnergySourceType.WIND, 1500, 5),
            # SE2 - Mixed
            (ZoneId.SE2, EnergySourceType.HYDRO, 3000, 18),
            (ZoneId.SE2, EnergySourceType.WIND, 1500, 5),
            # SE3 - Nuclear + mixed
            (ZoneId.SE3, EnergySourceType.NUCLEAR, 6500, 25),
            (ZoneId.SE3, EnergySourceType.HYDRO, 2000, 20),
            (ZoneId.SE3, EnergySourceType.WIND, 3000, 6),
            (ZoneId.SE3, EnergySourceType.GAS, 500, 80),
            # SE4 - Wind + import
            (ZoneId.SE4, EnergySourceType.WIND, 2500, 5),
            (ZoneId.SE4, EnergySourceType.GAS, 300, 85),
        ]
        
        self.producers: list[EnergyProducerAgent] = []
        for zone, source, capacity, cost in producer_configs:
            agent = EnergyProducerAgent(
                f"producer_{agent_id}",
                self,
                zone,
                source,
                capacity,
                cost,
            )
            self.producers.append(agent)
            agent_id += 1
        
        # Create industrial consumers
        industrial_configs = [
            (ZoneId.SE1, "mining", 800),
            (ZoneId.SE2, "paper_mill", 600),
            (ZoneId.SE3, "data_center", 400),
            (ZoneId.SE3, "manufacturing", 1200),
            (ZoneId.SE4, "refinery", 500),
        ]
        
        self.industrials: list[IndustrialConsumerAgent] = []
        for zone, industry, demand in industrial_configs:
            agent = IndustrialConsumerAgent(
                f"industrial_{agent_id}",
                self,
                zone,
                industry,
                demand,
            )
            self.industrials.append(agent)
            agent_id += 1
        
        # Create household aggregates (one per zone)
        household_configs = [
            (ZoneId.SE1, 300000, 400),
            (ZoneId.SE2, 500000, 700),
            (ZoneId.SE3, 3000000, 4500),
            (ZoneId.SE4, 1500000, 2200),
        ]
        
        self.households: list[HouseholdAgent] = []
        for zone, num_hh, demand in household_configs:
            agent = HouseholdAgent(
                f"households_{zone.value}",
                self,
                zone,
                num_hh,
                demand,
            )
            self.households.append(agent)
        
        # Create retailers
        self.retailers: list[RetailerAgent] = []
        for zone in ZoneId:
            agent = RetailerAgent(
                f"retailer_{zone.value}",
                self,
                zone,
                0.25,  # 25% market share each
            )
            self.retailers.append(agent)
        
        # Create grid operator
        self.grid_operator = GridOperatorAgent("svenska_kraftnat", self)
        
        logger.info(f"Created {len(self.producers)} producers, {len(self.industrials)} industrials, "
                   f"{len(self.households)} household groups, {len(self.retailers)} retailers")
    
    def inject_shock(self, shock_type: EventType, severity: float, target_zones: Optional[list[ZoneId]] = None) -> list[DominoEffect]:
        """
        Inject a shock into the system and propagate domino effects.
        
        Returns the complete chain of domino effects.
        """
        logger.warning(f"💥 SHOCK INJECTED: {shock_type.value} (severity: {severity:.0%})")
        
        self.domino_chain = []
        effects_queue: list[DominoEffect] = []
        
        # Get all agents
        all_agents = self.producers + self.industrials + self.households + self.retailers + [self.grid_operator]
        
        # Phase 1: Primary shock impacts
        for agent in all_agents:
            if isinstance(agent, BaseEnergyAgent):
                # Check if agent is in target zones (or all zones if not specified)
                if target_zones is None or (hasattr(agent, 'zone') and agent.zone in target_zones):
                    primary_effects = agent.receive_shock(shock_type, severity)
                    effects_queue.extend(primary_effects)
        
        # Phase 2: Propagate domino effects
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while effects_queue and iteration < max_iterations:
            iteration += 1
            current_effects = effects_queue.copy()
            effects_queue = []
            
            for effect in current_effects:
                self.domino_chain.append(effect)
                
                # Propagate to all agents
                for agent in all_agents:
                    if isinstance(agent, BaseEnergyAgent):
                        secondary = agent.propagate_effect(effect)
                        effects_queue.extend(secondary)
        
        logger.info(f"Shock propagation complete: {len(self.domino_chain)} domino effects across {iteration} iterations")
        return self.domino_chain
    
    def _get_total_production(self) -> float:
        return sum(p.current_output_mw for p in self.producers)
    
    def _get_total_demand(self) -> float:
        return sum(i.current_demand_mw for i in self.industrials) + \
               sum(h.current_demand_mw for h in self.households)
    
    def step(self):
        """Advance the model by one step."""
        self.current_step += 1
        self.datacollector.collect(self)
        # Step all agents
        all_agents = self.producers + self.industrials + self.households + self.retailers + [self.grid_operator]
        for agent in all_agents:
            agent.step()
    
    def run_simulation(self, steps: int = 24) -> list[dict]:
        """Run simulation for N steps (hours)."""
        results = []
        for _ in range(steps):
            self.step()
            results.append({
                "step": self.current_step,
                "production_mw": self._get_total_production(),
                "demand_mw": self._get_total_demand(),
                "balance_mw": self.grid_operator.system_balance_mw,
                "alert_level": self.grid_operator.alert_level,
            })
        return results
