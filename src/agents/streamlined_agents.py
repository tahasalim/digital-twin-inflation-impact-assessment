"""
Streamlined Multi-Agent Orchestration System for Swedish Energy Digital Twin.

Simplified hierarchy (1 + 3 + 9 = 13 agents):
- Master Orchestrator: Coordinates scenario simulation
- 3 Domain Orchestrators: Supply, Demand, External Factors
- 9 Specialists: 3 per domain

Features:
- DEBUG_MODE for dry-run testing without API calls
- Detailed scenario output with breakpoints
- Aggregated results for summary dashboard
"""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from loguru import logger
import random
import math

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Check for debug mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
MOCK_API_CALLS = os.getenv("MOCK_API_CALLS", "true").lower() in ("true", "1", "yes")


# =============================================================================
# ENUMS
# =============================================================================

class AgentRole(str, Enum):
    MASTER = "master"
    DOMAIN = "domain"
    SPECIALIST = "specialist"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class Domain(str, Enum):
    """Three main domains for MECE coverage."""
    SUPPLY = "supply"           # Energy production
    DEMAND = "demand"           # Energy consumption
    EXTERNAL = "external"       # Weather, markets, geopolitics


class Severity(str, Enum):
    """Severity levels for breakpoints."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# DATA MODELS
# =============================================================================

class Breakpoint(BaseModel):
    """Critical scenario breakpoint."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    domain: Domain
    title: str
    description: str
    severity: Severity
    impact_score: float = Field(ge=0, le=10)
    affected_zones: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    data: dict = Field(default_factory=dict)


class ScenarioOutput(BaseModel):
    """Output from a single agent scenario simulation."""
    agent_id: str
    agent_name: str
    domain: Domain
    scenario_description: str
    
    # Metrics
    baseline_value: float
    simulated_value: float
    change_percent: float
    confidence: float = Field(ge=0, le=1)
    
    # Time series (simplified)
    hourly_values: list[float] = Field(default_factory=list)
    
    # Risk assessment
    risk_level: Severity = Severity.LOW
    risk_factors: list[str] = Field(default_factory=list)
    
    # CPI impact
    estimated_cpi_impact_bps: float = 0.0


class DomainSummary(BaseModel):
    """Aggregated summary for a domain."""
    domain: Domain
    agent_count: int
    avg_change_percent: float
    max_risk_level: Severity
    total_cpi_impact_bps: float
    breakpoints: list[Breakpoint] = Field(default_factory=list)
    outputs: list[ScenarioOutput] = Field(default_factory=list)


class SimulationResult(BaseModel):
    """Complete simulation result from the multi-agent system."""
    scenario_name: str
    trigger_event: str
    start_time: datetime
    end_time: datetime
    duration_hours: int
    
    # Agent hierarchy
    total_agents: int
    api_calls_made: int
    is_debug_mode: bool
    
    # Domain summaries
    supply_summary: Optional[DomainSummary] = None
    demand_summary: Optional[DomainSummary] = None
    external_summary: Optional[DomainSummary] = None
    
    # All outputs
    all_outputs: list[ScenarioOutput] = Field(default_factory=list)
    
    # All breakpoints (critical events)
    breakpoints: list[Breakpoint] = Field(default_factory=list)
    
    # Final synthesis
    total_cpi_impact_bps: float = 0.0
    overall_risk_level: Severity = Severity.LOW
    executive_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AgentNode(BaseModel):
    """Node representation for visualization."""
    id: str
    name: str
    role: AgentRole
    domain: Optional[Domain] = None
    status: AgentStatus = AgentStatus.IDLE
    parent_id: Optional[str] = None
    children_ids: list[str] = Field(default_factory=list)
    level: int = 0
    x: float = 0.0
    y: float = 0.0
    output: Optional[ScenarioOutput] = None


# =============================================================================
# SPECIALIST AGENT
# =============================================================================

