"""
API Provider module for Swedish Energy Digital Twin.

Provides centralized API management with:
- Automatic enable/disable based on API key availability
- Graceful fallback to simulated data
- Rate limiting and caching
- Health monitoring
"""

from .providers import (
    # Core classes
    APIRegistry,
    BaseAPIProvider,
    APIConfig,
    APIStatus,
    
    # Providers
    GoogleTrendsProvider,
    NewsAPIProvider,
    WeatherProvider,
    CommodityProvider,
    NordPoolProvider,
    SMHIProvider,
    OpenAIProvider,
    FinnhubProvider,
    
    # Convenience functions
    get_registry,
    get_api,
    fetch_with_fallback,
    is_api_enabled,
    get_api_status,
    print_api_status,
    
    # Configs
    API_CONFIGS,
)

__all__ = [
    # Core classes
    "APIRegistry",
    "BaseAPIProvider",
    "APIConfig",
    "APIStatus",
    
    # Providers
    "GoogleTrendsProvider",
    "NewsAPIProvider",
    "WeatherProvider",
    "CommodityProvider",
    "NordPoolProvider",
    "SMHIProvider",
    "OpenAIProvider",
    "FinnhubProvider",
    
    # Convenience functions
    "get_registry",
    "get_api",
    "fetch_with_fallback",
    "is_api_enabled",
    "get_api_status",
    "print_api_status",
    
    # Configs
    "API_CONFIGS",
]
