"""
Swedish Energy Digital Twin - Dashboard Components

Modular components for the Streamlit dashboard:
- Multi-Agent View: Hierarchical agent visualization with breakpoints
- Summary View: Unified executive summary aggregating all subsystems
- Scenario Config: Centralized scenario configuration panel
- Agent Outputs: LLM-powered agent reasoning visualization
"""

from .multi_agent_view import render_multi_agent_view, inject_multi_agent_css
from .summary_view import render_summary_view, inject_summary_css, aggregate_scenario_data
from .scenario_config import (
    render_scenario_config,
    render_config_summary,
    get_current_config,
    inject_config_css,
    init_config_state,
    ScenarioConfig,
    DurationUnit,
    SCENARIO_TRIGGERS,
)
from .agent_outputs import (
    render_agent_output_card,
    render_all_agent_outputs,
    generate_agent_reasoning,
    inject_agent_output_css,
    AgentReasoning,
)
from .what_if_view import render_what_if_view, inject_what_if_css

__all__ = [
    # Multi-agent view
    "render_multi_agent_view",
    "inject_multi_agent_css",
    # Summary view
    "render_summary_view",
    "inject_summary_css",
    "aggregate_scenario_data",
    # Scenario config
    "render_scenario_config",
    "render_config_summary",
    "get_current_config",
    "inject_config_css",
    "init_config_state",
    "ScenarioConfig",
    "DurationUnit",
    "SCENARIO_TRIGGERS",
    # Agent outputs
    "render_agent_output_card",
    "render_all_agent_outputs",
    "generate_agent_reasoning",
    "inject_agent_output_css",
    "AgentReasoning",
    # What If view
    "render_what_if_view",
    "inject_what_if_css",
]