class SpecialistAgent:
    """
    Specialist agent that simulates a specific aspect.
    
    3 specialists per domain = 9 total.
    """
    
    # Specialist configurations by domain
    SPECIALIST_CONFIGS = {
        Domain.SUPPLY: [
            {"name": "Nuclear Production", "metric": "nuclear_mw", "base": 6500, "volatility": 0.03},
            {"name": "Hydro Production", "metric": "hydro_mw", "base": 8000, "volatility": 0.15},
            {"name": "Wind & Solar", "metric": "renewable_mw", "base": 5000, "volatility": 0.35},
        ],
        Domain.DEMAND: [
            {"name": "Industrial Demand", "metric": "industrial_mw", "base": 7000, "volatility": 0.08},
            {"name": "Residential Demand", "metric": "residential_mw", "base": 5000, "volatility": 0.20},
            {"name": "Commercial Demand", "metric": "commercial_mw", "base": 3000, "volatility": 0.12},
        ],
        Domain.EXTERNAL: [
            {"name": "Weather Impact", "metric": "weather_score", "base": 50, "volatility": 0.25},
            {"name": "Market Prices", "metric": "price_eur_mwh", "base": 45, "volatility": 0.30},
            {"name": "Geopolitical Risk", "metric": "risk_score", "base": 30, "volatility": 0.15},
        ],
    }
    
    def __init__(self, agent_id: str, name: str, domain: Domain, config: dict):
        self.id = agent_id
        self.name = name
        self.domain = domain
        self.config = config
        self.status = AgentStatus.IDLE
        
        self.base_value = config["base"]
        self.volatility = config["volatility"]
        self.metric = config["metric"]
        
        self.output: Optional[ScenarioOutput] = None
        self.breakpoints: list[Breakpoint] = []
        self.hourly_values: list[float] = []
        self.api_calls = 0
    
    async def simulate(
        self,
        trigger: str,
        trigger_magnitude: float,
        duration_hours: int
    ) -> ScenarioOutput:
        """Run simulation for this specialist."""
        self.status = AgentStatus.RUNNING
        
        # Determine trigger impact on this specialist
        impact_factor = self._calculate_trigger_impact(trigger, trigger_magnitude)
        
        # Simulate hourly values
        self.hourly_values = []
        current = self.base_value
        max_deviation = 0
        
        for hour in range(duration_hours):
            # Apply trend, seasonality, and noise
            trend = impact_factor * (hour / duration_hours) * self.base_value
            seasonal = self.base_value * 0.05 * math.sin(hour * math.pi / 12)  # Daily cycle
            noise = random.gauss(0, self.base_value * self.volatility * 0.1)
            
            current = self.base_value + trend + seasonal + noise
            current = max(0, current)  # No negative values
            self.hourly_values.append(current)
            
            deviation = abs(current - self.base_value) / self.base_value
            max_deviation = max(max_deviation, deviation)
            
            # Check for breakpoint conditions
            if deviation > 0.15:  # 15% deviation triggers breakpoint
                self._create_breakpoint(hour, current, deviation)
        
        # Calculate final metrics
        final_value = self.hourly_values[-1] if self.hourly_values else self.base_value
        change_pct = ((final_value - self.base_value) / self.base_value) * 100
        
        # Risk assessment
        risk_level = self._assess_risk(max_deviation)
        
        # CPI impact (energy weight ~6% of CPI)
        cpi_impact = abs(change_pct) * 0.06 * self._get_cpi_weight()
        
        self.output = ScenarioOutput(
            agent_id=self.id,
            agent_name=self.name,
            domain=self.domain,
            scenario_description=f"{self.name} simulation under {trigger} scenario",
            baseline_value=self.base_value,
            simulated_value=final_value,
            change_percent=change_pct,
            confidence=0.7 + random.uniform(0, 0.2),
            hourly_values=self.hourly_values,
            risk_level=risk_level,
            risk_factors=self._identify_risk_factors(trigger, change_pct),
            estimated_cpi_impact_bps=round(cpi_impact, 2)
        )
        
        self.status = AgentStatus.COMPLETED
        return self.output
    
    def _calculate_trigger_impact(self, trigger: str, magnitude: float) -> float:
        """Calculate how much this specialist is affected by the trigger."""
        trigger = trigger.lower()
        
        # Impact mappings
        impact_map = {
            ("drought", "hydro"): -0.35,
            ("drought", "weather"): 0.20,
            ("drought", "price"): 0.25,
            ("cold", "residential"): 0.40,
            ("cold", "weather"): -0.30,
            ("cold", "wind"): -0.15,
            ("nuclear", "nuclear"): -0.50,
            ("nuclear", "price"): 0.35,
            ("war", "geopolitical"): 0.60,
            ("war", "price"): 0.45,
            ("crisis", "price"): 0.40,
            ("crisis", "industrial"): -0.20,
        }
        
        base_impact = 0.0
        name_lower = self.name.lower()
        
        for (trigger_key, metric_key), impact in impact_map.items():
            if trigger_key in trigger and metric_key in name_lower:
                base_impact = impact
                break
        
        # Default small impact if no specific mapping
        if base_impact == 0:
            base_impact = random.uniform(-0.1, 0.1)
        
        return base_impact * magnitude
    
    def _assess_risk(self, max_deviation: float) -> Severity:
        """Assess risk level based on deviation."""
        if max_deviation > 0.30:
            return Severity.CRITICAL
        elif max_deviation > 0.20:
            return Severity.HIGH
        elif max_deviation > 0.10:
            return Severity.MEDIUM
        return Severity.LOW
    
    def _identify_risk_factors(self, trigger: str, change_pct: float) -> list[str]:
        """Identify key risk factors."""
        factors = []
        
        if abs(change_pct) > 20:
            factors.append(f"High volatility: {change_pct:+.1f}% change")
        
        if "drought" in trigger.lower() and "hydro" in self.name.lower():
            factors.append("Reduced hydroelectric capacity due to low water levels")
        
        if "cold" in trigger.lower() and "demand" in self.name.lower():
            factors.append("Increased heating demand from cold weather")
        
        if len(self.breakpoints) > 0:
            factors.append(f"{len(self.breakpoints)} critical thresholds exceeded")
        
        return factors or ["Normal operating conditions"]
    
    def _get_cpi_weight(self) -> float:
        """Get the CPI weight for this metric."""
        weights = {
            "nuclear": 0.15,
            "hydro": 0.20,
            "renewable": 0.10,
            "industrial": 0.25,
            "residential": 0.20,
            "commercial": 0.10,
            "weather": 0.0,
            "price": 1.0,
            "geopolitical": 0.0,
        }
        
        for key, weight in weights.items():
            if key in self.metric.lower():
                return weight
        return 0.1
    
    def _create_breakpoint(self, hour: int, value: float, deviation: float) -> None:
        """Create a breakpoint for significant deviations."""
        severity = Severity.MEDIUM if deviation < 0.25 else Severity.HIGH
        if deviation > 0.35:
            severity = Severity.CRITICAL
        
        bp = Breakpoint(
            id=f"bp_{self.id}_{hour}",
            timestamp=datetime.utcnow() + timedelta(hours=hour),
            agent_id=self.id,
            domain=self.domain,
            title=f"{self.name} threshold exceeded",
            description=f"{self.name} deviated {deviation*100:.1f}% from baseline at hour {hour}",
            severity=severity,
            impact_score=min(10, deviation * 20),
            affected_zones=["SE3", "SE4"] if self.domain == Domain.DEMAND else ["SE1", "SE2"],
            recommended_actions=self._get_recommendations(deviation),
            data={"hour": hour, "value": value, "baseline": self.base_value, "deviation_pct": deviation * 100}
        )
        self.breakpoints.append(bp)
    
    def _get_recommendations(self, deviation: float) -> list[str]:
        """Get recommended actions based on deviation."""
        if deviation > 0.30:
            return [
                "Activate emergency reserves",
                "Consider import capacity increase",
                "Alert grid operators"
            ]
        elif deviation > 0.20:
            return [
                "Monitor closely",
                "Prepare contingency measures",
                "Review demand response options"
            ]
        return ["Continue monitoring"]
    
    def to_node(self, parent_id: str, level: int = 2) -> AgentNode:
        """Convert to visualization node."""
        return AgentNode(
            id=self.id,
            name=self.name,
            role=AgentRole.SPECIALIST,
            domain=self.domain,
            status=self.status,
            parent_id=parent_id,
            children_ids=[],
            level=level,
            output=self.output
        )


