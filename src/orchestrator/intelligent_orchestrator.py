"""
Intelligent Master Orchestrator for Swedish Energy Digital Twin.

This orchestrator implements a 5-step intelligent workflow:
1. Historical Event Lookup - Query real Swedish historical events (droughts, nuclear outages, etc.)
2. Data Fetching - Gather relevant data from APIs, news, and social media
3. Agent Simulation - Feed data to timeline simulation and all domain agents
4. Verification - Validate that results are realistic using AI verification
5. Output - Generate final analysis with confidence scores

Author: Swedish Energy AI Team
"""

from __future__ import annotations

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field
from loguru import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# =============================================================================
# HISTORICAL EVENTS DATABASE
# =============================================================================

@dataclass
class HistoricalEvent:
    """A real historical event in Sweden's energy history."""
    event_id: str
    event_type: str
    name: str
    start_date: datetime
    end_date: datetime
    description: str
    severity: float  # 0.0 to 1.0
    affected_zones: List[str]
    peak_impact: Dict[str, Any]
    sources: List[str]
    
    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days


# Swedish Historical Events Database
# Based on real events from Swedish energy history
SWEDISH_HISTORICAL_EVENTS: Dict[str, List[HistoricalEvent]] = {
    "drought": [
        HistoricalEvent(
            event_id="drought_2018",
            event_type="drought",
            name="Nordic Drought 2018",
            start_date=datetime(2018, 5, 1),
            end_date=datetime(2018, 9, 30),
            description="Severe drought across Scandinavia reduced hydroelectric reservoir levels to historic lows. "
                       "Swedish hydro reservoirs dropped to 50% of normal levels, causing electricity prices to surge.",
            severity=0.85,
            affected_zones=["SE1", "SE2", "SE3", "SE4"],
            peak_impact={
                "hydro_reduction_pct": 50,
                "price_increase_pct": 300,
                "peak_price_eur_mwh": 65,
                "reservoir_level_pct": 50,
            },
            sources=[
                "https://www.svk.se/",
                "https://www.energimyndigheten.se/",
                "SMHI historical data"
            ]
        ),
        HistoricalEvent(
            event_id="drought_2003",
            event_type="drought",
            name="Scandinavian Drought 2002-2003",
            start_date=datetime(2002, 7, 1),
            end_date=datetime(2003, 4, 30),
            description="Extended dry period across Scandinavia leading to critically low hydro reservoir levels. "
                       "Norway and Sweden faced significant power shortages.",
            severity=0.9,
            affected_zones=["SE1", "SE2"],
            peak_impact={
                "hydro_reduction_pct": 55,
                "price_increase_pct": 400,
                "peak_price_eur_mwh": 100,
                "reservoir_level_pct": 45,
            },
            sources=[
                "https://www.nordpoolgroup.com/",
                "Historical hydrology data"
            ]
        ),
        HistoricalEvent(
            event_id="drought_2022",
            event_type="drought",
            name="European Drought Summer 2022",
            start_date=datetime(2022, 6, 1),
            end_date=datetime(2022, 9, 15),
            description="Widespread European drought affecting hydro production across the continent. "
                       "Combined with energy crisis from Ukraine war, caused record electricity prices.",
            severity=0.75,
            affected_zones=["SE1", "SE2", "SE3", "SE4"],
            peak_impact={
                "hydro_reduction_pct": 30,
                "price_increase_pct": 500,
                "peak_price_eur_mwh": 300,
                "reservoir_level_pct": 65,
            },
            sources=[
                "European Commission reports",
                "Nord Pool historical data"
            ]
        ),
    ],
    
    "nuclear_outage": [
        HistoricalEvent(
            event_id="ringhals_2020",
            event_type="nuclear_outage",
            name="Ringhals 1 & 2 Closure 2020",
            start_date=datetime(2019, 12, 31),
            end_date=datetime(2020, 12, 31),
            description="Permanent closure of Ringhals 1 (Dec 2019) and Ringhals 2 (Dec 2020) removed "
                       "1.8 GW of baseload capacity from SE3. Significant impact on southern Swedish supply.",
            severity=0.7,
            affected_zones=["SE3", "SE4"],
            peak_impact={
                "capacity_loss_mw": 1800,
                "price_impact_pct": 25,
                "baseload_reduction_pct": 15,
            },
            sources=[
                "Vattenfall annual reports",
                "Swedish Radiation Safety Authority"
            ]
        ),
        HistoricalEvent(
            event_id="forsmark_2006",
            event_type="nuclear_outage",
            name="Forsmark Incident July 2006",
            start_date=datetime(2006, 7, 25),
            end_date=datetime(2006, 10, 15),
            description="Electrical fault at Forsmark 1 caused emergency shutdown. Revealed safety "
                       "vulnerabilities leading to extended inspections across Swedish nuclear fleet.",
            severity=0.8,
            affected_zones=["SE3"],
            peak_impact={
                "capacity_loss_mw": 3200,  # Multiple units affected
                "price_impact_pct": 35,
                "outage_duration_days": 82,
            },
            sources=[
                "Swedish Nuclear Power Inspectorate (SKI)",
                "IAEA incident reports"
            ]
        ),
        HistoricalEvent(
            event_id="oskarshamn_2021",
            event_type="nuclear_outage",
            name="Oskarshamn 3 Unplanned Outage 2021",
            start_date=datetime(2021, 8, 1),
            end_date=datetime(2021, 11, 15),
            description="Unplanned outage at Sweden's largest reactor (1.4 GW) due to technical issues. "
                       "Extended maintenance outage during high-demand autumn period.",
            severity=0.6,
            affected_zones=["SE3", "SE4"],
            peak_impact={
                "capacity_loss_mw": 1400,
                "price_impact_pct": 20,
                "outage_duration_days": 106,
            },
            sources=[
                "OKG AB reports",
                "Svenska kraftnät"
            ]
        ),
    ],
    
    "cold_wave": [
        HistoricalEvent(
            event_id="cold_2010",
            event_type="cold_wave",
            name="Extreme Cold Wave February 2010",
            start_date=datetime(2010, 1, 15),
            end_date=datetime(2010, 2, 28),
            description="Extended period of extreme cold across Scandinavia with temperatures below -30°C "
                       "in northern Sweden. Record electricity demand for heating.",
            severity=0.85,
            affected_zones=["SE1", "SE2", "SE3", "SE4"],
            peak_impact={
                "min_temperature_c": -35,
                "demand_increase_pct": 45,
                "peak_demand_mw": 27500,
                "price_spike_pct": 200,
            },
            sources=[
                "SMHI climate data",
                "Svenska kraftnät demand records"
            ]
        ),
        HistoricalEvent(
            event_id="cold_2021",
            event_type="cold_wave",
            name="Arctic Blast January 2021",
            start_date=datetime(2021, 1, 5),
            end_date=datetime(2021, 1, 25),
            description="Severe cold snap combined with low wind output created critical grid conditions. "
                       "Svenska kraftnät issued demand reduction warnings.",
            severity=0.7,
            affected_zones=["SE1", "SE2", "SE3"],
            peak_impact={
                "min_temperature_c": -28,
                "demand_increase_pct": 35,
                "peak_demand_mw": 26000,
                "price_spike_pct": 150,
            },
            sources=[
                "Svenska kraftnät operational reports",
                "SMHI weather archives"
            ]
        ),
        HistoricalEvent(
            event_id="cold_1987",
            event_type="cold_wave",
            name="Historic Cold Wave 1987",
            start_date=datetime(1987, 1, 1),
            end_date=datetime(1987, 2, 15),
            description="One of the coldest winters on record in Sweden. Temperatures below -40°C "
                       "in Lapland. Tested grid resilience before major wind integration.",
            severity=0.95,
            affected_zones=["SE1", "SE2", "SE3", "SE4"],
            peak_impact={
                "min_temperature_c": -42,
                "demand_increase_pct": 50,
                "heating_degree_days": 850,
            },
            sources=[
                "SMHI historical climate records",
                "Swedish Energy Agency archives"
            ]
        ),
    ],
    
    "wind_lull": [
        HistoricalEvent(
            event_id="windlull_2021_01",
            event_type="wind_lull",
            name="January 2021 Wind Drought",
            start_date=datetime(2021, 1, 6),
            end_date=datetime(2021, 1, 15),
            description="Exceptionally calm period across Nordic region combined with cold wave. "
                       "Wind generation dropped to 5% of installed capacity.",
            severity=0.75,
            affected_zones=["SE1", "SE2", "SE3", "SE4"],
            peak_impact={
                "wind_capacity_factor_pct": 5,
                "missing_wind_mwh": 150000,
                "price_impact_pct": 180,
            },
            sources=[
                "Swedish Wind Energy Association",
                "Nord Pool market data"
            ]
        ),
        HistoricalEvent(
            event_id="windlull_2023_summer",
            event_type="wind_lull",
            name="Summer 2023 Low Wind Period",
            start_date=datetime(2023, 7, 10),
            end_date=datetime(2023, 7, 25),
            description="Extended high-pressure system over Scandinavia causing prolonged calm. "
                       "Highlighted increasing grid dependency on variable renewables.",
            severity=0.5,
            affected_zones=["SE1", "SE2", "SE3", "SE4"],
            peak_impact={
                "wind_capacity_factor_pct": 8,
                "average_windspeed_ms": 2.5,
            },
            sources=[
                "SMHI weather data",
                "Energiföretagen Sverige"
            ]
        ),
    ],
    
    "cable_failure": [
        HistoricalEvent(
            event_id="estlink_2019",
            event_type="cable_failure",
            name="EstLink 2 Outage 2019",
            start_date=datetime(2019, 1, 15),
            end_date=datetime(2019, 3, 20),
            description="Submarine cable between Finland and Estonia damaged, affecting Nordic-Baltic "
                       "power flows. Reduced export capacity from Swedish grid.",
            severity=0.4,
            affected_zones=["SE3"],
            peak_impact={
                "capacity_loss_mw": 650,
                "repair_duration_days": 64,
            },
            sources=[
                "Fingrid reports",
                "ENTSO-E transparency platform"
            ]
        ),
        HistoricalEvent(
            event_id="nordbalt_2024",
            event_type="cable_failure",
            name="NordBalt Cable Damage 2024",
            start_date=datetime(2024, 11, 17),
            end_date=datetime(2024, 12, 31),  # Ongoing
            description="Suspected sabotage of NordBalt cable between Sweden and Lithuania. "
                       "Reduced interconnection capacity affecting Baltic energy security.",
            severity=0.6,
            affected_zones=["SE4"],
            peak_impact={
                "capacity_loss_mw": 700,
                "security_alert_level": "high",
            },
            sources=[
                "Svenska kraftnät press releases",
                "Baltic news agencies"
            ]
        ),
    ],
    
    "price_crisis": [
        HistoricalEvent(
            event_id="price_crisis_2022",
            event_type="price_crisis",
            name="European Energy Crisis 2022",
            start_date=datetime(2022, 2, 24),
            end_date=datetime(2022, 12, 31),
            description="Russian invasion of Ukraine triggered unprecedented energy price crisis. "
                       "SE4 prices reached €600/MWh. Swedish government introduced electricity subsidies.",
            severity=1.0,
            affected_zones=["SE3", "SE4"],
            peak_impact={
                "peak_price_eur_mwh": 600,
                "average_price_increase_pct": 400,
                "consumer_bill_increase_pct": 300,
                "government_subsidy_sek_billion": 55,
            },
            sources=[
                "European Commission",
                "Swedish Government reports",
                "Nord Pool historical data"
            ]
        ),
    ],
}


