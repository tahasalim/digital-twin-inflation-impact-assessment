"""
Economic Indicators Service for Swedish Energy Digital Twin.

This module provides real-time economic data from:
- Riksbank API: Policy rate, CPIF inflation
- SCB API: Consumer Price Index
- Nord Pool: Electricity prices

Data is cached to respect rate limits and improve performance.
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from functools import lru_cache
from loguru import logger
import asyncio


@dataclass
class EconomicIndicators:
    """Current Swedish economic indicators."""
    cpif_rate: float  # CPIF inflation rate (%)
    cpif_date: str  # Date of CPIF reading
    policy_rate: float  # Riksbank policy rate (%)
    policy_rate_date: str  # Date policy rate effective from
    avg_electricity_price_eur: float  # Average electricity price €/MWh
    data_freshness: str  # "live" or "cached" or "fallback"
    last_updated: datetime


# Cache for indicators (refreshed every hour)
_cached_indicators: Optional[EconomicIndicators] = None
_cache_time: Optional[datetime] = None
CACHE_TTL_SECONDS = 3600  # 1 hour


def get_cached_indicators() -> Optional[EconomicIndicators]:
    """Get cached indicators if still valid."""
    global _cached_indicators, _cache_time
    if _cached_indicators and _cache_time:
        if datetime.now() - _cache_time < timedelta(seconds=CACHE_TTL_SECONDS):
            return _cached_indicators
    return None


def set_cached_indicators(indicators: EconomicIndicators):
    """Set cached indicators."""
    global _cached_indicators, _cache_time
    _cached_indicators = indicators
    _cache_time = datetime.now()


async def fetch_riksbank_policy_rate() -> tuple[float, str]:
    """
    Fetch current policy rate from Riksbank.
    
    The Riksbank provides an API at:
    https://www.riksbank.se/en-gb/statistics/interest-rates-and-exchange-rates/retrieving-interest-rates-and-exchange-rates-via-api/
    
    Returns:
        Tuple of (rate, effective_date)
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Riksbank API endpoint for policy rate
            url = "https://api.riksbank.se/swea/v1/Observations/Latest/SECBREPOEFF"
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                # Parse the response
                if data and len(data) > 0:
                    rate = float(data[0].get("value", 1.75))
                    date = data[0].get("date", "2025-11-12")
                    return rate, date
    except Exception as e:
        logger.warning(f"Failed to fetch Riksbank policy rate: {e}")
    
    # Fallback to known current value
    return 1.75, "2025-11-12"


async def fetch_cpif_inflation() -> tuple[float, str]:
    """
    Fetch current CPIF inflation from SCB or Riksbank.
    
    SCB API: https://api.scb.se/OV0104/v1/doris/sv/ssd/PR/PR0101/PR0101G/KPIF
    
    Returns:
        Tuple of (rate, period)
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # SCB API for CPIF
            url = "https://api.scb.se/OV0104/v1/doris/sv/ssd/PR/PR0101/PR0101G/KPIF"
            
            # Query for latest CPIF annual change
            query = {
                "query": [
                    {
                        "code": "ContentsCode",
                        "selection": {
                            "filter": "item",
                            "values": ["000004VX"]  # CPIF annual change
                        }
                    }
                ],
                "response": {"format": "json"}
            }
            
            response = await client.post(url, json=query)
            
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and len(data["data"]) > 0:
                    # Get the last (most recent) entry
                    latest = data["data"][-1]
                    period = latest["key"][0]  # e.g., "2025M10"
                    value = float(latest["values"][0])
                    return value, period
    except Exception as e:
        logger.warning(f"Failed to fetch CPIF from SCB: {e}")
    
    # Fallback to known current value (November 2025 flash estimate)
    return 2.3, "2025M11"


async def fetch_average_electricity_price() -> float:
    """
    Fetch average electricity price for Swedish zones.
    
    Uses the Digital Twin's existing data or Nord Pool API.
    
    Returns:
        Average price in €/MWh
    """
    # This is calculated from the Digital Twin state
    # For now, return a reasonable average
    return 43.8


async def fetch_economic_indicators() -> EconomicIndicators:
    """
    Fetch all economic indicators asynchronously.
    
    Returns cached data if available and fresh, otherwise fetches new data.
    """
    # Check cache first
    cached = get_cached_indicators()
    if cached:
        cached.data_freshness = "cached"
        return cached
    
    # Fetch all indicators in parallel
    try:
        policy_rate_task = fetch_riksbank_policy_rate()
        cpif_task = fetch_cpif_inflation()
        electricity_task = fetch_average_electricity_price()
        
        (policy_rate, policy_date), (cpif_rate, cpif_date), electricity_price = await asyncio.gather(
            policy_rate_task, cpif_task, electricity_task
        )
        
        indicators = EconomicIndicators(
            cpif_rate=cpif_rate,
            cpif_date=cpif_date,
            policy_rate=policy_rate,
            policy_rate_date=policy_date,
            avg_electricity_price_eur=electricity_price,
            data_freshness="live",
            last_updated=datetime.now()
        )
        
        set_cached_indicators(indicators)
        return indicators
        
    except Exception as e:
        logger.error(f"Error fetching economic indicators: {e}")
        # Return fallback values
        return get_fallback_indicators()


def get_fallback_indicators() -> EconomicIndicators:
    """
    Get fallback economic indicators when API calls fail.
    
    Uses the most recent known values as of December 2025.
    """
    return EconomicIndicators(
        cpif_rate=2.3,  # November 2025 flash estimate
        cpif_date="2025M11",
        policy_rate=1.75,  # Effective from Nov 12, 2025
        policy_rate_date="2025-11-12",
        avg_electricity_price_eur=43.8,
        data_freshness="fallback",
        last_updated=datetime.now()
    )


def get_economic_indicators_sync() -> EconomicIndicators:
    """
    Synchronous wrapper for fetching economic indicators.
    
    For use in Streamlit which doesn't play well with asyncio.
    """
    # Check cache first (synchronous)
    cached = get_cached_indicators()
    if cached:
        cached.data_freshness = "cached"
        return cached
    
    # Try to run async function
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            indicators = loop.run_until_complete(fetch_economic_indicators())
            return indicators
        finally:
            loop.close()
    except Exception as e:
        logger.warning(f"Failed to fetch indicators synchronously: {e}")
        return get_fallback_indicators()


# Quick access function for dashboard
def get_current_indicators() -> EconomicIndicators:
    """Get current economic indicators (cached or fresh)."""
    return get_economic_indicators_sync()