# =============================================================================
# DOMAIN ORCHESTRATOR
# =============================================================================

class DomainOrchestrator:
    """
    Domain orchestrator that manages 3 specialists.
    
    3 domains: Supply, Demand, External.
    """
    
    def __init__(self, domain: Domain):
        self.id = f"domain_{domain.value}"
        self.name = f"{domain.value.title()} Domain"
        self.domain = domain
        self.status = AgentStatus.IDLE
        
        # Create 3 specialists
        self.specialists: list[SpecialistAgent] = []
        configs = SpecialistAgent.SPECIALIST_CONFIGS[domain]
        
        for i, config in enumerate(configs):
            specialist = SpecialistAgent(
                agent_id=f"spec_{domain.value}_{i}",
                name=config["name"],
                domain=domain,
                config=config
            )
            self.specialists.append(specialist)
        
        self.summary: Optional[DomainSummary] = None
        self.api_calls = 0
    
    async def simulate(
        self,
        trigger: str,
        trigger_magnitude: float,
        duration_hours: int
    ) -> DomainSummary:
        """Run simulation across all specialists."""
        self.status = AgentStatus.RUNNING
        
        # Optionally fetch trends data (1 API call per domain if enabled)
        if not MOCK_API_CALLS and not DEBUG_MODE:
            await self._fetch_context_data(trigger)
        
        # Run all specialists concurrently
        tasks = [
            spec.simulate(trigger, trigger_magnitude, duration_hours)
            for spec in self.specialists
        ]
        outputs = await asyncio.gather(*tasks)
        
        # Aggregate results
        all_breakpoints = []
        for spec in self.specialists:
            all_breakpoints.extend(spec.breakpoints)
        
        # Calculate domain summary
        avg_change = sum(o.change_percent for o in outputs) / len(outputs)
        max_risk = max((o.risk_level for o in outputs), key=lambda x: list(Severity).index(x))
        total_cpi = sum(o.estimated_cpi_impact_bps for o in outputs)
        
        self.summary = DomainSummary(
            domain=self.domain,
            agent_count=len(self.specialists),
            avg_change_percent=avg_change,
            max_risk_level=max_risk,
            total_cpi_impact_bps=total_cpi,
            breakpoints=sorted(all_breakpoints, key=lambda x: x.impact_score, reverse=True),
            outputs=list(outputs)
        )
        
        self.status = AgentStatus.COMPLETED
        return self.summary
    
    async def _fetch_context_data(self, trigger: str) -> None:
        """Fetch context data from APIs (limited to 1 call per domain)."""
        try:
            from src.api.providers import get_api
            
            # One API call for trends
            trends_api = get_api("google_trends")
            if trends_api and trends_api.is_enabled:
                await trends_api.get_data(keywords=[f"{self.domain.value} energy {trigger}"])
                self.api_calls += 1
        except Exception as e:
            logger.debug(f"API call skipped: {e}")
    
    def get_nodes(self) -> list[AgentNode]:
        """Get all nodes including specialists."""
        nodes = [
            AgentNode(
                id=self.id,
                name=self.name,
                role=AgentRole.DOMAIN,
                domain=self.domain,
                status=self.status,
                parent_id="master",
                children_ids=[s.id for s in self.specialists],
                level=1
            )
        ]
        
        for spec in self.specialists:
            nodes.append(spec.to_node(self.id))
        
        return nodes