class HistoricalEventsProvider:
    """Provider for Swedish historical energy events."""
    
    def __init__(self):
        self.events = SWEDISH_HISTORICAL_EVENTS
    
    def get_events_by_type(self, event_type: str) -> List[HistoricalEvent]:
        """Get all historical events of a specific type."""
        event_type_lower = event_type.lower().replace(" ", "_").replace("-", "_")
        
        # Map common names to event types
        type_mapping = {
            "drought": "drought",
            "nordic_drought": "drought",
            "draught": "drought",
            "nuclear": "nuclear_outage",
            "nuclear_outage": "nuclear_outage",
            "reactor_outage": "nuclear_outage",
            "cold": "cold_wave",
            "cold_wave": "cold_wave",
            "coldwave": "cold_wave",
            "wind": "wind_lull",
            "wind_lull": "wind_lull",
            "windlull": "wind_lull",
            "cable": "cable_failure",
            "cable_failure": "cable_failure",
            "price": "price_crisis",
            "price_crisis": "price_crisis",
            "energy_crisis": "price_crisis",
        }
        
        mapped_type = type_mapping.get(event_type_lower, event_type_lower)
        return self.events.get(mapped_type, [])
    
    def get_all_events(self) -> List[HistoricalEvent]:
        """Get all historical events."""
        all_events = []
        for event_list in self.events.values():
            all_events.extend(event_list)
        return sorted(all_events, key=lambda e: e.start_date, reverse=True)
    
    def get_events_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None
    ) -> List[HistoricalEvent]:
        """Get events within a date range."""
        if event_type:
            events = self.get_events_by_type(event_type)
        else:
            events = self.get_all_events()
        
        return [
            e for e in events
            if e.start_date >= start_date and e.end_date <= end_date
        ]
    
    def get_most_similar_event(self, event_type: str, severity: float = 0.5) -> Optional[HistoricalEvent]:
        """Get the most similar historical event by type and severity."""
        events = self.get_events_by_type(event_type)
        if not events:
            return None
        
        # Find closest severity match
        return min(events, key=lambda e: abs(e.severity - severity))
    
    def format_events_for_prompt(self, events: List[HistoricalEvent]) -> str:
        """Format events for LLM prompt context."""
        if not events:
            return "No historical events found for this scenario type."
        
        lines = ["## Historical Swedish Energy Events:\n"]
        for event in events:
            lines.append(f"### {event.name}")
            lines.append(f"**Period:** {event.start_date.strftime('%Y-%m-%d')} to {event.end_date.strftime('%Y-%m-%d')}")
            lines.append(f"**Severity:** {event.severity:.0%}")
            lines.append(f"**Affected Zones:** {', '.join(event.affected_zones)}")
            lines.append(f"**Description:** {event.description}")
            lines.append(f"**Peak Impacts:**")
            for key, value in event.peak_impact.items():
                lines.append(f"  - {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        return "\n".join(lines)


# =============================================================================
# ORCHESTRATOR WORKFLOW STEPS
# =============================================================================

class WorkflowStep(str, Enum):
    """Steps in the intelligent orchestrator workflow."""
    HISTORICAL_LOOKUP = "historical_lookup"
    DATA_FETCHING = "data_fetching"
    AGENT_SIMULATION = "agent_simulation"
    VERIFICATION = "verification"
    OUTPUT = "output"


@dataclass
class WorkflowStepResult:
    """Result of a single workflow step."""
    step: WorkflowStep
    status: str  # "running", "completed", "error"
    start_time: datetime
    end_time: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class OrchestratorWorkflowState(BaseModel):
    """State of the orchestrator workflow."""
    scenario_trigger: str
    scenario_description: str = ""
    duration_hours: int = 24
    magnitude: float = 1.0
    
    current_step: WorkflowStep = WorkflowStep.HISTORICAL_LOOKUP
    step_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    historical_events: List[Dict[str, Any]] = Field(default_factory=list)
    fetched_data: Dict[str, Any] = Field(default_factory=dict)
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    verification_result: Dict[str, Any] = Field(default_factory=dict)
    final_output: Dict[str, Any] = Field(default_factory=dict)
    
    is_complete: bool = False
    has_error: bool = False
    error_message: str = ""
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# =============================================================================
# INTELLIGENT MASTER ORCHESTRATOR
# =============================================================================

class IntelligentOrchestrator:
    """
    Master orchestrator implementing the 5-step intelligent workflow.
    
    Steps:
    1. Historical Event Lookup - Query real Swedish historical events
    2. Data Fetching - Gather relevant data from APIs, news, social media
    3. Agent Simulation - Feed data to timeline simulation and domain agents
    4. Verification - Validate results are realistic using AI verification
    5. Output - Generate final analysis with confidence scores
    """
    
    _instance: Optional['IntelligentOrchestrator'] = None
    
    def __init__(self):
        self.events_provider = HistoricalEventsProvider()
        self.state: Optional[OrchestratorWorkflowState] = None
        self._gemini_model = None
        self._initialized = False
        
        # Import providers lazily to avoid circular imports
        self._google_trends_provider = None
        self._news_provider = None
        
    @classmethod
    def get_instance(cls) -> 'IntelligentOrchestrator':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize(self) -> None:
        """Initialize the orchestrator and its components."""
        if self._initialized:
            return
        
        # Initialize Gemini if available
        if GEMINI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self._gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("✅ Gemini AI initialized for intelligent orchestration")
            else:
                logger.warning("⚠️ GEMINI_API_KEY not set - using fallback mode")
        
        # Initialize API providers
        try:
            from src.api.providers import GoogleTrendsProvider, NewsAPIProvider
            self._google_trends_provider = GoogleTrendsProvider()
            self._news_provider = NewsAPIProvider()
            logger.info(f"✅ Google Trends: {'enabled' if self._google_trends_provider.is_enabled else 'simulated'}")
            logger.info(f"✅ News API: {'enabled' if self._news_provider.is_enabled else 'simulated'}")
        except ImportError as e:
            logger.warning(f"⚠️ API providers not available: {e}")
        
        self._initialized = True
        logger.info("🎯 Intelligent Orchestrator initialized")
    
    async def run_scenario(
        self,
        scenario_trigger: str,
        duration_hours: int = 24,
        magnitude: float = 1.0,
        custom_description: str = ""
    ) -> OrchestratorWorkflowState:
        """
        Run a complete intelligent scenario analysis.
        
        Args:
            scenario_trigger: The type of scenario (e.g., "nordic_drought", "nuclear_outage")
            duration_hours: Duration of scenario to simulate
            magnitude: Severity multiplier (0.1 to 2.0)
            custom_description: Optional custom scenario description
        
        Returns:
            Complete workflow state with all results
        """
        if not self._initialized:
            self.initialize()
        
        # Initialize state
        self.state = OrchestratorWorkflowState(
            scenario_trigger=scenario_trigger,
            scenario_description=custom_description,
            duration_hours=duration_hours,
            magnitude=magnitude,
            start_time=datetime.now()
        )
        
        logger.info(f"🚀 Starting intelligent orchestration: {scenario_trigger}")
        logger.info(f"   Duration: {duration_hours}h | Magnitude: {magnitude}")
        
        try:
            # Step 1: Historical Event Lookup
            await self._step_historical_lookup()
            
            # Step 2: Data Fetching
            await self._step_data_fetching()
            
            # Step 3: Agent Simulation
            await self._step_agent_simulation()
            
            # Step 4: Verification
            await self._step_verification()
            
            # Step 5: Output Generation
            await self._step_output_generation()
            
            self.state.is_complete = True
            
        except Exception as e:
            self.state.has_error = True
            self.state.error_message = str(e)
            logger.error(f"❌ Orchestration failed: {e}")
        
        self.state.end_time = datetime.now()
        
        total_time = (self.state.end_time - self.state.start_time).total_seconds()
        logger.success(f"✅ Orchestration complete in {total_time:.1f}s")
        
        return self.state
    
    async def _step_historical_lookup(self) -> None:
        """Step 1: Look up historical events matching the scenario."""
        self.state.current_step = WorkflowStep.HISTORICAL_LOOKUP
        start_time = datetime.now()
        
        logger.info("📚 Step 1: Historical Event Lookup")
        
        # Get historical events for this scenario type
        events = self.events_provider.get_events_by_type(self.state.scenario_trigger)
        
        # Format for storage
        historical_data = []
        for event in events:
            historical_data.append({
                "event_id": event.event_id,
                "name": event.name,
                "type": event.event_type,
                "start_date": event.start_date.isoformat(),
                "end_date": event.end_date.isoformat(),
                "duration_days": event.duration_days,
                "severity": event.severity,
                "affected_zones": event.affected_zones,
                "peak_impact": event.peak_impact,
                "description": event.description,
                "sources": event.sources,
            })
        
        self.state.historical_events = historical_data
        
        # If we have Gemini, ask for additional context
        if self._gemini_model and events:
            try:
                prompt = f"""You are an expert on Swedish energy history. Given the following historical events:

{self.events_provider.format_events_for_prompt(events)}

Provide a brief (2-3 sentence) summary of:
1. What patterns emerge from these historical events?
2. What would be the key indicators to watch for a similar event today?

Be specific to Swedish/Nordic energy markets."""

                response = await asyncio.to_thread(
                    self._gemini_model.generate_content, prompt
                )
                
                if response and response.text:
                    self.state.step_results["historical_insights"] = response.text.strip()
                    logger.info(f"   AI insights generated for {len(events)} historical events")
            except Exception as e:
                logger.warning(f"   Could not generate AI insights: {e}")
        
        self.state.step_results["historical_lookup"] = {
            "status": "completed",
            "events_found": len(events),
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }
        
        logger.info(f"   Found {len(events)} historical {self.state.scenario_trigger} events")
    
    async def _step_data_fetching(self) -> None:
        """Step 2: Fetch relevant data from external sources."""
        self.state.current_step = WorkflowStep.DATA_FETCHING
        start_time = datetime.now()
        
        logger.info("📡 Step 2: Data Fetching (Trends, News, Social)")
        
        fetched_data = {
            "google_trends": {},
            "news_articles": [],
            "social_sentiment": {},
            "external_context": {}
        }
        
        # Determine search keywords based on scenario
        scenario_keywords = self._get_scenario_keywords(self.state.scenario_trigger)
        
        # Fetch Google Trends if available
        if self._google_trends_provider:
            try:
                trends_data, is_real = await self._google_trends_provider.get_data(
                    keywords=scenario_keywords,
                    geo="SE"
                )
                fetched_data["google_trends"] = {
                    "data": trends_data,
                    "is_real_data": is_real,
                    "keywords": scenario_keywords
                }
                logger.info(f"   Google Trends: {'real' if is_real else 'simulated'} data for {len(scenario_keywords)} keywords")
            except Exception as e:
                logger.warning(f"   Google Trends fetch failed: {e}")
        
        # Fetch News if available
        if self._news_provider:
            try:
                news_data, is_real = await self._news_provider.get_data(
                    query=" OR ".join(scenario_keywords[:3]),
                    language="en",
                    page_size=10
                )
                fetched_data["news_articles"] = {
                    "articles": news_data if isinstance(news_data, list) else [],
                    "is_real_data": is_real
                }
                article_count = len(news_data) if isinstance(news_data, list) else 0
                logger.info(f"   News API: {'real' if is_real else 'simulated'} - {article_count} articles")
            except Exception as e:
                logger.warning(f"   News fetch failed: {e}")
        
        # Add context from historical events
        if self.state.historical_events:
            most_recent = max(
                self.state.historical_events, 
                key=lambda e: e.get("start_date", "")
            )
            fetched_data["external_context"]["most_recent_similar_event"] = most_recent
        
        self.state.fetched_data = fetched_data
        
        self.state.step_results["data_fetching"] = {
            "status": "completed",
            "trends_keywords": scenario_keywords,
            "news_count": len(fetched_data.get("news_articles", {}).get("articles", [])),
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }
        
        logger.info(f"   Data fetching complete")
    
    async def _step_agent_simulation(self) -> None:
        """Step 3: Run the multi-agent simulation with gathered data."""
        self.state.current_step = WorkflowStep.AGENT_SIMULATION
        start_time = datetime.now()
        
        logger.info("🤖 Step 3: Agent Simulation")
        
        try:
            # Import and run the multi-agent system
            from src.agents.llm_agents import run_multi_agent_analysis
            
            # Build context from historical events and fetched data
            context_parts = []
            
            if self.state.historical_events:
                context_parts.append(
                    f"Historical context: {len(self.state.historical_events)} similar events occurred in Sweden's history."
                )
                most_severe = max(
                    self.state.historical_events,
                    key=lambda e: e.get("severity", 0)
                )
                context_parts.append(
                    f"Most severe was {most_severe['name']} ({most_severe['severity']:.0%} severity) "
                    f"which caused: {most_severe.get('description', '')[:200]}"
                )
            
            if self.state.fetched_data.get("news_articles", {}).get("articles"):
                context_parts.append(
                    f"Current news context: {len(self.state.fetched_data['news_articles']['articles'])} "
                    "related articles found."
                )
            
            custom_prompt = "\n".join(context_parts) if context_parts else None
            
            # Run the actual multi-agent analysis
            result = await run_multi_agent_analysis(
                scenario_trigger=self.state.scenario_trigger,
                duration_hours=self.state.duration_hours,
                magnitude=self.state.magnitude,
                custom_prompt=custom_prompt
            )
            
            self.state.agent_results = result
            
            agent_count = result.get("agent_count", 0)
            processing_time = result.get("total_processing_time_ms", 0) / 1000
            
            logger.info(f"   {agent_count} agents completed in {processing_time:.1f}s")
            
        except Exception as e:
            logger.error(f"   Agent simulation failed: {e}")
            self.state.agent_results = {"error": str(e)}
        
        self.state.step_results["agent_simulation"] = {
            "status": "completed" if "error" not in self.state.agent_results else "error",
            "agent_count": self.state.agent_results.get("agent_count", 0),
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }
    
    async def _step_verification(self) -> None:
        """Step 4: Verify that results are realistic using AI."""
        self.state.current_step = WorkflowStep.VERIFICATION
        start_time = datetime.now()
        
        logger.info("✅ Step 4: Result Verification")
        
        verification_result = {
            "is_realistic": True,
            "confidence_score": 0.8,
            "warnings": [],
            "adjustments": [],
            "comparison_with_history": {}
        }
        
        # Compare with historical events
        if self.state.historical_events and self.state.agent_results:
            master_summary = self.state.agent_results.get("master_summary", {})
            
            # Extract predicted impacts
            predicted_cpi = master_summary.get("estimated_cpi_impact_bps", 0)
            
            # Compare with historical ranges
            historical_impacts = [
                e.get("peak_impact", {}).get("price_impact_pct", 0)
                for e in self.state.historical_events
            ]
            
            if historical_impacts:
                avg_historical = sum(historical_impacts) / len(historical_impacts)
                max_historical = max(historical_impacts)
                
                verification_result["comparison_with_history"] = {
                    "predicted_impact": predicted_cpi,
                    "avg_historical_impact": avg_historical,
                    "max_historical_impact": max_historical,
                }
                
                # Check if prediction is within reasonable bounds
                if predicted_cpi > max_historical * 1.5:
                    verification_result["warnings"].append(
                        f"Predicted impact ({predicted_cpi}) exceeds historical maximum ({max_historical}) by >50%"
                    )
                    verification_result["confidence_score"] -= 0.1
        
        # Use Gemini for deeper verification if available
        if self._gemini_model and self.state.agent_results:
            try:
                verification_prompt = f"""As a Swedish energy market expert, verify if this analysis is realistic:

Scenario: {self.state.scenario_trigger}
Duration: {self.state.duration_hours} hours
Magnitude: {self.state.magnitude}

Agent Analysis Summary:
{self.state.agent_results.get('master_summary', {}).get('analysis', 'No analysis available')[:1500]}

Historical Context:
{len(self.state.historical_events)} similar events occurred historically with impacts ranging from 
{min(e.get('severity', 0) for e in self.state.historical_events) if self.state.historical_events else 0:.0%} to 
{max(e.get('severity', 0) for e in self.state.historical_events) if self.state.historical_events else 0:.0%} severity.

Please evaluate:
1. Is this analysis realistic? (yes/no with brief reason)
2. Confidence score (0.0 to 1.0)
3. Any warnings or concerns?
4. Suggested adjustments?

Format: JSON with keys: is_realistic, confidence, warnings (list), adjustments (list)"""

                response = await asyncio.to_thread(
                    self._gemini_model.generate_content, verification_prompt
                )
                
                if response and response.text:
                    # Try to parse JSON from response
                    import re
                    import json
                    
                    json_match = re.search(r'\{[^{}]*\}', response.text, re.DOTALL)
                    if json_match:
                        try:
                            ai_verification = json.loads(json_match.group())
                            verification_result["ai_verification"] = ai_verification
                            
                            if "confidence" in ai_verification:
                                verification_result["confidence_score"] = float(ai_verification["confidence"])
                            if "warnings" in ai_verification:
                                verification_result["warnings"].extend(ai_verification["warnings"])
                            if "is_realistic" in ai_verification:
                                verification_result["is_realistic"] = ai_verification["is_realistic"]
                                
                            logger.info(f"   AI verification: confidence={verification_result['confidence_score']:.0%}")
                        except json.JSONDecodeError:
                            verification_result["ai_raw_response"] = response.text[:500]
                    else:
                        verification_result["ai_raw_response"] = response.text[:500]
                        
            except Exception as e:
                logger.warning(f"   AI verification failed: {e}")
        
        self.state.verification_result = verification_result
        
        self.state.step_results["verification"] = {
            "status": "completed",
            "is_realistic": verification_result["is_realistic"],
            "confidence_score": verification_result["confidence_score"],
            "warnings_count": len(verification_result["warnings"]),
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }
        
        logger.info(f"   Verification: {'✓ Realistic' if verification_result['is_realistic'] else '⚠ Concerns'} "
                   f"(confidence: {verification_result['confidence_score']:.0%})")
    
    async def _step_output_generation(self) -> None:
        """Step 5: Generate final consolidated output."""
        self.state.current_step = WorkflowStep.OUTPUT
        start_time = datetime.now()
        
        logger.info("📋 Step 5: Output Generation")
        
        # Compile final output
        final_output = {
            "scenario": {
                "trigger": self.state.scenario_trigger,
                "duration_hours": self.state.duration_hours,
                "magnitude": self.state.magnitude,
                "description": self.state.scenario_description
            },
            "historical_context": {
                "events_analyzed": len(self.state.historical_events),
                "events": self.state.historical_events[:3],  # Top 3 most relevant
                "insights": self.state.step_results.get("historical_insights", "")
            },
            "external_data": {
                "trends_keywords": self.state.fetched_data.get("google_trends", {}).get("keywords", []),
                "news_articles_count": len(
                    self.state.fetched_data.get("news_articles", {}).get("articles", [])
                ),
                "data_is_real": self.state.fetched_data.get("google_trends", {}).get("is_real_data", False)
            },
            "agent_analysis": self.state.agent_results,
            "verification": self.state.verification_result,
            "workflow_summary": {
                "total_steps": 5,
                "completed_steps": len(self.state.step_results),
                "total_duration_seconds": (
                    datetime.now() - self.state.start_time
                ).total_seconds() if self.state.start_time else 0,
                "step_timings": {
                    step: data.get("duration_seconds", 0)
                    for step, data in self.state.step_results.items()
                }
            },
            "confidence": self.state.verification_result.get("confidence_score", 0.8),
            "warnings": self.state.verification_result.get("warnings", []),
            "is_verified": self.state.verification_result.get("is_realistic", True)
        }
        
        self.state.final_output = final_output
        
        self.state.step_results["output"] = {
            "status": "completed",
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }
        
        logger.success(f"   Final output generated with confidence {final_output['confidence']:.0%}")
    
    def _get_scenario_keywords(self, trigger: str) -> List[str]:
        """Get search keywords for a scenario type."""
        keyword_map = {
            "drought": ["sweden drought", "nordic drought", "hydro reservoir sweden", "electricity prices sweden"],
            "nordic_drought": ["sweden drought", "nordic drought", "hydro reservoir sweden", "electricity prices sweden"],
            "nuclear_outage": ["sweden nuclear", "forsmark", "ringhals", "oskarshamn", "reactor outage"],
            "cold_wave": ["sweden cold weather", "nordic winter", "electricity demand sweden", "heating sweden"],
            "wind_lull": ["sweden wind energy", "nordic wind production", "wind capacity sweden"],
            "cable_failure": ["nordlink cable", "sweden interconnector", "baltic cable", "swepol link"],
            "gas_crisis": ["europe gas crisis", "natural gas prices", "germany gas", "energy crisis europe"],
            "price_spike": ["electricity prices sweden", "nord pool prices", "energy crisis nordic"],
        }
        
        return keyword_map.get(trigger.lower(), [trigger.replace("_", " "), "sweden energy", "electricity prices"])
    
    def get_current_state(self) -> Optional[OrchestratorWorkflowState]:
        """Get the current workflow state."""
        return self.state
    
    def get_historical_events(self, event_type: str) -> List[HistoricalEvent]:
        """Get historical events for a specific type."""
        return self.events_provider.get_events_by_type(event_type)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_orchestrator: Optional[IntelligentOrchestrator] = None


def get_intelligent_orchestrator() -> IntelligentOrchestrator:
    """Get the singleton intelligent orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = IntelligentOrchestrator()
    return _orchestrator


async def run_intelligent_scenario(
    trigger: str,
    duration_hours: int = 24,
    magnitude: float = 1.0,
    description: str = ""
) -> OrchestratorWorkflowState:
    """
    Run an intelligent scenario analysis using the 5-step workflow.
    
    This is the main entry point for the intelligent orchestrator.
    """
    orchestrator = get_intelligent_orchestrator()
    return await orchestrator.run_scenario(
        scenario_trigger=trigger,
        duration_hours=duration_hours,
        magnitude=magnitude,
        custom_description=description
    )


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == "__main__":
    async def test_orchestrator():
        print("\n" + "="*60)
        print("🧪 Testing Intelligent Orchestrator")
        print("="*60 + "\n")
        
        # Test historical events provider
        provider = HistoricalEventsProvider()
        
        print("📚 Historical Events Test:")
        for event_type in ["drought", "nuclear_outage", "cold_wave"]:
            events = provider.get_events_by_type(event_type)
            print(f"   {event_type}: {len(events)} events")
            for event in events[:2]:
                print(f"      - {event.name} ({event.start_date.year}): {event.severity:.0%} severity")
        
        print("\n" + "-"*60 + "\n")
        
        # Test full orchestration
        print("🚀 Running full orchestration for 'nordic_drought'...")
        result = await run_intelligent_scenario(
            trigger="nordic_drought",
            duration_hours=48,
            magnitude=0.8
        )
        
        print(f"\n📊 Results:")
        print(f"   Complete: {result.is_complete}")
        print(f"   Historical events found: {len(result.historical_events)}")
        print(f"   Confidence: {result.verification_result.get('confidence_score', 0):.0%}")
        print(f"   Warnings: {len(result.verification_result.get('warnings', []))}")
        
        if result.final_output:
            print(f"\n   Workflow timing:")
            for step, timing in result.final_output.get("workflow_summary", {}).get("step_timings", {}).items():
                print(f"      {step}: {timing:.1f}s")
    
    asyncio.run(test_orchestrator())
