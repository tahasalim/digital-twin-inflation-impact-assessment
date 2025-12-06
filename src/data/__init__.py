"""
Data module for Swedish Energy Digital Twin.

Provides connectors to real-world data sources for:
- Electricity prices (Nord Pool)
- Swedish economic statistics (SCB, NIER)
- International data (FRED, ECB)
- Weather data
- News sentiment
"""

from src.data.sources import (
    DataAggregator,
    get_data_aggregator,
    NordPoolClient,
    SCBClient,
    NIERClient,
    FREDClient,
    WeatherClient,
    NewsClient,
    SpotPrice,
    EconomicIndicator,
    WeatherData,
    NewsSentiment,
    PriceZone,
)

__all__ = [
    "DataAggregator",
    "get_data_aggregator",
    "NordPoolClient",
    "SCBClient",
    "NIERClient",
    "FREDClient",
    "WeatherClient",
    "NewsClient",
    "SpotPrice",
    "EconomicIndicator",
    "WeatherData",
    "NewsSentiment",
    "PriceZone",
]
