"""
Multi-Agent Orchestration System for Swedish Energy Digital Twin.

Hierarchical agent architecture:
- Master Orchestrator (GameMaster): Coordinates all sub-orchestrators
- Domain Orchestrators: MECE-structured coverage of all scenario domains
- Specialist Agents: Individual agents that simulate specific aspects

Each agent can:
- Make API calls (Google Trends, News, Weather, etc.)
- Simulate being in their designated scenario
- Report predictions to parent orchestrator
- Contribute to cascading domino effects
"""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Any, Callable
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import httpx
from loguru import logger
import random
import math

# Import the new API abstraction
from src.api.providers import (
    get_registry,
    get_api,
    fetch_with_fallback,
    is_api_enabled,
    get_api_status,
    APIRegistry,
    BaseAPIProvider,
)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class AgentRole(str, Enum):
    """Role of an agent in the hierarchy."""
    MASTER_ORCHESTRATOR = "master_orchestrator"
    DOMAIN_ORCHESTRATOR = "domain_orchestrator"
    SPECIALIST_AGENT = "specialist_agent"
    DATA_AGENT = "data_agent"


class AgentStatus(str, Enum):
    """Current status of an agent."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class DomainCategory(str, Enum):
    """MECE domain categories for scenario coverage."""
    # Supply-side domains
    PRODUCTION_NUCLEAR = "production_nuclear"
    PRODUCTION_HYDRO = "production_hydro"
    PRODUCTION_WIND = "production_wind"
    PRODUCTION_SOLAR = "production_solar"
    PRODUCTION_THERMAL = "production_thermal"
    
    # Demand-side domains
    DEMAND_INDUSTRIAL = "demand_industrial"
    DEMAND_RESIDENTIAL = "demand_residential"
    DEMAND_COMMERCIAL = "demand_commercial"
    DEMAND_TRANSPORT = "demand_transport"
    
    # Infrastructure domains
    GRID_TRANSMISSION = "grid_transmission"
    GRID_INTERCONNECTION = "grid_interconnection"
    GRID_STORAGE = "grid_storage"
    
    # External factors
    WEATHER_CLIMATE = "weather_climate"
    GEOPOLITICS = "geopolitics"
    MARKETS_COMMODITIES = "markets_commodities"
    REGULATION_POLICY = "regulation_policy"
    
    # Economic domains
    INFLATION_PRICES = "inflation_prices"
    CONSUMER_BEHAVIOR = "consumer_behavior"
    INVESTMENT_FINANCE = "investment_finance"


class SignalType(str, Enum):
    """Types of signals agents can emit."""
    PRICE_MOVEMENT = "price_movement"
    SUPPLY_CHANGE = "supply_change"
    DEMAND_CHANGE = "demand_change"
    RISK_ALERT = "risk_alert"
    TREND_SHIFT = "trend_shift"
    CORRELATION = "correlation"
    ANOMALY = "anomaly"


# =============================================================================
# DATA MODELS
# =============================================================================

class AgentMessage(BaseModel):
    """Message passed between agents."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_id: str
    receiver_id: Optional[str] = None  # None = broadcast
    message_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)  # 1=low, 10=critical
    requires_response: bool = False


class AgentSignal(BaseModel):
    """Signal emitted by an agent about observed phenomena."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    signal_type: SignalType
    domain: DomainCategory
    
    # Signal details
    metric: str
    current_value: float
    baseline_value: float
    change_pct: float
    
    # Confidence and source
    confidence: float = Field(ge=0, le=1, default=0.7)
    data_source: str = "simulation"
    is_api_backed: bool = False
    
    # Impact assessment
    severity: int = Field(ge=1, le=10, default=5)
    affected_zones: list[str] = Field(default_factory=list)
    propagation_probability: float = Field(ge=0, le=1, default=0.5)


class AgentPrediction(BaseModel):
    """Prediction made by an agent."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    domain: DomainCategory
    
    # Prediction details
    metric: str
    predicted_value: float
    prediction_range: tuple[float, float]  # (lower, upper)
    horizon_hours: int
    
    # Confidence and methodology
    confidence: float = Field(ge=0, le=1)
    methodology: str = "simulation"
    data_sources_used: list[str] = Field(default_factory=list)
    
    # Dependencies
    depends_on_predictions: list[str] = Field(default_factory=list)
    
    # CPI impact
    estimated_cpi_impact_bps: Optional[float] = None


class AgentNode(BaseModel):
    """Representation of an agent for visualization."""
    id: str
    name: str
    role: AgentRole
    domain: Optional[DomainCategory] = None
    status: AgentStatus = AgentStatus.IDLE
    parent_id: Optional[str] = None
    children_ids: list[str] = Field(default_factory=list)
    
    # Metrics
    signals_emitted: int = 0
    predictions_made: int = 0
    api_calls_made: int = 0
    last_activity: Optional[datetime] = None
    
    # Position for visualization
    x: float = 0.0
    y: float = 0.0
    level: int = 0


class SimulationContext(BaseModel):
    """Context passed to agents for simulation."""
    scenario_name: str
    scenario_description: str
    start_time: datetime
    current_time: datetime
    end_time: datetime
    
    # Initial conditions
    initial_prices: dict[str, float] = Field(default_factory=dict)  # zone -> price
    initial_generation: dict[str, float] = Field(default_factory=dict)  # source -> MW
    initial_demand: dict[str, float] = Field(default_factory=dict)  # zone -> MW
    
    # External triggers
    trigger_event: str
    trigger_magnitude: float = 1.0  # 1.0 = baseline
    
    # Propagation settings
    allow_cascades: bool = True
    max_cascade_depth: int = 5


# =============================================================================
# API DATA PROVIDERS
# =============================================================================

