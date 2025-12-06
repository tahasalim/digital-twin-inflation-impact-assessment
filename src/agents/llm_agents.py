"""
LLM-Powered Agent System for Swedish Energy Digital Twin.

Each agent:
1. Fetches real data from relevant APIs
2. Constructs a context-rich prompt
3. Calls an LLM (Google Gemini, OpenAI, etc.) for analysis
4. Returns structured, human-readable results

The orchestrator aggregates all agent outputs into a comprehensive summary.
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from loguru import logger

# Try to import LLM libraries
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not installed. Run: pip install google-generativeai")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================

class LLMSettings(BaseSettings):
    """LLM configuration from environment variables."""
    
    # Google Gemini (recommended - free tier available)
    google_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.0-flash"
    
    # OpenAI (alternative)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4o-mini"
    
    # General settings
    max_tokens: int = 1024
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


_llm_settings: Optional[LLMSettings] = None

def get_llm_settings() -> LLMSettings:
    global _llm_settings
    if _llm_settings is None:
        _llm_settings = LLMSettings()
    return _llm_settings


# =============================================================================
# LLM CLIENT ABSTRACTION
# =============================================================================

class LLMProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    MOCK = "mock"


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    provider: LLMProvider
    tokens_used: int = 0
    latency_ms: int = 0
    success: bool = True
    error: Optional[str] = None


class LLMClient:
    """
    Unified LLM client supporting multiple providers.
    Automatically selects available provider based on API keys.
    """
    
    def __init__(self):
        self.settings = get_llm_settings()
        self.provider = self._detect_provider()
        self._setup_provider()
    
    def _detect_provider(self) -> LLMProvider:
        """Detect which LLM provider is available."""
        if self.settings.google_api_key and GEMINI_AVAILABLE:
            logger.info("Using Google Gemini as LLM provider")
            return LLMProvider.GEMINI
        elif self.settings.openai_api_key and OPENAI_AVAILABLE:
            logger.info("Using OpenAI as LLM provider")
            return LLMProvider.OPENAI
        else:
            logger.warning("No LLM API keys configured, using mock responses")
            return LLMProvider.MOCK
    
    def _setup_provider(self):
        """Initialize the selected provider."""
        if self.provider == LLMProvider.GEMINI:
            genai.configure(api_key=self.settings.google_api_key)
            self.model = genai.GenerativeModel(self.settings.gemini_model)
        elif self.provider == LLMProvider.OPENAI:
            openai.api_key = self.settings.openai_api_key
    
    async def generate(self, prompt: str, system_prompt: str = None) -> LLMResponse:
        """Generate a response from the LLM."""
        start_time = datetime.now()
        
        try:
            if self.provider == LLMProvider.GEMINI:
                return await self._generate_gemini(prompt, system_prompt, start_time)
            elif self.provider == LLMProvider.OPENAI:
                return await self._generate_openai(prompt, system_prompt, start_time)
            else:
                return self._generate_mock(prompt, start_time)
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return LLMResponse(
                content=f"Error generating response: {str(e)}",
                model="error",
                provider=self.provider,
                success=False,
                error=str(e),
                latency_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )
    
    async def _generate_gemini(self, prompt: str, system_prompt: str, start_time: datetime) -> LLMResponse:
        """Generate using Google Gemini."""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        # Run in thread pool since genai is synchronous
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.settings.max_tokens,
                    temperature=self.settings.temperature,
                )
            )
        )
        
        latency = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return LLMResponse(
            content=response.text,
            model=self.settings.gemini_model,
            provider=LLMProvider.GEMINI,
            tokens_used=response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
            latency_ms=latency,
        )
    
    async def _generate_openai(self, prompt: str, system_prompt: str, start_time: datetime) -> LLMResponse:
        """Generate using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await openai.ChatCompletion.acreate(
            model=self.settings.openai_model,
            messages=messages,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
        )
        
        latency = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.settings.openai_model,
            provider=LLMProvider.OPENAI,
            tokens_used=response.usage.total_tokens,
            latency_ms=latency,
        )
    
    def _generate_mock(self, prompt: str, start_time: datetime) -> LLMResponse:
        """Generate a mock response when no LLM is available."""
        # Extract key info from prompt for a contextual mock response
        import re
        
        # Try to detect scenario type
        scenario_match = re.search(r"scenario[:\s]+([^\n]+)", prompt.lower())
        scenario = scenario_match.group(1).strip() if scenario_match else "energy crisis"
        
        mock_response = f"""Based on my analysis of the available data:

**Key Findings:**
1. The {scenario} scenario indicates significant stress on the Swedish energy system
2. Price volatility is expected to increase by 15-25% in affected zones
3. Supply-demand balance will be challenged during peak hours

**Impact Assessment:**
- SE3 (Stockholm) faces the highest price pressure due to population density
- SE1/SE2 (Northern zones) show more resilience due to hydro capacity
- Cross-border flows will need to increase by ~20% to maintain stability

**Recommendations:**
- Monitor real-time grid balance closely
- Prepare demand response mechanisms
- Consider strategic reserve activation if prices exceed €150/MWh

**Confidence Level:** 78%

*Note: This analysis is based on historical patterns and current market indicators.*
"""
        
        latency = int((datetime.now() - start_time).total_seconds() * 1000) + 50
        
        return LLMResponse(
            content=mock_response,
            model="mock-model",
            provider=LLMProvider.MOCK,
            tokens_used=len(mock_response.split()),
            latency_ms=latency,
        )