# =============================================================================
# MASTER ORCHESTRATOR
# =============================================================================

class MasterOrchestrator:
    """
    Master orchestrator (GameMaster) that coordinates 3 domain orchestrators.
    
    Hierarchy: 1 Master -> 3 Domains -> 9 Specialists = 13 agents total.
    """
    
    def __init__(self, name: str = "Swedish Energy GameMaster"):
        self.id = "master"
        self.name = name
        self.status = AgentStatus.IDLE
        
        # Create 3 domain orchestrators
        self.domains: dict[Domain, DomainOrchestrator] = {
            Domain.SUPPLY: DomainOrchestrator(Domain.SUPPLY),
            Domain.DEMAND: DomainOrchestrator(Domain.DEMAND),
            Domain.EXTERNAL: DomainOrchestrator(Domain.EXTERNAL),
        }
        
        self.result: Optional[SimulationResult] = None
        self.api_calls = 0
    
    @property
    def total_agents(self) -> int:
        return 1 + 3 + 9  # master + domains + specialists
    
    async def run_simulation(
        self,
        scenario_name: str,
        trigger_event: str,
        duration_hours: int = 24,
        trigger_magnitude: float = 1.0
    ) -> SimulationResult:
        """Run complete multi-agent simulation."""
        self.status = AgentStatus.RUNNING
        start_time = datetime.utcnow()
        
        logger.info(f"🎮 Master Orchestrator starting: {scenario_name}")
        logger.info(f"   Trigger: {trigger_event} (magnitude: {trigger_magnitude})")
        logger.info(f"   Duration: {duration_hours}h | Agents: {self.total_agents}")
        logger.info(f"   Mode: {'DEBUG' if DEBUG_MODE else 'LIVE'} | Mock APIs: {MOCK_API_CALLS}")
        
        # Run all domains concurrently
        tasks = [
            domain.simulate(trigger_event, trigger_magnitude, duration_hours)
            for domain in self.domains.values()
        ]
        summaries = await asyncio.gather(*tasks)
        
        # Count total API calls
        total_api_calls = sum(d.api_calls for d in self.domains.values())
        
        # Collect all outputs and breakpoints
        all_outputs = []
        all_breakpoints = []
        
        for summary in summaries:
            all_outputs.extend(summary.outputs)
            all_breakpoints.extend(summary.breakpoints)
        
        # Calculate overall metrics
        total_cpi_impact = sum(s.total_cpi_impact_bps for s in summaries)
        
        # Determine overall risk level
        risk_levels = [s.max_risk_level for s in summaries]
        overall_risk = max(risk_levels, key=lambda x: list(Severity).index(x))
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            scenario_name, trigger_event, summaries, total_cpi_impact, overall_risk
        )
        
        # Generate key findings and recommendations
        key_findings = self._generate_key_findings(summaries, all_breakpoints)
        recommendations = self._generate_recommendations(overall_risk, all_breakpoints)
        
        # Sort breakpoints by severity and impact
        all_breakpoints.sort(key=lambda x: (
            list(Severity).index(x.severity),
            -x.impact_score
        ), reverse=True)
        
        end_time = datetime.utcnow()
        
        self.result = SimulationResult(
            scenario_name=scenario_name,
            trigger_event=trigger_event,
            start_time=start_time,
            end_time=end_time,
            duration_hours=duration_hours,
            total_agents=self.total_agents,
            api_calls_made=total_api_calls,
            is_debug_mode=DEBUG_MODE or MOCK_API_CALLS,
            supply_summary=self.domains[Domain.SUPPLY].summary,
            demand_summary=self.domains[Domain.DEMAND].summary,
            external_summary=self.domains[Domain.EXTERNAL].summary,
            all_outputs=all_outputs,
            breakpoints=all_breakpoints[:20],  # Top 20 breakpoints
            total_cpi_impact_bps=round(total_cpi_impact, 2),
            overall_risk_level=overall_risk,
            executive_summary=executive_summary,
            key_findings=key_findings,
            recommendations=recommendations
        )
        
        self.status = AgentStatus.COMPLETED
        
        logger.success(f"✅ Simulation complete: {len(all_outputs)} outputs, {len(all_breakpoints)} breakpoints")
        logger.info(f"   Total CPI Impact: {total_cpi_impact:.2f} bps | Risk: {overall_risk.value}")
        
        return self.result
    
    def _generate_executive_summary(
        self,
        scenario_name: str,
        trigger: str,
        summaries: list[DomainSummary],
        cpi_impact: float,
        risk: Severity
    ) -> str:
        """Generate executive summary for Riksbanken economist."""
        risk_desc = {
            Severity.LOW: "manageable",
            Severity.MEDIUM: "moderate concern",
            Severity.HIGH: "significant concern",
            Severity.CRITICAL: "critical attention required"
        }
        
        supply_change = next((s.avg_change_percent for s in summaries if s.domain == Domain.SUPPLY), 0)
        demand_change = next((s.avg_change_percent for s in summaries if s.domain == Domain.DEMAND), 0)
        
        return (
            f"**Scenario Analysis: {scenario_name}**\n\n"
            f"The {trigger} scenario simulation indicates {risk_desc[risk]}. "
            f"Energy supply is projected to change by {supply_change:+.1f}% while demand "
            f"adjusts by {demand_change:+.1f}%. "
            f"The estimated impact on CPI is approximately {cpi_impact:.1f} basis points. "
            f"This analysis is based on {self.total_agents} agent simulations across "
            f"supply, demand, and external factor domains."
        )
    
    def _generate_key_findings(
        self,
        summaries: list[DomainSummary],
        breakpoints: list[Breakpoint]
    ) -> list[str]:
        """Generate key findings."""
        findings = []
        
        # Domain-specific findings
        for summary in summaries:
            if abs(summary.avg_change_percent) > 10:
                direction = "increase" if summary.avg_change_percent > 0 else "decrease"
                findings.append(
                    f"{summary.domain.value.title()} domain shows {abs(summary.avg_change_percent):.1f}% {direction}"
                )
        
        # Breakpoint-related findings
        critical_count = len([b for b in breakpoints if b.severity == Severity.CRITICAL])
        if critical_count > 0:
            findings.append(f"{critical_count} critical threshold(s) exceeded during simulation")
        
        # CPI findings
        total_cpi = sum(s.total_cpi_impact_bps for s in summaries)
        if total_cpi > 5:
            findings.append(f"Potential CPI impact of {total_cpi:.1f} bps warrants monetary policy attention")
        
        return findings or ["Simulation completed within normal parameters"]
    
    def _generate_recommendations(
        self,
        risk: Severity,
        breakpoints: list[Breakpoint]
    ) -> list[str]:
        """Generate recommendations based on simulation results."""
        recs = []
        
        if risk in [Severity.CRITICAL, Severity.HIGH]:
            recs.append("Consider activating contingency planning protocols")
            recs.append("Increase monitoring frequency for affected sectors")
        
        if risk == Severity.CRITICAL:
            recs.append("Recommend emergency coordination with grid operators")
            recs.append("Evaluate potential monetary policy implications")
        
        # Collect unique recommendations from breakpoints
        bp_recs = set()
        for bp in breakpoints[:5]:  # Top 5 breakpoints
            for rec in bp.recommended_actions[:2]:  # Top 2 recommendations each
                bp_recs.add(rec)
        
        recs.extend(list(bp_recs)[:3])
        
        return recs or ["Continue standard monitoring procedures"]
    
    def get_all_nodes(self) -> list[AgentNode]:
        """Get all nodes for visualization."""
        nodes = [
            AgentNode(
                id=self.id,
                name=self.name,
                role=AgentRole.MASTER,
                domain=None,
                status=self.status,
                parent_id=None,
                children_ids=[d.id for d in self.domains.values()],
                level=0
            )
        ]
        
        for domain_orch in self.domains.values():
            nodes.extend(domain_orch.get_nodes())
        
        return nodes