class APIProvider(ABC):
    """Base class for external API data providers."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._cache: dict[str, tuple[datetime, Any]] = {}
        self._call_count = 0
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    async def _cached_get(self, url: str, params: dict = None, ttl_seconds: int = 3600) -> dict:
        """Make a cached GET request."""
        cache_key = f"{url}_{params}"
        
        # Check cache
        if cache_key in self._cache:
            cached_time, data = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=ttl_seconds):
                return data
        
        # Make request
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                self._cache[cache_key] = (datetime.now(), data)
                self._call_count += 1
                return data
        except Exception as e:
            logger.warning(f"{self.name} API error: {e}")
            return {}


class GoogleTrendsProvider(APIProvider):
    """
    Google Trends data provider.
    
    Note: Official API requires registration. This uses SerpAPI or similar.
    For demo, we simulate realistic trends data.
    """
    
    @property
    def name(self) -> str:
        return "Google Trends"
    
    async def get_interest_over_time(
        self,
        keywords: list[str],
        geo: str = "SE",
        timeframe: str = "today 3-m"
    ) -> dict[str, list[dict]]:
        """
        Get search interest over time for keywords.
        
        Returns interest values (0-100) over time for each keyword.
        """
        # In production, would call actual API
        # For demo, simulate realistic trends
        
        results = {}
        base_date = datetime.now() - timedelta(days=90)
        
        for keyword in keywords:
            trend_data = []
            # Generate realistic trend pattern
            base_interest = random.randint(20, 60)
            trend = random.uniform(-0.5, 0.5)  # Slight trend
            
            for day in range(90):
                date = base_date + timedelta(days=day)
                # Add seasonality, trend, and noise
                seasonal = 10 * math.sin(day * 2 * math.pi / 30)  # Monthly cycle
                weekly = 5 * math.sin(day * 2 * math.pi / 7)  # Weekly cycle
                value = base_interest + trend * day + seasonal + weekly + random.gauss(0, 5)
                value = max(0, min(100, value))
                
                trend_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "value": round(value),
                    "keyword": keyword
                })
            
            results[keyword] = trend_data
        
        self._call_count += 1
        return results
    
    async def get_related_queries(self, keyword: str, geo: str = "SE") -> dict:
        """Get related queries for a keyword."""
        # Simulated related queries
        energy_related = {
            "electricity price": ["elpris", "elpriser", "vattenfall", "fortum", "tibber"],
            "energy crisis": ["energikris", "gaspris", "elkostnad", "spara el"],
            "nuclear power": ["kärnkraft", "ringhals", "forsmark", "oskarshamn"],
            "wind power": ["vindkraft", "vindkraftverk", "havsbaserad vindkraft"],
            "solar panels": ["solceller", "solpanel pris", "solenergi"],
        }
        
        self._call_count += 1
        return {
            "rising": energy_related.get(keyword.lower(), ["related query 1", "related query 2"]),
            "top": energy_related.get(keyword.lower(), ["top query 1", "top query 2"])
        }


class NewsAPIProvider(APIProvider):
    """News API for sentiment and headline analysis."""
    
    BASE_URL = "https://newsapi.org/v2"
    
    @property
    def name(self) -> str:
        return "NewsAPI"
    
    async def get_headlines(
        self,
        query: str,
        country: str = "se",
        category: str = "business"
    ) -> list[dict]:
        """Get news headlines matching query."""
        
        if self.api_key:
            try:
                data = await self._cached_get(
                    f"{self.BASE_URL}/everything",
                    params={
                        "q": query,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "apiKey": self.api_key
                    }
                )
                return data.get("articles", [])[:10]
            except Exception:
                pass
        
        # Simulated headlines
        headlines = [
            {"title": f"Energy markets react to {query} developments", "sentiment": random.uniform(-0.3, 0.3)},
            {"title": f"Nordic electricity prices shift amid {query}", "sentiment": random.uniform(-0.5, 0.5)},
            {"title": f"Analysts predict impact of {query} on Swedish grid", "sentiment": random.uniform(-0.2, 0.4)},
        ]
        self._call_count += 1
        return headlines


class WeatherAPIProvider(APIProvider):
    """Weather data for demand and renewable forecasting."""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # Swedish city coordinates
    SWEDISH_CITIES = {
        "SE1": {"name": "Luleå", "lat": 65.58, "lon": 22.15},
        "SE2": {"name": "Sundsvall", "lat": 62.39, "lon": 17.31},
        "SE3": {"name": "Stockholm", "lat": 59.33, "lon": 18.07},
        "SE4": {"name": "Malmö", "lat": 55.60, "lon": 13.00},
    }
    
    @property
    def name(self) -> str:
        return "OpenWeatherMap"
    
    async def get_weather(self, zone: str) -> dict:
        """Get current weather for a zone."""
        city = self.SWEDISH_CITIES.get(zone, self.SWEDISH_CITIES["SE3"])
        
        if self.api_key:
            try:
                data = await self._cached_get(
                    f"{self.BASE_URL}/weather",
                    params={
                        "lat": city["lat"],
                        "lon": city["lon"],
                        "appid": self.api_key,
                        "units": "metric"
                    }
                )
                return data
            except Exception:
                pass
        
        # Simulated weather
        month = datetime.now().month
        # Seasonal temperature adjustment
        base_temp = 10 - abs(month - 7) * 3  # Peak in July
        lat_adjustment = (city["lat"] - 59) * -0.5  # Colder in north
        
        self._call_count += 1
        return {
            "temp": round(base_temp + lat_adjustment + random.gauss(0, 3), 1),
            "wind_speed": round(random.uniform(2, 12), 1),
            "clouds": random.randint(20, 80),
            "description": random.choice(["clear sky", "partly cloudy", "overcast", "light rain"])
        }
    
    async def get_forecast(self, zone: str, hours: int = 48) -> list[dict]:
        """Get weather forecast."""
        current = await self.get_weather(zone)
        forecast = []
        
        base_temp = current["temp"]
        for h in range(hours):
            # Add daily cycle and random variation
            hour_of_day = (datetime.now().hour + h) % 24
            daily_variation = 4 * math.sin((hour_of_day - 6) * math.pi / 12)
            
            forecast.append({
                "hour": h,
                "temp": round(base_temp + daily_variation + random.gauss(0, 1), 1),
                "wind_speed": round(max(0, current["wind_speed"] + random.gauss(0, 2)), 1),
                "clouds": min(100, max(0, current["clouds"] + random.randint(-20, 20)))
            })
        
        return forecast


class CommodityPriceProvider(APIProvider):
    """Commodity prices (oil, gas, coal)."""
    
    @property
    def name(self) -> str:
        return "Commodity Prices"
    
    async def get_prices(self) -> dict[str, float]:
        """Get current commodity prices."""
        # Simulated prices (would use real API in production)
        self._call_count += 1
        return {
            "brent_crude_usd": 75.0 + random.gauss(0, 5),
            "natural_gas_eur_mwh": 35.0 + random.gauss(0, 8),
            "coal_usd_ton": 120.0 + random.gauss(0, 10),
            "co2_eur_ton": 65.0 + random.gauss(0, 5),
        }


# =============================================================================
# BASE AGENT CLASS
# =============================================================================

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    # Shared API registry for all agents
    _api_registry: Optional[APIRegistry] = None
    
    @classmethod
    def get_api_registry(cls) -> APIRegistry:
        """Get or initialize the shared API registry."""
        if cls._api_registry is None:
            cls._api_registry = get_registry()
            cls._api_registry.initialize()
        return cls._api_registry
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: AgentRole,
        domain: Optional[DomainCategory] = None,
        parent: Optional[BaseAgent] = None
    ):
        self.id = agent_id
        self.name = name
        self.role = role
        self.domain = domain
        self.parent = parent
        self.children: list[BaseAgent] = []
        self.status = AgentStatus.IDLE
        
        # Communication
        self.inbox: list[AgentMessage] = []
        self.outbox: list[AgentMessage] = []
        self.signals: list[AgentSignal] = []
        self.predictions: list[AgentPrediction] = []
        
        # Legacy API providers (for backward compatibility)
        self.api_providers: dict[str, APIProvider] = {}
        
        # Metrics
        self.api_call_count = 0
        self.last_activity = None
        
        # State
        self.current_context: Optional[SimulationContext] = None
        self._running = False
    
    def add_child(self, child: BaseAgent) -> None:
        """Add a child agent."""
        child.parent = self
        self.children.append(child)
    
    def add_api_provider(self, name: str, provider: APIProvider) -> None:
        """Add an API provider to this agent."""
        self.api_providers[name] = provider
    
    def to_node(self, level: int = 0) -> AgentNode:
        """Convert to visualization node."""
        return AgentNode(
            id=self.id,
            name=self.name,
            role=self.role,
            domain=self.domain,
            status=self.status,
            parent_id=self.parent.id if self.parent else None,
            children_ids=[c.id for c in self.children],
            signals_emitted=len(self.signals),
            predictions_made=len(self.predictions),
            api_calls_made=self.api_call_count,
            last_activity=self.last_activity,
            level=level
        )
    
    def get_all_nodes(self, level: int = 0) -> list[AgentNode]:
        """Get all nodes in subtree."""
        nodes = [self.to_node(level)]
        for child in self.children:
            nodes.extend(child.get_all_nodes(level + 1))
        return nodes
    
    def emit_signal(self, signal: AgentSignal) -> None:
        """Emit a signal."""
        self.signals.append(signal)
        self.last_activity = datetime.utcnow()
        
        # Propagate to parent
        if self.parent:
            self.parent.receive_signal(signal)
    
    def receive_signal(self, signal: AgentSignal) -> None:
        """Receive a signal from child."""
        self.signals.append(signal)
    
    def make_prediction(self, prediction: AgentPrediction) -> None:
        """Record a prediction."""
        self.predictions.append(prediction)
        self.last_activity = datetime.utcnow()
    
    async def call_api(self, provider_name: str, method: str = None, **kwargs) -> Any:
        """
        Call an API provider method using the centralized registry.
        
        The API registry automatically:
        - Uses real API if key is configured
        - Falls back to simulated data if no key
        - Handles rate limiting and caching
        
        Args:
            provider_name: Name of the API (e.g., 'weather', 'news', 'google_trends')
            method: Method name to call (optional, uses 'get_data' if not specified)
            **kwargs: Arguments to pass to the API method
            
        Returns:
            API response data (real or simulated)
        """
        registry = self.get_api_registry()
        provider = registry.get_provider(provider_name)
        
        if provider is None:
            # Fall back to legacy providers
            if provider_name in self.api_providers:
                legacy_provider = self.api_providers[provider_name]
                method_func = getattr(legacy_provider, method, None)
                if method_func:
                    try:
                        result = await method_func(**kwargs)
                        self.api_call_count += 1
                        self.last_activity = datetime.utcnow()
                        return result
                    except Exception as e:
                        logger.error(f"Agent {self.id}: Legacy API call failed: {e}")
                        return None
            
            logger.warning(f"Agent {self.id}: API provider '{provider_name}' not found")
            return None
        
        try:
            # Use new registry - get_data returns (data, is_real)
            data, is_real = await provider.get_data(**kwargs)
            self.api_call_count += 1
            self.last_activity = datetime.utcnow()
            
            if not is_real:
                logger.debug(f"Agent {self.id}: Using simulated data for {provider_name}")
            
            return data
        except Exception as e:
            logger.error(f"Agent {self.id}: API call to {provider_name} failed: {e}")
            return None
    
    async def call_api_with_status(self, provider_name: str, **kwargs) -> tuple[Any, bool]:
        """
        Call API and return both data and whether it's real or simulated.
        
        Returns:
            Tuple of (data, is_real_data)
        """
        registry = self.get_api_registry()
        provider = registry.get_provider(provider_name)
        
        if provider is None:
            return None, False
        
        try:
            data, is_real = await provider.get_data(**kwargs)
            self.api_call_count += 1
            self.last_activity = datetime.utcnow()
            return data, is_real
        except Exception as e:
            logger.error(f"Agent {self.id}: API call failed: {e}")
            return None, False
    
    def is_api_enabled(self, provider_name: str) -> bool:
        """Check if an API provider is enabled (has valid key)."""
        registry = self.get_api_registry()
        provider = registry.get_provider(provider_name)
        return provider.is_enabled if provider else False
    
    def get_api_status(self) -> dict:
        """Get status of all API providers."""
        return self.get_api_registry().get_status_report()
    
    @abstractmethod
    async def initialize(self, context: SimulationContext) -> None:
        """Initialize the agent with simulation context."""
        pass
    
    @abstractmethod
    async def simulate_step(self, step: int, delta_hours: float) -> None:
        """Execute one simulation step."""
        pass
    
    @abstractmethod
    async def aggregate_predictions(self) -> list[AgentPrediction]:
        """Aggregate predictions from self and children."""
        pass
    
    async def run_simulation(self, context: SimulationContext, steps: int = 24) -> list[AgentPrediction]:
        """Run full simulation."""
        self._running = True
        self.status = AgentStatus.INITIALIZING
        self.current_context = context
        
        try:
            # Initialize self and children
            await self.initialize(context)
            for child in self.children:
                await child.run_simulation(context, steps)
            
            self.status = AgentStatus.RUNNING
            
            # Run simulation steps
            delta_hours = (context.end_time - context.start_time).total_seconds() / 3600 / steps
            for step in range(steps):
                if not self._running:
                    break
                await self.simulate_step(step, delta_hours)
            
            self.status = AgentStatus.COMPLETED
            
            # Aggregate all predictions
            return await self.aggregate_predictions()
            
        except Exception as e:
            logger.error(f"Agent {self.id} simulation failed: {e}")
            self.status = AgentStatus.ERROR
            return []
        finally:
            self._running = False
    
    def stop(self) -> None:
        """Stop the simulation."""
        self._running = False
        for child in self.children:
            child.stop()


# =============================================================================
# SPECIALIST AGENTS
# =============================================================================

class SpecialistAgent(BaseAgent):
    """
    Specialist agent that simulates a specific domain aspect.
    
    Can make API calls and generate signals/predictions.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        domain: DomainCategory,
        parent: Optional[BaseAgent] = None
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            role=AgentRole.SPECIALIST_AGENT,
            domain=domain,
            parent=parent
        )
        
        # Domain-specific parameters
        self.base_value = 0.0
        self.volatility = 0.1
        self.trend = 0.0
        self.sensitivity_to_trigger = 1.0
    
    async def initialize(self, context: SimulationContext) -> None:
        """Initialize with context-specific parameters."""
        self.status = AgentStatus.INITIALIZING
        
        # Set base values based on domain
        if self.domain in [DomainCategory.PRODUCTION_NUCLEAR, DomainCategory.PRODUCTION_HYDRO]:
            self.base_value = context.initial_generation.get("nuclear", 6000) if "NUCLEAR" in self.domain.value else context.initial_generation.get("hydro", 8000)
            self.volatility = 0.05  # Stable
        elif self.domain in [DomainCategory.PRODUCTION_WIND, DomainCategory.PRODUCTION_SOLAR]:
            self.base_value = context.initial_generation.get("wind", 3000)
            self.volatility = 0.3  # High variability
        elif "DEMAND" in self.domain.value:
            zone = self.domain.value.split("_")[1][:3].upper()
            self.base_value = context.initial_demand.get(zone, 5000)
            self.volatility = 0.15
        
        # Fetch initial API data using the new registry
        # Google Trends for market sentiment
        trends = await self.call_api("google_trends", 
                                     keywords=[self.name.lower().replace(" ", "+")])
        if trends:
            logger.debug(f"{self.name}: Got trends data")
        
        # Weather data for weather-related domains
        if "WEATHER" in self.domain.value or "WIND" in self.domain.value or "SOLAR" in self.domain.value:
            weather = await self.call_api("weather", zone="SE3")
            if weather:
                logger.debug(f"{self.name}: Weather = {weather.get('temp')}°C")
    
    async def simulate_step(self, step: int, delta_hours: float) -> None:
        """Simulate one step in this domain."""
        if not self.current_context:
            return
        
        # Calculate value change
        trigger_impact = 0.0
        if self._is_affected_by_trigger():
            # Apply trigger effect
            trigger_impact = self._calculate_trigger_impact(step)
        
        # Add random variation
        random_change = random.gauss(0, self.volatility * self.base_value * 0.01)
        
        # Calculate new value
        new_value = self.base_value * (1 + self.trend * delta_hours) + trigger_impact + random_change
        
        # Check for significant changes
        change_pct = (new_value - self.base_value) / self.base_value * 100 if self.base_value != 0 else 0
        
        if abs(change_pct) > 5:  # Significant change
            self.emit_signal(AgentSignal(
                agent_id=self.id,
                signal_type=SignalType.SUPPLY_CHANGE if "PRODUCTION" in self.domain.value else SignalType.DEMAND_CHANGE,
                domain=self.domain,
                metric=f"{self.domain.value}_level",
                current_value=new_value,
                baseline_value=self.base_value,
                change_pct=change_pct,
                confidence=0.7 + random.uniform(0, 0.2),
                severity=min(10, int(abs(change_pct) / 5)),
                affected_zones=["SE1", "SE2", "SE3", "SE4"] if abs(change_pct) > 15 else ["SE3"]
            ))
        
        self.base_value = new_value
    
    def _is_affected_by_trigger(self) -> bool:
        """Check if this domain is affected by the trigger event."""
        if not self.current_context:
            return False
        
        trigger = self.current_context.trigger_event.lower()
        domain = self.domain.value.lower()
        
        # Map triggers to affected domains
        trigger_domain_map = {
            "drought": ["hydro", "weather"],
            "nuclear": ["nuclear"],
            "cold": ["demand", "weather"],
            "wind": ["wind", "weather"],
            "gas": ["thermal", "commodities"],
            "cable": ["interconnection", "transmission"],
            "crisis": ["geopolitics", "commodities", "markets"],
        }
        
        for key, domains in trigger_domain_map.items():
            if key in trigger:
                for d in domains:
                    if d in domain:
                        return True
        return False
    
    def _calculate_trigger_impact(self, step: int) -> float:
        """Calculate impact of trigger on this domain."""
        if not self.current_context:
            return 0.0
        
        magnitude = self.current_context.trigger_magnitude
        
        # Impact grows over time then stabilizes
        time_factor = 1 - math.exp(-step / 10)  # Asymptotic to 1
        
        # Domain-specific impact direction
        if "PRODUCTION" in self.domain.value:
            # Production typically decreases during crises
            return -self.base_value * 0.2 * magnitude * time_factor * self.sensitivity_to_trigger
        else:
            # Demand might increase (heating) or decrease (price response)
            return self.base_value * 0.1 * magnitude * time_factor * self.sensitivity_to_trigger
    
    async def aggregate_predictions(self) -> list[AgentPrediction]:
        """Generate prediction based on simulation."""
        if not self.current_context:
            return []
        
        # Make prediction based on simulated state
        prediction = AgentPrediction(
            agent_id=self.id,
            domain=self.domain,
            metric=f"{self.domain.value}_forecast",
            predicted_value=self.base_value,
            prediction_range=(self.base_value * 0.9, self.base_value * 1.1),
            horizon_hours=24,
            confidence=0.6 + random.uniform(0, 0.3),
            methodology="simulation_with_api_data",
            data_sources_used=[p.name for p in self.api_providers.values()]
        )
        
        self.make_prediction(prediction)
        return [prediction]