# Singleton LLM client
_llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# =============================================================================
# AGENT DATA MODELS
# =============================================================================

@dataclass
class AgentContext:
    """Context passed to an agent for analysis."""
    scenario_trigger: str
    scenario_description: str
    duration_hours: int
    magnitude: float
    timestamp: datetime = field(default_factory=datetime.now)
    custom_prompt: Optional[str] = None
    parent_results: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result from an agent's analysis."""
    agent_id: str
    agent_name: str
    domain: str
    
    # Data fetched
    data_sources: List[str]
    raw_data: Dict[str, Any]
    
    # LLM analysis
    analysis: str  # Human-readable analysis from LLM
    key_findings: List[str]
    metrics: Dict[str, Any]
    confidence: float
    
    # Metadata
    llm_response: Optional[LLMResponse] = None
    processing_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "data_sources": self.data_sources,
            "raw_data": self.raw_data,
            "analysis": self.analysis,
            "key_findings": self.key_findings,
            "metrics": self.metrics,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# BASE AGENT CLASS
# =============================================================================

class BaseAgent(ABC):
    """
    Base class for all LLM-powered agents.
    
    Each agent:
    1. Defines its data sources
    2. Fetches relevant data
    3. Constructs a prompt with context
    4. Calls the LLM for analysis
    5. Returns structured results
    """
    
    def __init__(self, agent_id: str, agent_name: str, domain: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.domain = domain
        self.llm = get_llm_client()
    
    @abstractmethod
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        """Fetch relevant data for this agent's analysis."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    def build_analysis_prompt(self, context: AgentContext, data: Dict[str, Any]) -> str:
        """Build the analysis prompt with context and data."""
        prompt = f"""
## Scenario Analysis Request

**Scenario:** {context.scenario_trigger.replace('_', ' ').title()}
**Description:** {context.scenario_description}
**Duration:** {context.duration_hours} hours
**Magnitude:** {context.magnitude}x severity

## Available Data

{json.dumps(data, indent=2, default=str)}

## Analysis Required

Based on the scenario and data above, provide:
1. **Impact Assessment**: How does this scenario affect your domain?
2. **Key Metrics**: Quantify the expected changes (prices, volumes, etc.)
3. **Risk Factors**: What are the main risks and uncertainties?
4. **Recommendations**: What actions should be considered?

Please be specific and use the actual data values in your analysis.
"""
        
        if context.custom_prompt:
            prompt += f"\n## Additional Context\n{context.custom_prompt}\n"
        
        return prompt
    
    async def analyze(self, context: AgentContext) -> AgentResult:
        """Run the full analysis pipeline."""
        start_time = datetime.now()
        
        # Step 1: Fetch data
        logger.info(f"[{self.agent_name}] Fetching data...")
        try:
            data = await self.fetch_data(context)
            data_sources = list(data.keys())
        except Exception as e:
            logger.error(f"[{self.agent_name}] Data fetch error: {e}")
            data = {"error": str(e)}
            data_sources = []
        
        # Step 2: Build prompt
        prompt = self.build_analysis_prompt(context, data)
        system_prompt = self.get_system_prompt()
        
        # Step 3: Call LLM
        logger.info(f"[{self.agent_name}] Calling LLM for analysis...")
        llm_response = await self.llm.generate(prompt, system_prompt)
        
        # Step 4: Parse response
        analysis = llm_response.content
        key_findings = self._extract_key_findings(analysis)
        metrics = self._extract_metrics(analysis, data)
        confidence = self._calculate_confidence(llm_response, data)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            domain=self.domain,
            data_sources=data_sources,
            raw_data=data,
            analysis=analysis,
            key_findings=key_findings,
            metrics=metrics,
            confidence=confidence,
            llm_response=llm_response,
            processing_time_ms=processing_time,
        )
    
    def _extract_key_findings(self, analysis: str) -> List[str]:
        """Extract key findings from the analysis text."""
        findings = []
        lines = analysis.split('\n')
        
        in_findings_section = False
        for line in lines:
            line = line.strip()
            if 'finding' in line.lower() or 'key' in line.lower():
                in_findings_section = True
                continue
            if in_findings_section and line.startswith(('1.', '2.', '3.', '-', '•', '*')):
                # Clean up the line
                clean = line.lstrip('0123456789.-•* ').strip()
                if clean:
                    findings.append(clean)
            if len(findings) >= 5:
                break
        
        # If no structured findings, extract first sentences
        if not findings:
            sentences = analysis.replace('\n', ' ').split('.')
            findings = [s.strip() + '.' for s in sentences[:3] if len(s.strip()) > 20]
        
        return findings
    
    def _extract_metrics(self, analysis: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract quantitative metrics from analysis."""
        import re
        
        metrics = {}
        
        # Extract percentages
        pct_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', analysis)
        if pct_matches:
            metrics['mentioned_percentages'] = [float(p) for p in pct_matches[:5]]
        
        # Extract prices (EUR/MWh patterns)
        price_matches = re.findall(r'€?\s*(\d+(?:\.\d+)?)\s*(?:EUR)?/MWh', analysis)
        if price_matches:
            metrics['mentioned_prices_eur_mwh'] = [float(p) for p in price_matches[:5]]
        
        # Include key data metrics
        if 'electricity_prices' in data:
            metrics['current_prices'] = data['electricity_prices']
        
        return metrics
    
    def _calculate_confidence(self, llm_response: LLMResponse, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data quality and LLM response."""
        base_confidence = 0.7
        
        # Boost for successful LLM response
        if llm_response.success:
            base_confidence += 0.1
        
        # Boost for having real data
        if data and 'error' not in data:
            base_confidence += 0.1
        
        # Reduce if using mock LLM
        if llm_response.provider == LLMProvider.MOCK:
            base_confidence -= 0.15
        
        return min(0.95, max(0.3, base_confidence))


# =============================================================================
# SPECIALIZED AGENTS
# =============================================================================

class HydroAgent(BaseAgent):
    """Agent analyzing hydroelectric power supply."""
    
    def __init__(self):
        super().__init__("hydro", "Hydro Power Analyst", "SUPPLY")
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        from src.data.sources import get_data_aggregator
        aggregator = get_data_aggregator()
        
        # Fetch relevant data
        weather = await aggregator.get_weather_impact()
        prices = await aggregator.get_current_electricity_prices()
        
        return {
            "weather_by_zone": {k: v.model_dump() for k, v in weather.items()},
            "current_prices_eur_mwh": prices,
            "scenario": {
                "trigger": context.scenario_trigger,
                "duration_hours": context.duration_hours,
                "magnitude": context.magnitude,
            },
            "hydro_context": {
                "typical_share_of_generation": "45%",
                "major_producers": ["Vattenfall", "Fortum", "Uniper"],
                "reservoir_regions": ["Norrland (SE1/SE2)", "Dalälven"],
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert hydroelectric power analyst for the Swedish energy system.

Your expertise includes:
- Swedish reservoir hydrology and seasonal patterns
- Impact of weather (precipitation, temperature) on hydro production
- Price formation in Nord Pool electricity market
- Grid balancing and hydro flexibility

Sweden's hydro power provides ~45% of electricity, primarily in northern zones (SE1/SE2).
Reservoirs are crucial for balancing intermittent wind power.

Provide analysis in a clear, structured format with specific numbers and actionable insights."""


class WindAgent(BaseAgent):
    """Agent analyzing wind power supply."""
    
    def __init__(self):
        super().__init__("wind", "Wind Power Analyst", "SUPPLY")
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        from src.data.sources import get_data_aggregator
        aggregator = get_data_aggregator()
        
        weather = await aggregator.get_weather_impact()
        prices = await aggregator.get_current_electricity_prices()
        
        return {
            "weather_by_zone": {k: {"wind_speed_ms": v.wind_speed_ms, "temp_c": v.temperature_c} 
                               for k, v in weather.items()},
            "current_prices_eur_mwh": prices,
            "scenario": context.scenario_trigger,
            "wind_context": {
                "installed_capacity_gw": 16.5,
                "typical_share": "20%",
                "key_regions": ["SE2 (Sundsvall)", "SE4 (Skåne offshore)"],
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert wind power analyst for the Swedish energy system.

Your expertise includes:
- Wind farm operations and capacity factors
- Weather forecasting impact on wind generation
- Grid integration challenges of variable wind
- Nord Pool price dynamics during high/low wind periods

Sweden has ~16.5 GW installed wind capacity, growing rapidly.
Wind is highly variable - capacity factors range from 5% to 90%.

Provide specific, data-driven analysis with attention to forecast uncertainty."""


class NuclearAgent(BaseAgent):
    """Agent analyzing nuclear power supply."""
    
    def __init__(self):
        super().__init__("nuclear", "Nuclear Power Analyst", "SUPPLY")
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        from src.data.sources import get_data_aggregator
        aggregator = get_data_aggregator()
        
        prices = await aggregator.get_current_electricity_prices()
        
        return {
            "current_prices_eur_mwh": prices,
            "scenario": context.scenario_trigger,
            "nuclear_context": {
                "active_reactors": [
                    {"name": "Forsmark 1", "capacity_mw": 984, "status": "operational"},
                    {"name": "Forsmark 2", "capacity_mw": 1120, "status": "operational"},
                    {"name": "Forsmark 3", "capacity_mw": 1170, "status": "operational"},
                    {"name": "Ringhals 3", "capacity_mw": 1070, "status": "operational"},
                    {"name": "Ringhals 4", "capacity_mw": 1120, "status": "operational"},
                    {"name": "Oskarshamn 3", "capacity_mw": 1400, "status": "operational"},
                ],
                "total_capacity_mw": 6864,
                "typical_share": "30%",
                "decommissioned": ["Ringhals 1", "Ringhals 2", "Oskarshamn 1", "Oskarshamn 2"],
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert nuclear power analyst for the Swedish energy system.

Your expertise includes:
- Swedish nuclear reactor operations (Forsmark, Ringhals, Oskarshamn)
- Baseload power characteristics and grid stability
- Maintenance schedules and unplanned outages
- Nuclear policy and phase-out/restart debates

Sweden has 6 operational reactors providing ~30% of electricity.
Nuclear provides stable baseload but has limited flexibility.

Analyze nuclear impact on grid stability and prices with technical precision."""


class IndustrialDemandAgent(BaseAgent):
    """Agent analyzing industrial electricity demand."""
    
    def __init__(self):
        super().__init__("industrial", "Industrial Demand Analyst", "DEMAND")
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        from src.data.sources import get_data_aggregator
        aggregator = get_data_aggregator()
        
        prices = await aggregator.get_current_electricity_prices()
        inflation = await aggregator.get_inflation_indicators()
        
        return {
            "current_prices_eur_mwh": prices,
            "inflation_data": inflation,
            "scenario": context.scenario_trigger,
            "industrial_context": {
                "major_sectors": [
                    {"name": "Steel (SSAB, H2 Green Steel)", "demand_twh": 8.5, "price_sensitivity": "high"},
                    {"name": "Paper & Pulp", "demand_twh": 12, "price_sensitivity": "medium"},
                    {"name": "Chemicals", "demand_twh": 4, "price_sensitivity": "medium"},
                    {"name": "Data Centers", "demand_twh": 3, "price_sensitivity": "low"},
                ],
                "total_industrial_demand_twh": 50,
                "demand_response_potential_mw": 1500,
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert industrial demand analyst for the Swedish electricity market.

Your expertise includes:
- Swedish industrial energy consumption patterns
- Price elasticity of major industrial sectors
- Demand response capabilities and contracts
- Impact of electricity costs on production decisions

Major sectors: Steel, Paper/Pulp, Chemicals, Data Centers.
Industrial demand is ~35% of Swedish electricity use.

Analyze how the scenario affects industrial consumption and flexibility."""


class ResidentialDemandAgent(BaseAgent):
    """Agent analyzing residential and commercial demand."""
    
    def __init__(self):
        super().__init__("residential", "Residential Demand Analyst", "DEMAND")
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        from src.data.sources import get_data_aggregator
        aggregator = get_data_aggregator()
        
        weather = await aggregator.get_weather_impact()
        prices = await aggregator.get_current_electricity_prices()
        
        return {
            "weather_by_zone": {k: v.model_dump() for k, v in weather.items()},
            "current_prices_eur_mwh": prices,
            "scenario": context.scenario_trigger,
            "residential_context": {
                "heating_degree_days_impact": "15 TWh/°C below normal winter temp",
                "heat_pump_penetration": "35% of households",
                "ev_charging_load_growth": "12% annually",
                "typical_peak_demand_gw": 27,
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert residential and commercial demand analyst for Sweden.

Your expertise includes:
- Swedish heating patterns and temperature sensitivity
- Heat pump and electric vehicle adoption trends
- Peak demand forecasting
- Consumer behavior and price response

Swedish residential demand is highly temperature-sensitive due to electric heating.
Winter peaks can reach 27 GW vs summer lows of 15 GW.

Analyze demand impacts considering weather and consumer behavior."""


class GridBalanceAgent(BaseAgent):
    """Agent analyzing grid balance and interconnectors."""
    
    def __init__(self):
        super().__init__("grid", "Grid Balance Analyst", "DEMAND")
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        from src.data.sources import get_data_aggregator
        aggregator = get_data_aggregator()
        
        prices = await aggregator.get_current_electricity_prices()
        
        return {
            "current_prices_eur_mwh": prices,
            "price_spreads": {
                "SE1_SE4": prices.get("SE4", 0) - prices.get("SE1", 0) if prices else 0,
            },
            "scenario": context.scenario_trigger,
            "grid_context": {
                "interconnectors": [
                    {"name": "NordLink (NO)", "capacity_mw": 1400},
                    {"name": "SwePol (PL)", "capacity_mw": 600},
                    {"name": "Baltic Cable (DE)", "capacity_mw": 600},
                    {"name": "Fenno-Skan (FI)", "capacity_mw": 1200},
                    {"name": "Kontek (DK)", "capacity_mw": 680},
                ],
                "internal_bottlenecks": "SE2→SE3 (limited by ~7000 MW)",
                "tso": "Svenska kraftnät",
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert grid balance and transmission analyst for Svenska kraftnät.

Your expertise includes:
- Swedish transmission grid operations
- Cross-border interconnector flows
- Internal bottlenecks (especially SE2→SE3)
- Frequency regulation and reserve markets

Sweden typically exports to Finland and imports from Norway.
The SE2→SE3 bottleneck creates persistent price differences.

Analyze grid balance, congestion risks, and interconnector utilization."""


class CommoditiesAgent(BaseAgent):
    """Agent analyzing commodity markets impact."""
    
    def __init__(self):
        super().__init__("commodities", "Commodities Analyst", "EXTERNAL")
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        from src.data.sources import get_data_aggregator
        aggregator = get_data_aggregator()
        
        prices = await aggregator.get_current_electricity_prices()
        
        # Would fetch from FRED/other commodity sources
        return {
            "current_electricity_prices": prices,
            "scenario": context.scenario_trigger,
            "commodity_context": {
                "ttf_gas_eur_mwh": 35.0,  # Would be real-time
                "eu_ets_carbon_eur_t": 70.0,  # Would be real-time
                "brent_oil_usd": 75.0,
                "coal_usd_t": 120.0,
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert commodities analyst focusing on energy markets.

Your expertise includes:
- TTF natural gas pricing and European gas market dynamics
- EU ETS carbon pricing and policy developments
- Oil market fundamentals and price transmission
- Commodity price impact on electricity marginal costs

Commodity prices set the marginal cost for thermal generation.
Carbon prices increasingly drive electricity prices in Europe.

Analyze commodity market impacts on Swedish electricity prices."""


class PolicyAgent(BaseAgent):
    """Agent analyzing policy and regulatory impacts."""
    
    def __init__(self):
        super().__init__("policy", "Policy Analyst", "EXTERNAL")
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        from src.data.sources import get_data_aggregator
        aggregator = get_data_aggregator()
        
        news = await aggregator.get_news_sentiment()
        
        return {
            "news_sentiment": news,
            "scenario": context.scenario_trigger,
            "policy_context": {
                "government": "Center-right coalition (2022-)",
                "energy_minister": "Ebba Busch",
                "key_policies": [
                    "Nuclear power restart support",
                    "Electricity price cap discussions",
                    "Green transition investments",
                    "Grid expansion program",
                ],
                "riksbank_rate": 3.75,  # Would be real-time
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert energy policy analyst for Sweden and the EU.

Your expertise includes:
- Swedish energy and climate policy
- EU energy regulations (REPowerEU, Fit for 55)
- Riksbank monetary policy implications
- Government intervention mechanisms

Sweden's government supports nuclear expansion and has debated price caps.
EU regulations on renewables and emissions shape long-term investment.

Analyze policy risks and potential government responses to the scenario."""


class WeatherAgent(BaseAgent):
    """Agent analyzing weather impacts."""
    
    def __init__(self):
        super().__init__("weather", "Weather Analyst", "EXTERNAL")
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        from src.data.sources import get_data_aggregator
        aggregator = get_data_aggregator()
        
        weather = await aggregator.get_weather_impact()
        
        return {
            "current_weather": {k: v.model_dump() for k, v in weather.items()},
            "scenario": context.scenario_trigger,
            "weather_context": {
                "data_source": "SMHI (Swedish Meteorological Institute)",
                "climate_zone": "Subarctic to Temperate",
                "heating_season": "October - April",
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert meteorologist focused on energy-relevant weather analysis.

Your expertise includes:
- Swedish and Nordic weather patterns
- Temperature impact on electricity demand
- Wind resource forecasting
- Hydrology and precipitation patterns

Swedish demand is highly weather-sensitive (heating in winter).
Wind and hydro generation depend directly on weather conditions.

Provide weather analysis focused on energy system impacts."""


# =============================================================================
# ORCHESTRATOR AGENTS
# =============================================================================

class DomainOrchestrator(BaseAgent):
    """Orchestrator that aggregates results from domain-specific agents."""
    
    def __init__(self, domain: str, child_agents: List[BaseAgent]):
        super().__init__(f"{domain.lower()}_orchestrator", f"{domain} Orchestrator", domain)
        self.child_agents = child_agents
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        """Aggregate data from child agents."""
        # parent_results may be dicts or AgentResult objects
        child_results = []
        for r in context.parent_results:
            if hasattr(r, 'to_dict'):
                child_results.append(r.to_dict())
            elif isinstance(r, dict):
                child_results.append(r)
            else:
                child_results.append(str(r))
        return {
            "child_results": child_results,
            "scenario": context.scenario_trigger,
        }
    
    async def run_children(self, context: AgentContext) -> List[AgentResult]:
        """Run all child agents and collect results."""
        tasks = [agent.analyze(context) for agent in self.child_agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for r in results:
            if isinstance(r, AgentResult):
                valid_results.append(r)
            else:
                logger.error(f"Child agent error: {r}")
        
        return valid_results
    
    def get_system_prompt(self) -> str:
        return f"""You are the {self.domain} Domain Orchestrator for the Swedish Energy Digital Twin.

Your role is to:
1. Synthesize analyses from your domain's specialist agents
2. Identify cross-cutting themes and risks
3. Provide a coherent domain-level assessment
4. Highlight key metrics and recommendations

Be concise but comprehensive. Focus on actionable insights."""


class MasterOrchestrator(BaseAgent):
    """Top-level orchestrator that synthesizes all domain analyses."""
    
    def __init__(self):
        super().__init__("master", "Master Orchestrator", "SYSTEM")
        
        # Create domain orchestrators with their child agents
        self.supply_agents = [HydroAgent(), WindAgent(), NuclearAgent()]
        self.demand_agents = [IndustrialDemandAgent(), ResidentialDemandAgent(), GridBalanceAgent()]
        self.external_agents = [WeatherAgent(), CommoditiesAgent(), PolicyAgent()]
        
        self.supply_orchestrator = DomainOrchestrator("SUPPLY", self.supply_agents)
        self.demand_orchestrator = DomainOrchestrator("DEMAND", self.demand_agents)
        self.external_orchestrator = DomainOrchestrator("EXTERNAL", self.external_agents)
    
    async def fetch_data(self, context: AgentContext) -> Dict[str, Any]:
        # parent_results may be dicts or AgentResult objects
        domain_summaries = []
        for r in context.parent_results:
            if hasattr(r, 'to_dict'):
                domain_summaries.append(r.to_dict())
            elif isinstance(r, dict):
                domain_summaries.append(r)
            else:
                domain_summaries.append(str(r))
        return {
            "domain_summaries": domain_summaries,
            "scenario": context.scenario_trigger,
        }
    
    async def run_full_analysis(self, context: AgentContext) -> Dict[str, Any]:
        """Run the complete multi-agent analysis pipeline."""
        logger.info(f"Starting full analysis for scenario: {context.scenario_trigger}")
        start_time = datetime.now()
        
        all_results = []
        domain_results = {}
        
        # Run all specialist agents in parallel
        logger.info("Running specialist agents...")
        supply_results = await self.supply_orchestrator.run_children(context)
        demand_results = await self.demand_orchestrator.run_children(context)
        external_results = await self.external_orchestrator.run_children(context)
        
        all_results.extend(supply_results)
        all_results.extend(demand_results)
        all_results.extend(external_results)
        
        # Run domain orchestrators
        logger.info("Running domain orchestrators...")
        
        supply_context = AgentContext(
            scenario_trigger=context.scenario_trigger,
            scenario_description=context.scenario_description,
            duration_hours=context.duration_hours,
            magnitude=context.magnitude,
            parent_results=[r.to_dict() for r in supply_results],
        )
        supply_summary = await self.supply_orchestrator.analyze(supply_context)
        domain_results["supply"] = supply_summary
        
        demand_context = AgentContext(
            scenario_trigger=context.scenario_trigger,
            scenario_description=context.scenario_description,
            duration_hours=context.duration_hours,
            magnitude=context.magnitude,
            parent_results=[r.to_dict() for r in demand_results],
        )
        demand_summary = await self.demand_orchestrator.analyze(demand_context)
        domain_results["demand"] = demand_summary
        
        external_context = AgentContext(
            scenario_trigger=context.scenario_trigger,
            scenario_description=context.scenario_description,
            duration_hours=context.duration_hours,
            magnitude=context.magnitude,
            parent_results=[r.to_dict() for r in external_results],
        )
        external_summary = await self.external_orchestrator.analyze(external_context)
        domain_results["external"] = external_summary
        
        # Run master synthesis
        logger.info("Running master synthesis...")
        master_context = AgentContext(
            scenario_trigger=context.scenario_trigger,
            scenario_description=context.scenario_description,
            duration_hours=context.duration_hours,
            magnitude=context.magnitude,
            parent_results=[
                supply_summary.to_dict(),
                demand_summary.to_dict(),
                external_summary.to_dict(),
            ],
        )
        master_result = await self.analyze(master_context)
        
        total_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return {
            "master_summary": master_result.to_dict(),
            "domain_summaries": {k: v.to_dict() for k, v in domain_results.items()},
            "specialist_results": [r.to_dict() for r in all_results],
            "total_processing_time_ms": total_time,
            "agent_count": len(all_results) + 4,  # specialists + orchestrators + master
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_system_prompt(self) -> str:
        return """You are the Master Orchestrator for the Swedish Energy Digital Twin system.

Your role is to provide an executive-level synthesis of all domain analyses:
- SUPPLY: Hydro, Wind, Nuclear generation impacts
- DEMAND: Industrial, Residential consumption, Grid balance
- EXTERNAL: Weather, Commodities, Policy factors

Provide a clear, actionable summary suitable for Riksbank economists and energy policymakers.
Include:
1. Executive Summary (2-3 sentences)
2. Key Impacts by Domain
3. Overall Risk Assessment
4. Recommended Actions
5. Confidence Level and Caveats

Be authoritative but acknowledge uncertainties. Use specific numbers from the analyses."""


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def run_multi_agent_analysis(
    scenario_trigger: str,
    duration_hours: int = 24,
    magnitude: float = 1.0,
    custom_prompt: str = None,
) -> Dict[str, Any]:
    """
    Run a complete multi-agent analysis for a scenario.
    
    This is the main entry point for the multi-agent system.
    """
    scenario_descriptions = {
        "nordic_drought": "Prolonged dry period reducing hydroelectric reservoir levels across Scandinavia",
        "nuclear_outage": "Unplanned outage at one or more Swedish nuclear reactors",
        "cold_wave": "Extended period of below-normal temperatures increasing heating demand",
        "wind_lull": "Low wind conditions across the Nordic region reducing wind generation",
        "gas_crisis": "European natural gas supply disruption affecting thermal generation",
        "cable_failure": "Failure of major interconnector cable limiting cross-border capacity",
        "cyber_attack": "Cyber incident affecting grid operations or market systems",
        "price_spike": "Extreme price spike in Nord Pool day-ahead market",
    }
    
    context = AgentContext(
        scenario_trigger=scenario_trigger,
        scenario_description=scenario_descriptions.get(
            scenario_trigger, 
            f"Custom scenario: {scenario_trigger}"
        ),
        duration_hours=duration_hours,
        magnitude=magnitude,
        custom_prompt=custom_prompt,
    )
    
    orchestrator = MasterOrchestrator()
    return await orchestrator.run_full_analysis(context)


def run_multi_agent_analysis_sync(
    scenario_trigger: str,
    duration_hours: int = 24,
    magnitude: float = 1.0,
    custom_prompt: str = None,
) -> Dict[str, Any]:
    """Synchronous wrapper for run_multi_agent_analysis."""
    return asyncio.run(run_multi_agent_analysis(
        scenario_trigger=scenario_trigger,
        duration_hours=duration_hours,
        magnitude=magnitude,
        custom_prompt=custom_prompt,
    ))


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Settings
    "LLMSettings",
    "get_llm_settings",
    
    # LLM Client
    "LLMClient",
    "LLMProvider",
    "LLMResponse",
    "get_llm_client",
    
    # Data Models
    "AgentContext",
    "AgentResult",
    
    # Base Agent
    "BaseAgent",
    
    # Specialist Agents
    "HydroAgent",
    "WindAgent",
    "NuclearAgent",
    "IndustrialDemandAgent",
    "ResidentialDemandAgent",
    "GridBalanceAgent",
    "WeatherAgent",
    "CommoditiesAgent",
    "PolicyAgent",
    
    # Orchestrators
    "DomainOrchestrator",
    "MasterOrchestrator",
    
    # Entry Points
    "run_multi_agent_analysis",
    "run_multi_agent_analysis_sync",
]
