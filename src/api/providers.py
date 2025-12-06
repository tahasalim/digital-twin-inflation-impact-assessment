"""
API Provider Registry for Swedish Energy Digital Twin.

Centralized management of all external API providers with:
- Automatic enable/disable based on API key availability
- Unified configuration from environment variables
- Graceful fallback to simulated data
- Rate limiting and caching
- Health monitoring
"""

from __future__ import annotations

import os
import asyncio
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
from functools import wraps

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# =============================================================================
# API STATUS & CONFIGURATION
# =============================================================================

class APIStatus(str, Enum):
    """Status of an API provider."""
    ENABLED = "enabled"          # API key present and validated
    DISABLED = "disabled"        # No API key provided
    SIMULATED = "simulated"      # Using simulated data
    ERROR = "error"              # API key present but failing
    RATE_LIMITED = "rate_limited"  # Temporarily rate limited


@dataclass
class APIConfig:
    """Configuration for an API provider."""
    name: str
    env_key: str                          # Environment variable name for API key
    env_keys: list[str] = field(default_factory=list)  # Additional env vars
    base_url: Optional[str] = None
    rate_limit_rpm: int = 60              # Requests per minute
    cache_ttl_seconds: int = 3600         # Cache time-to-live
    requires_key: bool = True             # Some APIs don't need keys
    description: str = ""
    docs_url: str = ""


# =============================================================================
# API PROVIDER REGISTRY
# =============================================================================

