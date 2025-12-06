"""
Swedish Inflation Energy Digital Twin - Design System

Provides consistent styling across the dashboard with:
- Professional Bloomberg-inspired aesthetic
- Proper color contrast (dark text on light backgrounds)
- Reusable components
- Typography scale
- Semantic color usage
"""

from .modern_design import (
    COLORS,
    TYPOGRAPHY,
    ZONE_COLORS,
    ZONE_COLOR_LIST,
    get_main_css,
)

# Alias for compatibility
get_professional_css = get_main_css

# Legacy exports for backwards compatibility
from .riksbank_modern import (
    render_header,
    render_info_banner,
)

__all__ = [
    # Modern Design System
    "COLORS",
    "TYPOGRAPHY",
    "ZONE_COLORS",
    "ZONE_COLOR_LIST",
    "get_professional_css",
    "get_main_css",
    # Legacy
    "render_header",
    "render_info_banner",
]
