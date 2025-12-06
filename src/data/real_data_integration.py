"""
Real Data Integration for Swedish Energy Digital Twin.

This module bridges real-world data sources with the simulation engine,
providing actual market prices, weather conditions, and economic indicators
instead of hardcoded values.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from loguru import logger

from src.data.sources import (
    get_data_aggregator,
    DataAggregator,
    PriceZone,
    SpotPrice,
    EconomicIndicator,
    WeatherData,
)
from src.models.energy import ZoneId


@dataclass
class RealTimeMarketData:
    """Container for real-time market data."""
    
    # Electricity prices by zone (EUR/MWh)
    spot_prices: Dict[str, float] = field(default_factory=dict)
    
    # Weather by zone
    weather: Dict[str, WeatherData] = field(default_factory=dict)
    
    # Economic indicators
    cpi_yoy: Optional[float] = None
    price_expectations: Optional[float] = None
    oil_price_usd: Optional[float] = None
    
    # News sentiment
    news_sentiment: float = 0.0
    
    # Metadata
    fetch_timestamp: Optional[datetime] = None
    sources_used: Dict[str, bool] = field(default_factory=dict)
    is_live_data: bool = False
    
    # Fallback values (used when real data unavailable)
    FALLBACK_PRICES = {
        "SE1": 25.0,
        "SE2": 35.0,
        "SE3": 50.0,
        "SE4": 65.0,
    }
    
    def get_price(self, zone: str) -> float:
        """Get price for zone, falling back to default if unavailable."""
        return self.spot_prices.get(zone, self.FALLBACK_PRICES.get(zone, 50.0))
    
    def get_weather_temp(self, zone: str) -> float:
        """Get temperature for zone, with seasonal fallback."""
        if zone in self.weather and self.weather[zone]:
            return self.weather[zone].temperature_c
        # Seasonal fallback based on current month
        month = datetime.now().month
        # Swedish seasonal averages
        if month in [12, 1, 2]:  # Winter
            return {"SE1": -15, "SE2": -10, "SE3": -3, "SE4": 0}.get(zone, -5)
        elif month in [6, 7, 8]:  # Summer
            return {"SE1": 15, "SE2": 18, "SE3": 20, "SE4": 22}.get(zone, 18)
        else:  # Spring/Autumn
            return {"SE1": 5, "SE2": 8, "SE3": 10, "SE4": 12}.get(zone, 8)


class RealDataIntegration:
    """
    Fetches and caches real-time data from all available sources.
    
    Uses a tiered approach:
    1. Try to fetch from real APIs
    2. Fall back to cached data if API fails
    3. Fall back to reasonable defaults if no data available
    """
    
    # Cache duration
    CACHE_TTL_SECONDS = 300  # 5 minutes for prices
    WEATHER_CACHE_TTL = 1800  # 30 minutes for weather
    
    def __init__(self):
        self._aggregator: Optional[DataAggregator] = None
        self._cache: Optional[RealTimeMarketData] = None
        self._cache_time: Optional[datetime] = None
    
    @property
    def aggregator(self) -> DataAggregator:
        if self._aggregator is None:
            self._aggregator = get_data_aggregator()
        return self._aggregator
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache is None or self._cache_time is None:
            return False
        return (datetime.now() - self._cache_time).total_seconds() < self.CACHE_TTL_SECONDS
    
    async def fetch_market_data(self, force_refresh: bool = False) -> RealTimeMarketData:
        """
        Fetch current market data from all sources.
        
        Returns cached data if available and not expired.
        """
        if not force_refresh and self._is_cache_valid():
            logger.debug("Using cached market data")
            return self._cache
        
        logger.info("Fetching real-time market data from APIs...")
        
        data = RealTimeMarketData(
            fetch_timestamp=datetime.now(),
            sources_used=self.aggregator.get_available_sources(),
        )
        
        # Fetch all data concurrently
        try:
            prices, weather, inflation, news = await asyncio.gather(
                self._fetch_prices(),
                self._fetch_weather(),
                self._fetch_inflation(),
                self._fetch_news_sentiment(),
                return_exceptions=True,
            )
            
            # Process prices
            if isinstance(prices, dict) and prices:
                data.spot_prices = prices
                data.is_live_data = True
                logger.info(f"✓ Fetched live prices: {prices}")
            else:
                logger.warning(f"Using fallback prices (fetch returned: {type(prices)})")
                data.spot_prices = data.FALLBACK_PRICES.copy()
            
            # Process weather
            if isinstance(weather, dict) and weather:
                data.weather = weather
                logger.info(f"✓ Fetched weather for {len(weather)} zones")
            
            # Process inflation
            if isinstance(inflation, dict):
                data.cpi_yoy = inflation.get("cpi_yoy")
                data.price_expectations = inflation.get("price_expectations")
                data.oil_price_usd = inflation.get("oil_price_usd")
                if data.cpi_yoy is not None:
                    logger.info(f"✓ Fetched CPI: {data.cpi_yoy}%")
            
            # Process news sentiment
            if isinstance(news, dict):
                data.news_sentiment = news.get("avg_sentiment", 0)
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            data.spot_prices = data.FALLBACK_PRICES.copy()
        
        # Update cache
        self._cache = data
        self._cache_time = datetime.now()
        
        return data
    
    async def _fetch_prices(self) -> Dict[str, float]:
        """Fetch electricity prices from Nord Pool."""
        try:
            return await self.aggregator.get_current_electricity_prices()
        except Exception as e:
            logger.warning(f"Failed to fetch prices: {e}")
            return {}
    
    async def _fetch_weather(self) -> Dict[str, WeatherData]:
        """Fetch weather from SMHI."""
        try:
            return await self.aggregator.get_weather_impact()
        except Exception as e:
            logger.warning(f"Failed to fetch weather: {e}")
            return {}
    
    async def _fetch_inflation(self) -> Dict[str, Any]:
        """Fetch inflation indicators."""
        try:
            return await self.aggregator.get_inflation_indicators()
        except Exception as e:
            logger.warning(f"Failed to fetch inflation data: {e}")
            return {}
    
    async def _fetch_news_sentiment(self) -> Dict[str, Any]:
        """Fetch news sentiment."""
        try:
            return await self.aggregator.get_news_sentiment()
        except Exception as e:
            logger.warning(f"Failed to fetch news: {e}")
            return {}
    
    def get_cached_data(self) -> Optional[RealTimeMarketData]:
        """Get currently cached data (may be stale)."""
        return self._cache
    
    def get_baseline_prices_from_real_data(self) -> Dict[ZoneId, float]:
        """
        Get baseline prices for the simulation from real data.
        
        Returns dict mapping ZoneId to price in EUR/MWh.
        """
        if self._cache is None:
            return {
                ZoneId.SE1: 25.0,
                ZoneId.SE2: 35.0,
                ZoneId.SE3: 50.0,
                ZoneId.SE4: 65.0,
            }
        
        return {
            ZoneId.SE1: self._cache.get_price("SE1"),
            ZoneId.SE2: self._cache.get_price("SE2"),
            ZoneId.SE3: self._cache.get_price("SE3"),
            ZoneId.SE4: self._cache.get_price("SE4"),
        }
    
    def get_weather_demand_modifier(self, zone: str) -> float:
        """
        Calculate demand modifier based on temperature.
        
        Cold weather increases heating demand.
        Hot weather increases cooling demand.
        Mild weather (10-18°C) is baseline.
        
        Returns a multiplier (1.0 = baseline).
        """
        if self._cache is None:
            return 1.0
        
        temp = self._cache.get_weather_temp(zone)
        
        # Swedish demand is primarily heating-driven
        if temp < -10:
            return 1.25  # Very cold - 25% more demand
        elif temp < 0:
            return 1.15  # Cold - 15% more demand
        elif temp < 10:
            return 1.05  # Cool - 5% more demand
        elif temp < 18:
            return 1.0   # Mild - baseline
        elif temp < 25:
            return 1.02  # Warm - slight AC load
        else:
            return 1.08  # Hot - AC demand
    
    def get_economic_context(self) -> Dict[str, Any]:
        """Get economic context for the simulation."""
        if self._cache is None:
            return {
                "cpi_yoy": None,
                "oil_price": None,
                "sentiment": "neutral",
            }
        
        # Classify sentiment
        if self._cache.news_sentiment > 0.2:
            sentiment = "positive"
        elif self._cache.news_sentiment < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "cpi_yoy": self._cache.cpi_yoy,
            "oil_price": self._cache.oil_price_usd,
            "sentiment": sentiment,
            "price_expectations": self._cache.price_expectations,
        }


# Singleton instance
_integration: Optional[RealDataIntegration] = None


def get_real_data_integration() -> RealDataIntegration:
    """Get the singleton RealDataIntegration instance."""
    global _integration
    if _integration is None:
        _integration = RealDataIntegration()
    return _integration


async def fetch_real_data() -> RealTimeMarketData:
    """Convenience function to fetch real-time data."""
    integration = get_real_data_integration()
    return await integration.fetch_market_data()


def get_cached_real_data() -> Optional[RealTimeMarketData]:
    """Get cached real-time data (non-async)."""
    integration = get_real_data_integration()
    return integration.get_cached_data()