# All supported API configurations
API_CONFIGS: dict[str, APIConfig] = {
    # Search & Trends
    "serpapi": APIConfig(
        name="SerpAPI (Google Trends)",
        env_key="SERPAPI_API_KEY",
        base_url="https://serpapi.com/search",
        rate_limit_rpm=100,
        description="Google Trends data via SerpAPI",
        docs_url="https://serpapi.com/"
    ),
    "google_search": APIConfig(
        name="Google Custom Search",
        env_key="GOOGLE_API_KEY",
        env_keys=["GOOGLE_CUSTOM_SEARCH_ENGINE_ID"],
        base_url="https://customsearch.googleapis.com/customsearch/v1",
        rate_limit_rpm=100,
        description="Google Custom Search for news",
        docs_url="https://developers.google.com/custom-search/"
    ),
    
    # Social Media
    "twitter": APIConfig(
        name="Twitter/X API",
        env_key="TWITTER_BEARER_TOKEN",
        env_keys=["TWITTER_API_KEY", "TWITTER_API_SECRET"],
        base_url="https://api.twitter.com/2",
        rate_limit_rpm=300,
        description="Social sentiment from Twitter",
        docs_url="https://developer.twitter.com/"
    ),
    "reddit": APIConfig(
        name="Reddit API",
        env_key="REDDIT_CLIENT_ID",
        env_keys=["REDDIT_CLIENT_SECRET"],
        base_url="https://oauth.reddit.com",
        rate_limit_rpm=60,
        description="Community sentiment from Reddit",
        docs_url="https://www.reddit.com/dev/api/"
    ),
    
    # AI/LLM
    "openai": APIConfig(
        name="OpenAI",
        env_key="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        rate_limit_rpm=60,
        description="GPT models for agent reasoning",
        docs_url="https://platform.openai.com/"
    ),
    "anthropic": APIConfig(
        name="Anthropic Claude",
        env_key="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com/v1",
        rate_limit_rpm=60,
        description="Claude models for agent reasoning",
        docs_url="https://console.anthropic.com/"
    ),
    "azure_openai": APIConfig(
        name="Azure OpenAI",
        env_key="AZURE_OPENAI_API_KEY",
        env_keys=["AZURE_OPENAI_ENDPOINT"],
        rate_limit_rpm=60,
        description="Enterprise GPT via Azure",
        docs_url="https://azure.microsoft.com/en-us/products/ai-services/openai-service"
    ),
    
    # Weather
    "openweathermap": APIConfig(
        name="OpenWeatherMap",
        env_key="OPENWEATHERMAP_API_KEY",
        base_url="https://api.openweathermap.org/data/2.5",
        rate_limit_rpm=60,
        description="Weather forecasts for demand modeling",
        docs_url="https://openweathermap.org/api"
    ),
    "visual_crossing": APIConfig(
        name="Visual Crossing Weather",
        env_key="VISUAL_CROSSING_API_KEY",
        base_url="https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services",
        rate_limit_rpm=60,
        description="Historical weather data",
        docs_url="https://www.visualcrossing.com/"
    ),
    "tomorrow_io": APIConfig(
        name="Tomorrow.io",
        env_key="TOMORROW_IO_API_KEY",
        base_url="https://api.tomorrow.io/v4",
        rate_limit_rpm=60,
        description="Minute-by-minute weather forecasts",
        docs_url="https://www.tomorrow.io/"
    ),
    "smhi": APIConfig(
        name="SMHI Open Data",
        env_key="SMHI_API_KEY",
        base_url="https://opendata-download-metfcst.smhi.se/api",
        rate_limit_rpm=60,
        requires_key=False,  # SMHI is free
        description="Swedish Meteorological data",
        docs_url="https://opendata.smhi.se/"
    ),
    
    # News & Sentiment
    "newsapi": APIConfig(
        name="NewsAPI",
        env_key="NEWS_API_KEY",
        base_url="https://newsapi.org/v2",
        rate_limit_rpm=100,
        description="News headlines and sentiment",
        docs_url="https://newsapi.org/"
    ),
    "gnews": APIConfig(
        name="GNews",
        env_key="GNEWS_API_KEY",
        base_url="https://gnews.io/api/v4",
        rate_limit_rpm=100,
        description="Alternative news API",
        docs_url="https://gnews.io/"
    ),
    "event_registry": APIConfig(
        name="Event Registry",
        env_key="EVENT_REGISTRY_API_KEY",
        base_url="https://eventregistry.org/api/v1",
        rate_limit_rpm=60,
        description="Global news events",
        docs_url="https://eventregistry.org/"
    ),
    
    # Energy Data
    "nordpool": APIConfig(
        name="Nord Pool",
        env_key="NORDPOOL_API_KEY",
        base_url="https://data.nordpoolgroup.com/api",
        rate_limit_rpm=60,
        description="Nordic electricity spot prices",
        docs_url="https://data.nordpoolgroup.com/"
    ),
    "entsoe": APIConfig(
        name="ENTSO-E",
        env_key="ENTSOE_API_KEY",
        base_url="https://web-api.tp.entsoe.eu/api",
        rate_limit_rpm=60,
        description="European electricity transparency",
        docs_url="https://transparency.entsoe.eu/"
    ),
    "eia": APIConfig(
        name="EIA",
        env_key="EIA_API_KEY",
        base_url="https://api.eia.gov/v2",
        rate_limit_rpm=60,
        description="US Energy Information Administration",
        docs_url="https://www.eia.gov/opendata/"
    ),
    "electricity_maps": APIConfig(
        name="Electricity Maps",
        env_key="ELECTRICITY_MAPS_API_KEY",
        base_url="https://api.electricitymap.org/v3",
        rate_limit_rpm=30,
        description="Real-time carbon intensity",
        docs_url="https://www.electricitymaps.com/"
    ),
    
    # Commodities & Markets
    "commodities_api": APIConfig(
        name="Commodities API",
        env_key="COMMODITIES_API_KEY",
        base_url="https://commodities-api.com/api",
        rate_limit_rpm=60,
        description="Oil, gas, carbon prices",
        docs_url="https://commodities-api.com/"
    ),
    "finnhub": APIConfig(
        name="Finnhub",
        env_key="FINNHUB_API_KEY",
        base_url="https://finnhub.io/api/v1",
        rate_limit_rpm=60,
        description="Real-time stock/forex data",
        docs_url="https://finnhub.io/"
    ),
    "alpha_vantage": APIConfig(
        name="Alpha Vantage",
        env_key="ALPHA_VANTAGE_API_KEY",
        base_url="https://www.alphavantage.co/query",
        rate_limit_rpm=5,  # Free tier is very limited
        description="Stock and forex data",
        docs_url="https://www.alphavantage.co/"
    ),
    "polygon": APIConfig(
        name="Polygon.io",
        env_key="POLYGON_API_KEY",
        base_url="https://api.polygon.io/v2",
        rate_limit_rpm=60,
        description="Market data",
        docs_url="https://polygon.io/"
    ),
    
    # Economic Data
    "fred": APIConfig(
        name="FRED",
        env_key="FRED_API_KEY",
        base_url="https://api.stlouisfed.org/fred",
        rate_limit_rpm=120,
        description="Federal Reserve Economic Data",
        docs_url="https://fred.stlouisfed.org/docs/api/"
    ),
    "scb": APIConfig(
        name="SCB (Statistics Sweden)",
        env_key="",  # No key needed
        base_url="https://api.scb.se/OV0104/v1/doris/sv/ssd",
        rate_limit_rpm=60,
        requires_key=False,
        description="Swedish official statistics",
        docs_url="https://www.scb.se/"
    ),
    "eurostat": APIConfig(
        name="Eurostat",
        env_key="",
        base_url="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0",
        rate_limit_rpm=60,
        requires_key=False,
        description="EU statistics",
        docs_url="https://ec.europa.eu/eurostat/"
    ),
    
    # Notifications
    "slack": APIConfig(
        name="Slack",
        env_key="SLACK_WEBHOOK_URL",
        rate_limit_rpm=60,
        description="Alert notifications via Slack",
        docs_url="https://api.slack.com/"
    ),
    "telegram": APIConfig(
        name="Telegram",
        env_key="TELEGRAM_BOT_TOKEN",
        env_keys=["TELEGRAM_CHAT_ID"],
        base_url="https://api.telegram.org",
        rate_limit_rpm=30,
        description="Mobile alerts via Telegram",
        docs_url="https://core.telegram.org/bots/api"
    ),
}