# =============================================================================
# DOMAIN ORCHESTRATOR
# =============================================================================

class DomainOrchestrator(BaseAgent):
    """
    Domain orchestrator that manages specialist agents in one domain area.
    
    Coordinates MECE coverage of a specific domain.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        domain: DomainCategory,
        parent: Optional[BaseAgent] = None
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            role=AgentRole.DOMAIN_ORCHESTRATOR,
            domain=domain,
            parent=parent
        )
        
        self.domain_weight = 1.0  # Importance weight for this domain
        self.cross_domain_correlations: dict[DomainCategory, float] = {}
    
    def create_specialists(self) -> None:
        """Create specialist agents for this domain."""
        # Create specialists based on domain
        specialists_config = self._get_specialist_config()
        
        for i, (name, params) in enumerate(specialists_config.items()):
            specialist = SpecialistAgent(
                agent_id=f"{self.id}_spec_{i}",
                name=name,
                domain=self.domain,
                parent=self
            )
            specialist.sensitivity_to_trigger = params.get("sensitivity", 1.0)
            specialist.volatility = params.get("volatility", 0.1)
            
            # Add API providers
            specialist.add_api_provider("google_trends", GoogleTrendsProvider())
            specialist.add_api_provider("weather", WeatherAPIProvider())
            specialist.add_api_provider("news", NewsAPIProvider())
            specialist.add_api_provider("commodities", CommodityPriceProvider())
            
            self.add_child(specialist)
    
    def _get_specialist_config(self) -> dict:
        """Get specialist configuration for this domain."""
        configs = {
            DomainCategory.PRODUCTION_NUCLEAR: {
                "Ringhals Reactor": {"sensitivity": 1.5, "volatility": 0.02},
                "Forsmark Reactor": {"sensitivity": 1.5, "volatility": 0.02},
                "Oskarshamn Reactor": {"sensitivity": 1.5, "volatility": 0.02},
            },
            DomainCategory.PRODUCTION_HYDRO: {
                "Northern Hydro": {"sensitivity": 1.2, "volatility": 0.1},
                "Central Hydro": {"sensitivity": 1.0, "volatility": 0.1},
                "Reservoir Levels": {"sensitivity": 0.8, "volatility": 0.05},
            },
            DomainCategory.PRODUCTION_WIND: {
                "Offshore Wind": {"sensitivity": 0.5, "volatility": 0.4},
                "Onshore Wind SE1-2": {"sensitivity": 0.5, "volatility": 0.35},
                "Onshore Wind SE3-4": {"sensitivity": 0.5, "volatility": 0.35},
            },
            DomainCategory.DEMAND_INDUSTRIAL: {
                "Manufacturing Demand": {"sensitivity": 0.8, "volatility": 0.15},
                "Mining Demand": {"sensitivity": 0.6, "volatility": 0.1},
                "Process Industry": {"sensitivity": 0.7, "volatility": 0.12},
            },
            DomainCategory.DEMAND_RESIDENTIAL: {
                "Urban Households": {"sensitivity": 1.2, "volatility": 0.2},
                "Rural Households": {"sensitivity": 1.0, "volatility": 0.15},
                "Electric Heating": {"sensitivity": 1.5, "volatility": 0.25},
            },
            DomainCategory.WEATHER_CLIMATE: {
                "Temperature Forecast": {"sensitivity": 0.3, "volatility": 0.2},
                "Wind Forecast": {"sensitivity": 0.3, "volatility": 0.3},
                "Precipitation": {"sensitivity": 0.5, "volatility": 0.25},
            },
            DomainCategory.MARKETS_COMMODITIES: {
                "Natural Gas Prices": {"sensitivity": 1.0, "volatility": 0.2},
                "Oil Prices": {"sensitivity": 0.8, "volatility": 0.15},
                "Carbon Prices": {"sensitivity": 0.6, "volatility": 0.1},
            },
            DomainCategory.GRID_INTERCONNECTION: {
                "Nordic Connections": {"sensitivity": 1.0, "volatility": 0.1},
                "Baltic Cables": {"sensitivity": 0.8, "volatility": 0.08},
                "Continental Links": {"sensitivity": 0.7, "volatility": 0.08},
            },
        }
        return configs.get(self.domain, {"Default Specialist": {"sensitivity": 1.0, "volatility": 0.1}})
    
    async def initialize(self, context: SimulationContext) -> None:
        """Initialize domain orchestrator."""
        self.status = AgentStatus.INITIALIZING
        
        # Create specialists if not already done
        if not self.children:
            self.create_specialists()
        
        # Initialize all specialists
        for child in self.children:
            await child.initialize(context)
        
        # Set domain weight based on trigger relevance
        if self._is_primary_domain_for_trigger(context.trigger_event):
            self.domain_weight = 2.0
        elif self._is_secondary_domain_for_trigger(context.trigger_event):
            self.domain_weight = 1.5
    
    def _is_primary_domain_for_trigger(self, trigger: str) -> bool:
        """Check if this is the primary domain for the trigger."""
        trigger = trigger.lower()
        domain = self.domain.value.lower()
        
        primary_map = {
            "drought": "hydro",
            "nuclear": "nuclear",
            "wind": "wind",
            "cold": "demand_residential",
            "gas": "thermal",
        }
        
        for key, primary in primary_map.items():
            if key in trigger and primary in domain:
                return True
        return False
    
    def _is_secondary_domain_for_trigger(self, trigger: str) -> bool:
        """Check if this is a secondary affected domain."""
        trigger = trigger.lower()
        domain = self.domain.value.lower()
        
        if "drought" in trigger and "weather" in domain:
            return True
        if "cold" in trigger and "weather" in domain:
            return True
        if any(k in trigger for k in ["crisis", "war", "conflict"]) and "geopolitics" in domain:
            return True
        return False
    
    async def simulate_step(self, step: int, delta_hours: float) -> None:
        """Coordinate simulation across specialists."""
        self.status = AgentStatus.RUNNING
        
        # Run all specialists
        for child in self.children:
            await child.simulate_step(step, delta_hours)
        
        # Aggregate signals from children
        all_signals = []
        for child in self.children:
            all_signals.extend(child.signals[-5:])  # Last 5 signals
        
        # Check for domain-level events
        if len(all_signals) >= 3:
            avg_severity = sum(s.severity for s in all_signals) / len(all_signals)
            if avg_severity > 6:
                # Emit domain-level alert
                self.emit_signal(AgentSignal(
                    agent_id=self.id,
                    signal_type=SignalType.RISK_ALERT,
                    domain=self.domain,
                    metric=f"{self.domain.value}_risk",
                    current_value=avg_severity,
                    baseline_value=5.0,
                    change_pct=(avg_severity - 5.0) / 5.0 * 100,
                    confidence=0.8,
                    severity=int(avg_severity),
                    affected_zones=["SE1", "SE2", "SE3", "SE4"]
                ))
    
    async def aggregate_predictions(self) -> list[AgentPrediction]:
        """Aggregate predictions from all specialists."""
        all_predictions = []
        
        for child in self.children:
            child_predictions = await child.aggregate_predictions()
            all_predictions.extend(child_predictions)
        
        # Create domain-level aggregate prediction
        if all_predictions:
            avg_value = sum(p.predicted_value for p in all_predictions) / len(all_predictions)
            avg_confidence = sum(p.confidence for p in all_predictions) / len(all_predictions)
            
            domain_prediction = AgentPrediction(
                agent_id=self.id,
                domain=self.domain,
                metric=f"{self.domain.value}_aggregate",
                predicted_value=avg_value,
                prediction_range=(avg_value * 0.85, avg_value * 1.15),
                horizon_hours=24,
                confidence=min(1.0, avg_confidence * self.domain_weight),  # Clamp to max 1.0
                methodology="domain_aggregation",
                data_sources_used=[p.methodology for p in all_predictions],
                depends_on_predictions=[p.id for p in all_predictions]
            )
            
            self.make_prediction(domain_prediction)
            all_predictions.append(domain_prediction)
        
        return all_predictions


# =============================================================================
# MASTER ORCHESTRATOR
# =============================================================================

class MasterOrchestrator(BaseAgent):
    """
    Master orchestrator (GameMaster) that coordinates all domain orchestrators.
    
    Responsibilities:
    - Create MECE domain coverage
    - Coordinate scenario simulation
    - Aggregate cross-domain insights
    - Identify domino effects
    """
    
    def __init__(self, name: str = "GameMaster"):
        super().__init__(
            agent_id="master",
            name=name,
            role=AgentRole.MASTER_ORCHESTRATOR,
            domain=None,
            parent=None
        )
        
        self.scenario_active = False
        self.domino_chains: list[dict] = []
        self.cross_domain_effects: list[dict] = []
    
    def create_domain_orchestrators(self, domains: Optional[list[DomainCategory]] = None) -> None:
        """Create MECE domain orchestrators."""
        domains = domains or [
            DomainCategory.PRODUCTION_NUCLEAR,
            DomainCategory.PRODUCTION_HYDRO,
            DomainCategory.PRODUCTION_WIND,
            DomainCategory.DEMAND_INDUSTRIAL,
            DomainCategory.DEMAND_RESIDENTIAL,
            DomainCategory.WEATHER_CLIMATE,
            DomainCategory.MARKETS_COMMODITIES,
            DomainCategory.GRID_INTERCONNECTION,
        ]
        
        for domain in domains:
            orchestrator = DomainOrchestrator(
                agent_id=f"domain_{domain.value}",
                name=f"{domain.value.replace('_', ' ').title()} Orchestrator",
                domain=domain,
                parent=self
            )
            orchestrator.create_specialists()
            self.add_child(orchestrator)
        
        logger.info(f"Created {len(self.children)} domain orchestrators with "
                   f"{sum(len(c.children) for c in self.children)} total specialists")
    
    async def initialize(self, context: SimulationContext) -> None:
        """Initialize the master orchestrator."""
        self.status = AgentStatus.INITIALIZING
        self.scenario_active = True
        
        # Create orchestrators if not done
        if not self.children:
            self.create_domain_orchestrators()
        
        # Set cross-domain correlations based on trigger
        self._setup_correlations(context.trigger_event)
        
        # Log API status
        api_status = self.get_api_status()
        logger.info(f"Master: {api_status['enabled']} APIs enabled, {api_status['simulated']} simulated")
        
        # Fetch scenario-level trends using new API registry
        trends = await self.call_api("google_trends",
                                     keywords=[context.trigger_event, "electricity price sweden", "energy crisis"])
        if trends:
            logger.info(f"Master: Fetched trends for scenario '{context.scenario_name}'")
    
    def _setup_correlations(self, trigger: str) -> None:
        """Setup cross-domain correlations based on trigger type."""
        trigger = trigger.lower()
        
        # Define correlation patterns
        if "drought" in trigger:
            self.cross_domain_effects = [
                {"from": DomainCategory.WEATHER_CLIMATE, "to": DomainCategory.PRODUCTION_HYDRO, "strength": 0.9},
                {"from": DomainCategory.PRODUCTION_HYDRO, "to": DomainCategory.MARKETS_COMMODITIES, "strength": 0.7},
                {"from": DomainCategory.MARKETS_COMMODITIES, "to": DomainCategory.DEMAND_INDUSTRIAL, "strength": 0.5},
            ]
        elif "nuclear" in trigger:
            self.cross_domain_effects = [
                {"from": DomainCategory.PRODUCTION_NUCLEAR, "to": DomainCategory.GRID_INTERCONNECTION, "strength": 0.8},
                {"from": DomainCategory.PRODUCTION_NUCLEAR, "to": DomainCategory.MARKETS_COMMODITIES, "strength": 0.7},
                {"from": DomainCategory.MARKETS_COMMODITIES, "to": DomainCategory.DEMAND_RESIDENTIAL, "strength": 0.6},
            ]
        elif "cold" in trigger:
            self.cross_domain_effects = [
                {"from": DomainCategory.WEATHER_CLIMATE, "to": DomainCategory.DEMAND_RESIDENTIAL, "strength": 0.95},
                {"from": DomainCategory.DEMAND_RESIDENTIAL, "to": DomainCategory.GRID_INTERCONNECTION, "strength": 0.7},
                {"from": DomainCategory.WEATHER_CLIMATE, "to": DomainCategory.PRODUCTION_WIND, "strength": 0.6},
            ]
    
    async def simulate_step(self, step: int, delta_hours: float) -> None:
        """Coordinate cross-domain simulation step."""
        self.status = AgentStatus.RUNNING
        
        # Run all domain orchestrators
        for child in self.children:
            await child.simulate_step(step, delta_hours)
        
        # Process cross-domain effects
        await self._process_cross_domain_effects(step)
        
        # Detect domino chains
        self._detect_domino_chains()
    
    async def _process_cross_domain_effects(self, step: int) -> None:
        """Process correlations between domains."""
        for effect in self.cross_domain_effects:
            from_domain = effect["from"]
            to_domain = effect["to"]
            strength = effect["strength"]
            
            # Find source signals
            source_signals = [
                s for s in self.signals
                if s.domain == from_domain and s.severity > 5
            ]
            
            if source_signals:
                # Propagate to target domain
                target_children = [c for c in self.children if c.domain == to_domain]
                for target in target_children:
                    # Trigger secondary effect
                    for signal in source_signals[-3:]:  # Last 3 significant signals
                        propagated_severity = int(signal.severity * strength)
                        if propagated_severity > 3:
                            self.emit_signal(AgentSignal(
                                agent_id=self.id,
                                signal_type=SignalType.CORRELATION,
                                domain=to_domain,
                                metric=f"cascaded_from_{from_domain.value}",
                                current_value=propagated_severity,
                                baseline_value=signal.severity,
                                change_pct=(propagated_severity - signal.severity) / signal.severity * 100 if signal.severity else 0,
                                confidence=signal.confidence * strength,
                                severity=propagated_severity,
                                propagation_probability=strength
                            ))
    
    def _detect_domino_chains(self) -> None:
        """Detect and record domino effect chains."""
        # Group signals by time
        recent_signals = sorted(self.signals[-20:], key=lambda s: s.timestamp)
        
        # Look for causal chains
        for i, signal in enumerate(recent_signals[:-1]):
            for next_signal in recent_signals[i+1:]:
                time_diff = (next_signal.timestamp - signal.timestamp).total_seconds()
                
                if 0 < time_diff < 3600:  # Within 1 hour
                    # Check if domains are correlated
                    for effect in self.cross_domain_effects:
                        if signal.domain == effect["from"] and next_signal.domain == effect["to"]:
                            self.domino_chains.append({
                                "source_signal": signal.id,
                                "target_signal": next_signal.id,
                                "source_domain": signal.domain.value,
                                "target_domain": next_signal.domain.value,
                                "time_lag_seconds": time_diff,
                                "correlation_strength": effect["strength"]
                            })
    
    async def aggregate_predictions(self) -> list[AgentPrediction]:
        """Aggregate all predictions into master forecast."""
        all_predictions = []
        
        # Collect from all domains
        for child in self.children:
            child_predictions = await child.aggregate_predictions()
            all_predictions.extend(child_predictions)
        
        # Create master-level synthesis
        if all_predictions:
            # Calculate weighted average based on domain weights
            domain_predictions = {}
            for pred in all_predictions:
                if pred.domain not in domain_predictions:
                    domain_predictions[pred.domain] = []
                domain_predictions[pred.domain].append(pred)
            
            # Master synthesis - use INFLATION_PRICES as it represents final CPI impact
            master_prediction = AgentPrediction(
                agent_id=self.id,
                domain=DomainCategory.INFLATION_PRICES,  # Master level synthesis for CPI impact
                metric="system_wide_forecast",
                predicted_value=sum(p.predicted_value for p in all_predictions) / len(all_predictions),
                prediction_range=(
                    min(p.prediction_range[0] for p in all_predictions),
                    max(p.prediction_range[1] for p in all_predictions)
                ),
                horizon_hours=24,
                confidence=sum(p.confidence for p in all_predictions) / len(all_predictions),
                methodology="multi_agent_synthesis",
                data_sources_used=list(set(
                    source for p in all_predictions for source in p.data_sources_used
                )),
                depends_on_predictions=[p.id for p in all_predictions],
                estimated_cpi_impact_bps=self._estimate_cpi_impact(all_predictions)
            )
            
            self.make_prediction(master_prediction)
            all_predictions.append(master_prediction)
        
        return all_predictions
    
    def _estimate_cpi_impact(self, predictions: list[AgentPrediction]) -> float:
        """Estimate CPI impact from predictions."""
        # Energy weight in CPI is approximately 5-7%
        energy_cpi_weight = 0.06
        
        # Calculate average price change prediction
        price_changes = []
        for pred in predictions:
            if "price" in pred.metric.lower() or "market" in pred.metric.lower():
                baseline = pred.prediction_range[0]
                if baseline > 0:
                    change_pct = (pred.predicted_value - baseline) / baseline
                    price_changes.append(change_pct)
        
        if price_changes:
            avg_change = sum(price_changes) / len(price_changes)
            cpi_impact_bps = avg_change * energy_cpi_weight * 10000  # Convert to basis points
            return round(cpi_impact_bps, 1)
        
        return 0.0
    
    def get_simulation_summary(self) -> dict:
        """Get summary of simulation results."""
        return {
            "scenario": self.current_context.scenario_name if self.current_context else "N/A",
            "total_agents": len(self.get_all_nodes()),
            "domain_orchestrators": len(self.children),
            "total_signals": len(self.signals),
            "total_predictions": len(self.predictions),
            "domino_chains_detected": len(self.domino_chains),
            "cross_domain_effects": len(self.cross_domain_effects),
            "api_calls_total": sum(n.api_calls_made for n in self.get_all_nodes()),
            "status": self.status.value
        }


# =============================================================================
# MULTI-AGENT SYSTEM
# =============================================================================

class MultiAgentSystem:
    """
    Complete multi-agent simulation system.
    
    Provides:
    - Hierarchical agent management
    - Scenario-based simulation
    - Visualization data
    - API integration
    """
    
    def __init__(self):
        self.master = MasterOrchestrator("Swedish Energy GameMaster")
        self.initialized = False
        self.last_simulation_result: Optional[dict] = None
    
    def initialize(self, domains: Optional[list[DomainCategory]] = None) -> None:
        """Initialize the multi-agent system."""
        self.master.create_domain_orchestrators(domains)
        self.initialized = True
        logger.info("Multi-agent system initialized")
    
    async def run_scenario(
        self,
        scenario_name: str,
        trigger_event: str,
        duration_hours: int = 24,
        trigger_magnitude: float = 1.0,
        initial_prices: Optional[dict[str, float]] = None,
        initial_generation: Optional[dict[str, float]] = None,
        initial_demand: Optional[dict[str, float]] = None
    ) -> dict:
        """
        Run a complete scenario simulation.
        
        Args:
            scenario_name: Name of the scenario
            trigger_event: Trigger event description (e.g., "nordic_drought")
            duration_hours: Simulation duration
            trigger_magnitude: Severity of trigger (1.0 = normal)
            initial_prices: Initial prices by zone
            initial_generation: Initial generation by source
            initial_demand: Initial demand by zone
        
        Returns:
            Simulation results dictionary
        """
        if not self.initialized:
            self.initialize()
        
        # Create simulation context
        context = SimulationContext(
            scenario_name=scenario_name,
            scenario_description=f"Simulation of {trigger_event} impact on Swedish energy sector",
            start_time=datetime.utcnow(),
            current_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=duration_hours),
            initial_prices=initial_prices or {"SE1": 35, "SE2": 40, "SE3": 50, "SE4": 55},
            initial_generation=initial_generation or {
                "nuclear": 6000, "hydro": 8000, "wind": 4000, "solar": 500, "thermal": 1000
            },
            initial_demand=initial_demand or {"SE1": 3000, "SE2": 4000, "SE3": 8000, "SE4": 5000},
            trigger_event=trigger_event,
            trigger_magnitude=trigger_magnitude,
            allow_cascades=True,
            max_cascade_depth=5
        )
        
        logger.info(f"Starting multi-agent simulation: {scenario_name}")
        
        # Run simulation
        predictions = await self.master.run_simulation(context, steps=duration_hours)
        
        # Compile results
        self.last_simulation_result = {
            "scenario": scenario_name,
            "trigger": trigger_event,
            "duration_hours": duration_hours,
            "predictions": [p.model_dump() for p in predictions],
            "signals": [s.model_dump() for s in self.master.signals],
            "domino_chains": self.master.domino_chains,
            "summary": self.master.get_simulation_summary(),
            "agent_tree": [n.model_dump() for n in self.master.get_all_nodes()],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.success(f"Simulation complete: {len(predictions)} predictions, "
                      f"{len(self.master.signals)} signals")
        
        return self.last_simulation_result
    
    def get_agent_tree(self) -> list[AgentNode]:
        """Get the agent hierarchy for visualization."""
        if not self.initialized:
            self.initialize()
        return self.master.get_all_nodes()
    
    def get_visualization_data(self) -> dict:
        """Get data formatted for visualization."""
        nodes = self.get_agent_tree()
        
        # Create nodes and edges for graph visualization
        graph_nodes = []
        graph_edges = []
        
        for node in nodes:
            graph_nodes.append({
                "id": node.id,
                "label": node.name,
                "role": node.role.value,
                "domain": node.domain.value if node.domain else "master",
                "status": node.status.value,
                "level": node.level,
                "signals": node.signals_emitted,
                "predictions": node.predictions_made,
                "api_calls": node.api_calls_made
            })
            
            if node.parent_id:
                graph_edges.append({
                    "source": node.parent_id,
                    "target": node.id,
                    "animated": node.status == AgentStatus.RUNNING
                })
        
        return {
            "nodes": graph_nodes,
            "edges": graph_edges,
            "summary": self.master.get_simulation_summary() if self.initialized else {}
        }


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

_multi_agent_system: Optional[MultiAgentSystem] = None


def get_multi_agent_system() -> MultiAgentSystem:
    """Get or create the multi-agent system singleton."""
    global _multi_agent_system
    if _multi_agent_system is None:
        _multi_agent_system = MultiAgentSystem()
    return _multi_agent_system


async def run_multi_agent_scenario(
    trigger: str,
    duration_hours: int = 24,
    magnitude: float = 1.0
) -> dict:
    """
    Convenience function to run a multi-agent scenario.
    
    Args:
        trigger: Trigger event (e.g., "nordic_drought", "nuclear_outage")
        duration_hours: Simulation duration
        magnitude: Severity multiplier
    
    Returns:
        Simulation results
    """
    system = get_multi_agent_system()
    return await system.run_scenario(
        scenario_name=f"{trigger.replace('_', ' ').title()} Scenario",
        trigger_event=trigger,
        duration_hours=duration_hours,
        trigger_magnitude=magnitude
    )


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == "__main__":
    async def test_system():
        print("Testing Multi-Agent System")
        print("=" * 60)
        
        system = get_multi_agent_system()
        system.initialize()
        
        # Show agent tree
        nodes = system.get_agent_tree()
        print(f"\nAgent Hierarchy ({len(nodes)} total agents):")
        for node in nodes:
            indent = "  " * node.level
            print(f"{indent}├─ {node.name} ({node.role.value})")
        
        # Run simulation
        print("\n" + "=" * 60)
        print("Running 'Nordic Drought' scenario...")
        
        result = await system.run_scenario(
            scenario_name="Nordic Drought Crisis",
            trigger_event="nordic_drought",
            duration_hours=24,
            trigger_magnitude=1.5
        )
        
        print(f"\nResults:")
        print(f"  Predictions: {len(result['predictions'])}")
        print(f"  Signals: {len(result['signals'])}")
        print(f"  Domino Chains: {len(result['domino_chains'])}")
        print(f"  API Calls: {result['summary']['api_calls_total']}")
        
        # Show some predictions
        print("\nTop Predictions:")
        for pred in result['predictions'][:5]:
            print(f"  - {pred['metric']}: {pred['predicted_value']:.1f} "
                  f"(confidence: {pred['confidence']:.2f})")
        
        # Show domino chains
        if result['domino_chains']:
            print("\nDomino Chains Detected:")
            for chain in result['domino_chains'][:3]:
                print(f"  {chain['source_domain']} → {chain['target_domain']} "
                      f"(strength: {chain['correlation_strength']:.2f})")
    
    asyncio.run(test_system())