# =============================================================================
# MULTI-AGENT SYSTEM
# =============================================================================

class StreamlinedMultiAgentSystem:
    """
    Streamlined multi-agent system for energy scenario simulation.
    
    Features:
    - 13 total agents (1 + 3 + 9)
    - Limited API calls (~3-4 when enabled)
    - Debug mode for dry-run testing
    - Detailed scenario outputs with breakpoints
    """
    
    _instance: Optional['StreamlinedMultiAgentSystem'] = None
    
    def __init__(self):
        self.master = MasterOrchestrator()
        self.initialized = False
        self.last_result: Optional[SimulationResult] = None
    
    @classmethod
    def get_instance(cls) -> 'StreamlinedMultiAgentSystem':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize(self) -> None:
        """Initialize the system."""
        if not self.initialized:
            logger.info(f"Initializing StreamlinedMultiAgentSystem with {self.master.total_agents} agents")
            logger.info(f"DEBUG_MODE: {DEBUG_MODE} | MOCK_API_CALLS: {MOCK_API_CALLS}")
            self.initialized = True
    
    async def run_scenario(
        self,
        scenario_name: str,
        trigger_event: str,
        duration_hours: int = 24,
        trigger_magnitude: float = 1.0
    ) -> SimulationResult:
        """Run a complete scenario simulation."""
        if not self.initialized:
            self.initialize()
        
        self.last_result = await self.master.run_simulation(
            scenario_name=scenario_name,
            trigger_event=trigger_event,
            duration_hours=duration_hours,
            trigger_magnitude=trigger_magnitude
        )
        
        return self.last_result
    
    def get_agent_tree(self) -> list[AgentNode]:
        """Get agent hierarchy for visualization."""
        return self.master.get_all_nodes()
    
    def get_status(self) -> dict:
        """Get system status."""
        return {
            "initialized": self.initialized,
            "total_agents": self.master.total_agents,
            "debug_mode": DEBUG_MODE,
            "mock_api_calls": MOCK_API_CALLS,
            "has_result": self.last_result is not None,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_streamlined_system() -> StreamlinedMultiAgentSystem:
    """Get the streamlined multi-agent system singleton."""
    return StreamlinedMultiAgentSystem.get_instance()


def set_debug_mode(enabled: bool) -> None:
    """Enable or disable debug mode."""
    global DEBUG_MODE
    DEBUG_MODE = enabled


def set_mock_api_calls(enabled: bool) -> None:
    """Enable or disable API call mocking."""
    global MOCK_API_CALLS
    MOCK_API_CALLS = enabled


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("STREAMLINED MULTI-AGENT SYSTEM TEST")
        print("=" * 60)
        
        system = get_streamlined_system()
        system.initialize()
        
        print(f"\nStatus: {system.get_status()}")
        print(f"Agent tree: {len(system.get_agent_tree())} nodes")
        
        # Run simulation
        result = await system.run_scenario(
            scenario_name="Nordic Drought Test",
            trigger_event="nordic_drought",
            duration_hours=24,
            trigger_magnitude=0.8
        )
        
        print(f"\n{'='*60}")
        print("SIMULATION RESULTS")
        print(f"{'='*60}")
        print(f"Scenario: {result.scenario_name}")
        print(f"Duration: {result.duration_hours}h")
        print(f"Agents: {result.total_agents}")
        print(f"API Calls: {result.api_calls_made}")
        print(f"Debug Mode: {result.is_debug_mode}")
        print(f"\nTotal CPI Impact: {result.total_cpi_impact_bps:.2f} bps")
        print(f"Overall Risk: {result.overall_risk_level.value}")
        print(f"\nBreakpoints: {len(result.breakpoints)}")
        
        for bp in result.breakpoints[:5]:
            print(f"  - [{bp.severity.value}] {bp.title}: {bp.description}")
        
        print(f"\nKey Findings:")
        for finding in result.key_findings:
            print(f"  • {finding}")
        
        print(f"\nRecommendations:")
        for rec in result.recommendations:
            print(f"  → {rec}")
        
        print(f"\n{result.executive_summary}")
    
    asyncio.run(test())