# =============================================================================
# BASE API PROVIDER
# =============================================================================

class BaseAPIProvider(ABC):
    """Abstract base class for API providers with automatic key detection."""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self._cache: dict[str, tuple[datetime, Any]] = {}
        self._call_count = 0
        self._last_call: Optional[datetime] = None
        self._error_count = 0
        self._status = APIStatus.DISABLED
        
        # Load API key from environment
        self._api_key = os.getenv(config.env_key, "").strip() if config.env_key else None
        self._additional_keys: dict[str, str] = {}
        
        for key_name in config.env_keys:
            self._additional_keys[key_name] = os.getenv(key_name, "").strip()
        
        # Determine status
        self._update_status()
    
    def _update_status(self) -> None:
        """Update provider status based on configuration."""
        if not self.config.requires_key:
            self._status = APIStatus.ENABLED
        elif self._api_key:
            # Check if additional required keys are present
            all_keys_present = all(
                self._additional_keys.get(k) 
                for k in self.config.env_keys
            )
            if all_keys_present or not self.config.env_keys:
                self._status = APIStatus.ENABLED
            else:
                self._status = APIStatus.DISABLED
        else:
            self._status = APIStatus.SIMULATED
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def is_enabled(self) -> bool:
        """Check if API is enabled (has valid key)."""
        return self._status == APIStatus.ENABLED
    
    @property
    def is_simulated(self) -> bool:
        """Check if using simulated data."""
        return self._status == APIStatus.SIMULATED
    
    @property
    def status(self) -> APIStatus:
        return self._status
    
    @property
    def api_key(self) -> Optional[str]:
        return self._api_key
    
    @property
    def call_count(self) -> int:
        return self._call_count
    
    def get_status_info(self) -> dict:
        """Get status information for this provider."""
        return {
            "name": self.name,
            "status": self._status.value,
            "enabled": self.is_enabled,
            "simulated": self.is_simulated,
            "calls": self._call_count,
            "errors": self._error_count,
            "last_call": self._last_call.isoformat() if self._last_call else None,
            "env_key": self.config.env_key,
            "requires_key": self.config.requires_key,
        }
    
    async def _rate_limit(self) -> None:
        """Apply rate limiting."""
        if self._last_call:
            elapsed = (datetime.now() - self._last_call).total_seconds()
            min_interval = 60.0 / self.config.rate_limit_rpm
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
    
    async def _cached_request(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        json_data: Optional[dict] = None,
        ttl_seconds: Optional[int] = None
    ) -> dict:
        """Make a cached HTTP request with rate limiting."""
        cache_key = f"{method}:{url}:{params}:{json_data}"
        ttl = ttl_seconds or self.config.cache_ttl_seconds
        
        # Check cache
        if cache_key in self._cache:
            cached_time, data = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=ttl):
                logger.debug(f"{self.name}: Cache hit for {url}")
                return data
        
        # Rate limit
        await self._rate_limit()
        
        # Make request
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, params=params, headers=headers, json=json_data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                data = response.json()
                
                self._cache[cache_key] = (datetime.now(), data)
                self._call_count += 1
                self._last_call = datetime.now()
                self._error_count = 0  # Reset on success
                
                logger.debug(f"{self.name}: API call successful ({self._call_count} total)")
                return data
                
        except httpx.HTTPStatusError as e:
            self._error_count += 1
            if e.response.status_code == 429:
                self._status = APIStatus.RATE_LIMITED
                logger.warning(f"{self.name}: Rate limited")
            else:
                logger.warning(f"{self.name}: HTTP error {e.response.status_code}")
            raise
        except Exception as e:
            self._error_count += 1
            if self._error_count >= 3:
                self._status = APIStatus.ERROR
            logger.warning(f"{self.name}: Request error: {e}")
            raise
    
    @abstractmethod
    async def fetch(self, **kwargs) -> Any:
        """Fetch data from the API. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def simulate(self, **kwargs) -> Any:
        """Return simulated data when API is not available."""
        pass
    
    async def get_data(self, **kwargs) -> tuple[Any, bool]:
        """
        Get data, using real API if enabled or simulation if not.
        
        Returns:
            Tuple of (data, is_real_data)
        """
        if self.is_enabled:
            try:
                data = await self.fetch(**kwargs)
                return data, True
            except Exception as e:
                logger.warning(f"{self.name}: Falling back to simulation due to: {e}")
                return self.simulate(**kwargs), False
        else:
            return self.simulate(**kwargs), False


# =============================================================================
# CONCRETE API PROVIDERS
# =============================================================================

class GoogleTrendsProvider(BaseAPIProvider):
    """Google Trends via SerpAPI."""
    
    def __init__(self):
        super().__init__(API_CONFIGS["serpapi"])
    
    async def fetch(
        self,
        keywords: list[str],
        geo: str = "SE",
        timeframe: str = "today 3-m"
    ) -> dict[str, list[dict]]:
        """Fetch real Google Trends data via SerpAPI."""
        results = {}
        
        for keyword in keywords:
            data = await self._cached_request(
                "GET",
                self.config.base_url,
                params={
                    "engine": "google_trends",
                    "q": keyword,
                    "geo": geo,
                    "data_type": "TIMESERIES",
                    "api_key": self.api_key
                }
            )
            
            # Parse SerpAPI response
            timeline = data.get("interest_over_time", {}).get("timeline_data", [])
            results[keyword] = [
                {"date": item.get("date"), "value": item.get("values", [{}])[0].get("value", 0)}
                for item in timeline
            ]
        
        return results
    
    def simulate(
        self,
        keywords: list[str],
        geo: str = "SE",
        timeframe: str = "today 3-m"
    ) -> dict[str, list[dict]]:
        """Generate simulated trends data."""
        results = {}
        base_date = datetime.now() - timedelta(days=90)
        
        for keyword in keywords:
            trend_data = []
            base_interest = random.randint(20, 60)
            trend = random.uniform(-0.5, 0.5)
            
            for day in range(90):
                date = base_date + timedelta(days=day)
                seasonal = 10 * math.sin(day * 2 * math.pi / 30)
                weekly = 5 * math.sin(day * 2 * math.pi / 7)
                value = base_interest + trend * day + seasonal + weekly + random.gauss(0, 5)
                value = max(0, min(100, value))
                
                trend_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "value": round(value),
                    "keyword": keyword
                })
            
            results[keyword] = trend_data
        
        return results


class NewsAPIProvider(BaseAPIProvider):
    """News headlines and sentiment."""
    
    def __init__(self):
        super().__init__(API_CONFIGS["newsapi"])
    
    async def fetch(
        self,
        query: str,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 10
    ) -> list[dict]:
        """Fetch real news articles."""
        data = await self._cached_request(
            "GET",
            f"{self.config.base_url}/everything",
            params={
                "q": query,
                "language": language,
                "sortBy": sort_by,
                "pageSize": page_size,
                "apiKey": self.api_key
            }
        )
        return data.get("articles", [])
    
    def simulate(
        self,
        query: str,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 10
    ) -> list[dict]:
        """Generate simulated news data."""
        templates = [
            f"Energy markets react to {query} developments",
            f"Nordic electricity prices shift amid {query}",
            f"Analysts predict impact of {query} on Swedish grid",
            f"Swedish energy sector braces for {query} effects",
            f"EU energy ministers discuss {query} implications",
        ]
        
        return [
            {
                "title": templates[i % len(templates)],
                "description": f"Analysis of {query} and its effects on energy markets.",
                "source": {"name": f"Energy News {i+1}"},
                "publishedAt": (datetime.now() - timedelta(hours=i*2)).isoformat(),
                "sentiment": random.uniform(-0.5, 0.5),
                "url": f"https://example.com/news/{i+1}"
            }
            for i in range(min(page_size, 5))
        ]


class WeatherProvider(BaseAPIProvider):
    """Weather data for demand and renewable forecasting."""
    
    SWEDISH_ZONES = {
        "SE1": {"name": "Luleå", "lat": 65.58, "lon": 22.15},
        "SE2": {"name": "Sundsvall", "lat": 62.39, "lon": 17.31},
        "SE3": {"name": "Stockholm", "lat": 59.33, "lon": 18.07},
        "SE4": {"name": "Malmö", "lat": 55.60, "lon": 13.00},
    }
    
    def __init__(self):
        super().__init__(API_CONFIGS["openweathermap"])
    
    async def fetch(self, zone: str = "SE3") -> dict:
        """Fetch real weather data."""
        city = self.SWEDISH_ZONES.get(zone, self.SWEDISH_ZONES["SE3"])
        
        data = await self._cached_request(
            "GET",
            f"{self.config.base_url}/weather",
            params={
                "lat": city["lat"],
                "lon": city["lon"],
                "appid": self.api_key,
                "units": "metric"
            }
        )
        
        return {
            "temp": data.get("main", {}).get("temp", 10),
            "wind_speed": data.get("wind", {}).get("speed", 5),
            "clouds": data.get("clouds", {}).get("all", 50),
            "description": data.get("weather", [{}])[0].get("description", "unknown"),
            "humidity": data.get("main", {}).get("humidity", 70),
        }
    
    def simulate(self, zone: str = "SE3") -> dict:
        """Generate simulated weather data."""
        city = self.SWEDISH_ZONES.get(zone, self.SWEDISH_ZONES["SE3"])
        month = datetime.now().month
        
        # Seasonal temperature
        base_temp = 10 - abs(month - 7) * 3
        lat_adjustment = (city["lat"] - 59) * -0.5
        
        return {
            "temp": round(base_temp + lat_adjustment + random.gauss(0, 3), 1),
            "wind_speed": round(random.uniform(2, 12), 1),
            "clouds": random.randint(20, 80),
            "description": random.choice(["clear sky", "partly cloudy", "overcast", "light rain"]),
            "humidity": random.randint(50, 90),
        }


class CommodityProvider(BaseAPIProvider):
    """Commodity prices (oil, gas, carbon)."""
    
    def __init__(self):
        super().__init__(API_CONFIGS["commodities_api"])
    
    async def fetch(self) -> dict[str, float]:
        """Fetch real commodity prices."""
        data = await self._cached_request(
            "GET",
            f"{self.config.base_url}/latest",
            params={
                "access_key": self.api_key,
                "symbols": "BRENTOIL,NG,COAL"
            }
        )
        
        rates = data.get("data", {}).get("rates", {})
        return {
            "brent_crude_usd": rates.get("BRENTOIL", 75.0),
            "natural_gas_eur_mwh": rates.get("NG", 35.0),
            "coal_usd_ton": rates.get("COAL", 120.0),
            "co2_eur_ton": 65.0,  # Typically from different source
        }
    
    def simulate(self) -> dict[str, float]:
        """Generate simulated commodity prices."""
        return {
            "brent_crude_usd": 75.0 + random.gauss(0, 5),
            "natural_gas_eur_mwh": 35.0 + random.gauss(0, 8),
            "coal_usd_ton": 120.0 + random.gauss(0, 10),
            "co2_eur_ton": 65.0 + random.gauss(0, 5),
        }


class NordPoolProvider(BaseAPIProvider):
    """Nordic electricity spot prices."""
    
    def __init__(self):
        super().__init__(API_CONFIGS["nordpool"])
    
    async def fetch(self, zones: list[str] = None) -> dict[str, float]:
        """Fetch real Nord Pool prices."""
        zones = zones or ["SE1", "SE2", "SE3", "SE4"]
        
        # Nord Pool API structure varies - this is a simplified example
        data = await self._cached_request(
            "GET",
            f"{self.config.base_url}/dayahead/prices",
            params={"areas": ",".join(zones)},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        return {zone: data.get(zone, 50.0) for zone in zones}
    
    def simulate(self, zones: list[str] = None) -> dict[str, float]:
        """Generate simulated Nord Pool prices."""
        zones = zones or ["SE1", "SE2", "SE3", "SE4"]
        base_prices = {"SE1": 35, "SE2": 40, "SE3": 50, "SE4": 55}
        
        return {
            zone: base_prices.get(zone, 45) + random.gauss(0, 10)
            for zone in zones
        }


class SMHIProvider(BaseAPIProvider):
    """Swedish Meteorological and Hydrological Institute data."""
    
    def __init__(self):
        super().__init__(API_CONFIGS["smhi"])
    
    async def fetch(self, lat: float = 59.33, lon: float = 18.07) -> dict:
        """Fetch real SMHI forecast."""
        data = await self._cached_request(
            "GET",
            f"{self.config.base_url}/category/pmp3g/version/2/geotype/point/lon/{lon}/lat/{lat}/data.json"
        )
        
        # Parse SMHI response
        time_series = data.get("timeSeries", [])
        if time_series:
            current = time_series[0]
            params = {p["name"]: p["values"][0] for p in current.get("parameters", [])}
            return {
                "temp": params.get("t", 10),
                "wind_speed": params.get("ws", 5),
                "precipitation": params.get("pmean", 0),
                "cloud_cover": params.get("tcc_mean", 50),
            }
        return self.simulate(lat, lon)
    
    def simulate(self, lat: float = 59.33, lon: float = 18.07) -> dict:
        """Generate simulated SMHI data."""
        month = datetime.now().month
        base_temp = 10 - abs(month - 7) * 3
        lat_adjustment = (lat - 59) * -0.5
        
        return {
            "temp": round(base_temp + lat_adjustment + random.gauss(0, 3), 1),
            "wind_speed": round(random.uniform(2, 12), 1),
            "precipitation": round(random.uniform(0, 5), 1),
            "cloud_cover": random.randint(20, 80),
        }


class OpenAIProvider(BaseAPIProvider):
    """OpenAI for agent reasoning."""
    
    def __init__(self):
        super().__init__(API_CONFIGS["openai"])
    
    async def fetch(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 500
    ) -> str:
        """Call OpenAI API."""
        data = await self._cached_request(
            "POST",
            f"{self.config.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json_data={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            },
            ttl_seconds=0  # Don't cache LLM responses
        )
        
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    def simulate(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 500
    ) -> str:
        """Return a simulated LLM response."""
        return f"[Simulated response - OpenAI not configured] Analysis of: {prompt[:100]}..."


class FinnhubProvider(BaseAPIProvider):
    """Real-time market data."""
    
    def __init__(self):
        super().__init__(API_CONFIGS["finnhub"])
    
    async def fetch(self, symbol: str = "EQNR") -> dict:
        """Fetch stock quote."""
        data = await self._cached_request(
            "GET",
            f"{self.config.base_url}/quote",
            params={"symbol": symbol, "token": self.api_key}
        )
        return {
            "current": data.get("c", 0),
            "high": data.get("h", 0),
            "low": data.get("l", 0),
            "open": data.get("o", 0),
            "previous_close": data.get("pc", 0),
            "change": data.get("d", 0),
            "change_percent": data.get("dp", 0),
        }
    
    def simulate(self, symbol: str = "EQNR") -> dict:
        """Generate simulated stock data."""
        base_price = 300.0
        change = random.gauss(0, 5)
        return {
            "current": base_price + change,
            "high": base_price + abs(change) + random.uniform(1, 5),
            "low": base_price - abs(change) - random.uniform(1, 5),
            "open": base_price,
            "previous_close": base_price - random.uniform(-3, 3),
            "change": change,
            "change_percent": (change / base_price) * 100,
        }


# =============================================================================
# API REGISTRY (SINGLETON)
# =============================================================================

class APIRegistry:
    """
    Central registry for all API providers.
    
    Singleton pattern - use get_registry() to get the instance.
    """
    
    _instance: Optional['APIRegistry'] = None
    
    def __init__(self):
        self._providers: dict[str, BaseAPIProvider] = {}
        self._initialized = False
    
    @classmethod
    def get_instance(cls) -> 'APIRegistry':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize(self) -> None:
        """Initialize all providers."""
        if self._initialized:
            return
        
        # Register all providers
        self._providers = {
            "google_trends": GoogleTrendsProvider(),
            "news": NewsAPIProvider(),
            "weather": WeatherProvider(),
            "commodities": CommodityProvider(),
            "nordpool": NordPoolProvider(),
            "smhi": SMHIProvider(),
            "openai": OpenAIProvider(),
            "finnhub": FinnhubProvider(),
        }
        
        self._initialized = True
        
        # Log status
        enabled = [n for n, p in self._providers.items() if p.is_enabled]
        simulated = [n for n, p in self._providers.items() if p.is_simulated]
        
        logger.info(f"API Registry initialized: {len(enabled)} enabled, {len(simulated)} simulated")
        if enabled:
            logger.info(f"  Enabled APIs: {', '.join(enabled)}")
        if simulated:
            logger.debug(f"  Simulated APIs: {', '.join(simulated)}")
    
    def get_provider(self, name: str) -> Optional[BaseAPIProvider]:
        """Get a provider by name."""
        if not self._initialized:
            self.initialize()
        return self._providers.get(name)
    
    def get_all_providers(self) -> dict[str, BaseAPIProvider]:
        """Get all providers."""
        if not self._initialized:
            self.initialize()
        return self._providers.copy()
    
    def get_enabled_providers(self) -> dict[str, BaseAPIProvider]:
        """Get only enabled providers."""
        return {n: p for n, p in self.get_all_providers().items() if p.is_enabled}
    
    def get_simulated_providers(self) -> dict[str, BaseAPIProvider]:
        """Get only simulated providers."""
        return {n: p for n, p in self.get_all_providers().items() if p.is_simulated}
    
    def get_status_report(self) -> dict:
        """Get status report for all providers."""
        if not self._initialized:
            self.initialize()
        
        return {
            "total": len(self._providers),
            "enabled": len(self.get_enabled_providers()),
            "simulated": len(self.get_simulated_providers()),
            "providers": {
                name: provider.get_status_info()
                for name, provider in self._providers.items()
            }
        }
    
    def print_status(self) -> None:
        """Print a formatted status report."""
        report = self.get_status_report()
        
        print("\n" + "=" * 60)
        print("API PROVIDER STATUS")
        print("=" * 60)
        print(f"Total: {report['total']} | Enabled: {report['enabled']} | Simulated: {report['simulated']}")
        print("-" * 60)
        
        for name, info in report['providers'].items():
            status_icon = "✅" if info['enabled'] else ("🔶" if info['simulated'] else "❌")
            env_hint = f"({info['env_key']})" if info['env_key'] else "(no key needed)"
            print(f"{status_icon} {info['name']:30} {info['status']:12} {env_hint}")
        
        print("=" * 60 + "\n")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_registry() -> APIRegistry:
    """Get the API registry singleton."""
    return APIRegistry.get_instance()


def get_api(name: str) -> Optional[BaseAPIProvider]:
    """Get an API provider by name."""
    return get_registry().get_provider(name)


async def fetch_with_fallback(api_name: str, **kwargs) -> tuple[Any, bool]:
    """
    Fetch data from an API with automatic fallback to simulation.
    
    Returns:
        Tuple of (data, is_real_data)
    """
    provider = get_api(api_name)
    if provider:
        return await provider.get_data(**kwargs)
    logger.warning(f"Unknown API: {api_name}")
    return None, False


def is_api_enabled(name: str) -> bool:
    """Check if an API is enabled."""
    provider = get_api(name)
    return provider.is_enabled if provider else False


def get_api_status() -> dict:
    """Get status of all APIs."""
    return get_registry().get_status_report()


def print_api_status() -> None:
    """Print formatted API status."""
    get_registry().print_status()


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_apis():
        # Initialize and show status
        registry = get_registry()
        registry.initialize()
        registry.print_status()
        
        # Test a few providers
        print("\nTesting providers:")
        
        # Weather
        weather = get_api("weather")
        data, is_real = await weather.get_data(zone="SE3")
        print(f"Weather (real={is_real}): {data}")
        
        # Trends
        trends = get_api("google_trends")
        data, is_real = await trends.get_data(keywords=["electricity price"])
        print(f"Trends (real={is_real}): {len(data.get('electricity price', []))} data points")
        
        # News
        news = get_api("news")
        data, is_real = await news.get_data(query="energy crisis")
        print(f"News (real={is_real}): {len(data)} articles")
    
    asyncio.run(test_apis())
