"""
Centralized Scenario Configuration Component

Provides a unified configuration panel for all dashboard tabs.
Features:
- Single source of truth for scenario settings
- Duration flexibility (hours, days, weeks, months)
- Parameter tweaking (supply adjustments, demand modifications)
- Custom promptable scenarios
- LLM-powered natural language outputs
"""

import streamlit as st
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class DurationUnit(Enum):
    """Duration unit options."""
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"


@dataclass
class ScenarioConfig:
    """Unified scenario configuration."""
    # Core settings
    trigger: str
    duration_value: int
    duration_unit: DurationUnit
    magnitude: float
    
    # Custom scenario
    custom_prompt: Optional[str]
    
    # Parameter adjustments
    supply_adjustment_pct: float  # -100 to +100%
    demand_adjustment_pct: float  # -100 to +100%
    import_capacity_pct: float    # Capacity utilization %
    
    # Zone-specific adjustments
    zone_adjustments: Dict[str, float]  # SE1-SE4 adjustments
    
    # Advanced options
    include_weather: bool
    include_commodity_prices: bool
    include_policy_events: bool
    
    def get_duration_hours(self) -> int:
        """Convert duration to hours."""
        if self.duration_unit == DurationUnit.HOURS:
            return self.duration_value
        elif self.duration_unit == DurationUnit.DAYS:
            return self.duration_value * 24
        elif self.duration_unit == DurationUnit.WEEKS:
            return self.duration_value * 24 * 7
        elif self.duration_unit == DurationUnit.MONTHS:
            return self.duration_value * 24 * 30  # Approximate
        return self.duration_value
    
    def get_duration_display(self) -> str:
        """Get human-readable duration string."""
        hours = self.get_duration_hours()
        if hours < 24:
            return f"{hours} hours"
        elif hours < 168:
            days = hours / 24
            return f"{days:.1f} days ({hours} hours)"
        elif hours < 720:
            weeks = hours / 168
            return f"{weeks:.1f} weeks ({hours} hours)"
        else:
            months = hours / 720
            return f"{months:.1f} months ({hours} hours)"
    
    def to_prompt_context(self) -> str:
        """Generate prompt context for LLM agents."""
        prompt_parts = [
            f"Scenario: {self.trigger.replace('_', ' ').title()}",
            f"Duration: {self.get_duration_display()}",
            f"Magnitude: {self.magnitude:.1f}x",
        ]
        
        if self.supply_adjustment_pct != 0:
            prompt_parts.append(f"Supply Adjustment: {self.supply_adjustment_pct:+.1f}%")
        if self.demand_adjustment_pct != 0:
            prompt_parts.append(f"Demand Adjustment: {self.demand_adjustment_pct:+.1f}%")
        if self.import_capacity_pct != 100:
            prompt_parts.append(f"Import Capacity: {self.import_capacity_pct:.0f}%")
        
        for zone, adj in self.zone_adjustments.items():
            if adj != 0:
                prompt_parts.append(f"{zone} Adjustment: {adj:+.1f}%")
        
        if self.custom_prompt:
            prompt_parts.append(f"Custom Scenario: {self.custom_prompt}")
        
        return "\n".join(prompt_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "trigger": self.trigger,
            "duration_value": self.duration_value,
            "duration_unit": self.duration_unit.value,
            "duration_hours": self.get_duration_hours(),
            "magnitude": self.magnitude,
            "custom_prompt": self.custom_prompt,
            "supply_adjustment_pct": self.supply_adjustment_pct,
            "demand_adjustment_pct": self.demand_adjustment_pct,
            "import_capacity_pct": self.import_capacity_pct,
            "zone_adjustments": self.zone_adjustments,
            "include_weather": self.include_weather,
            "include_commodity_prices": self.include_commodity_prices,
            "include_policy_events": self.include_policy_events,
        }


# Scenario trigger options with descriptions
SCENARIO_TRIGGERS = {
    "nordic_drought": {
        "name": "Nordic Drought",
        "icon": "🏜️",
        "description": "Severe drought affecting hydropower reservoirs across Nordic region",
        "affected_supply": ["hydro"],
        "default_magnitude": 1.5,
    },
    "nuclear_outage": {
        "name": "Nuclear Outage",
        "icon": "☢️",
        "description": "Unplanned shutdown of nuclear reactors (Forsmark, Ringhals, or Oskarshamn)",
        "affected_supply": ["nuclear"],
        "default_magnitude": 2.0,
    },
    "cold_wave": {
        "name": "Extreme Cold Wave",
        "icon": "❄️",
        "description": "Severe cold weather event increasing heating demand",
        "affected_demand": ["residential", "industrial"],
        "default_magnitude": 1.8,
    },
    "wind_lull": {
        "name": "Wind Generation Lull",
        "icon": "🌬️",
        "description": "Extended period of low wind conditions",
        "affected_supply": ["wind"],
        "default_magnitude": 1.3,
    },
    "gas_supply_shock": {
        "name": "Gas Supply Shock",
        "icon": "🔥",
        "description": "Disruption to natural gas supply affecting backup generation",
        "affected_supply": ["gas", "backup"],
        "default_magnitude": 2.0,
    },
    "transmission_failure": {
        "name": "Transmission Grid Failure",
        "icon": "⚡",
        "description": "Major transmission line or interconnector outage",
        "affected_grid": ["transmission"],
        "default_magnitude": 1.7,
    },
    "cyber_attack": {
        "name": "Cyber Attack",
        "icon": "🔐",
        "description": "Cyber attack on grid infrastructure or control systems",
        "affected_grid": ["control", "scada"],
        "default_magnitude": 2.5,
    },
    "price_spike": {
        "name": "Market Price Spike",
        "icon": "📈",
        "description": "Extreme electricity price volatility in spot market",
        "affected_market": ["spot", "intraday"],
        "default_magnitude": 1.5,
    },
    "se1_hacked": {
        "name": "SE1 Zone Compromised",
        "icon": "🚨",
        "description": "Complete compromise of SE1 (Luleå) zone infrastructure",
        "affected_zones": ["SE1"],
        "default_magnitude": 3.0,
    },
    "custom": {
        "name": "Custom Scenario",
        "icon": "✏️",
        "description": "Define your own scenario with custom parameters",
        "custom": True,
        "default_magnitude": 1.0,
    },
}


def inject_config_css():
    """Inject CSS styling for the configuration panel."""
    st.markdown("""
    <style>
    /* Scenario Configuration Panel - Professional Design */
    .config-panel {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .config-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .scenario-card {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        transition: all 0.2s ease;
    }
    
    .scenario-card:hover {
        border-color: #003366;
        box-shadow: 0 2px 8px rgba(0, 51, 102, 0.1);
    }
    
    .scenario-card.selected {
        border-color: #003366;
        background: rgba(0, 51, 102, 0.05);
    }
    
    .param-section {
        background: #F9FAFB;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .param-label {
        color: #6B7280;
        font-size: 0.85rem;
        margin-bottom: 5px;
    }
    
    .param-value {
        color: #003366;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .duration-pills {
        display: flex;
        gap: 10px;
        margin: 10px 0;
    }
    
    .duration-pill {
        padding: 8px 16px;
        border-radius: 4px;
        border: 1px solid #E5E7EB;
        background: white;
        color: #374151;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .duration-pill.active {
        background: #003366;
        color: white;
        border-color: #003366;
    }
    
    .custom-prompt-box {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
    }
    
    .zone-adjuster {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px;
        background: #F9FAFB;
        border-radius: 6px;
        margin: 5px 0;
    }
    
    .zone-label {
        width: 60px;
        font-weight: 600;
    }
    
    /* Professional zone colors */
    .zone-se1 { color: #059669; }
    .zone-se2 { color: #0891b2; }
    .zone-se3 { color: #0066cc; }
    .zone-se4 { color: #7c3aed; }
    </style>
    """, unsafe_allow_html=True)


def init_config_state():
    """Initialize configuration state in session."""
    if "scenario_config" not in st.session_state:
        st.session_state.scenario_config = None
    if "config_trigger" not in st.session_state:
        st.session_state.config_trigger = "nordic_drought"
    if "config_duration_value" not in st.session_state:
        st.session_state.config_duration_value = 24
    if "config_duration_unit" not in st.session_state:
        st.session_state.config_duration_unit = DurationUnit.HOURS.value
    if "config_magnitude" not in st.session_state:
        st.session_state.config_magnitude = 1.0
    if "config_custom_prompt" not in st.session_state:
        st.session_state.config_custom_prompt = ""
    if "config_supply_adj" not in st.session_state:
        st.session_state.config_supply_adj = 0.0
    if "config_demand_adj" not in st.session_state:
        st.session_state.config_demand_adj = 0.0
    if "config_import_cap" not in st.session_state:
        st.session_state.config_import_cap = 100.0
    if "config_zone_adj" not in st.session_state:
        st.session_state.config_zone_adj = {"SE1": 0.0, "SE2": 0.0, "SE3": 0.0, "SE4": 0.0}
    if "config_include_weather" not in st.session_state:
        st.session_state.config_include_weather = True
    if "config_include_commodities" not in st.session_state:
        st.session_state.config_include_commodities = True
    if "config_include_policy" not in st.session_state:
        st.session_state.config_include_policy = False


def get_current_config() -> ScenarioConfig:
    """Get current configuration from session state."""
    init_config_state()
    
    return ScenarioConfig(
        trigger=st.session_state.config_trigger,
        duration_value=st.session_state.config_duration_value,
        duration_unit=DurationUnit(st.session_state.config_duration_unit),
        magnitude=st.session_state.config_magnitude,
        custom_prompt=st.session_state.config_custom_prompt if st.session_state.config_custom_prompt else None,
        supply_adjustment_pct=st.session_state.config_supply_adj,
        demand_adjustment_pct=st.session_state.config_demand_adj,
        import_capacity_pct=st.session_state.config_import_cap,
        zone_adjustments=st.session_state.config_zone_adj.copy(),
        include_weather=st.session_state.config_include_weather,
        include_commodity_prices=st.session_state.config_include_commodities,
        include_policy_events=st.session_state.config_include_policy,
    )


def render_scenario_config(compact: bool = False, show_run_button: bool = True) -> Tuple[Optional[ScenarioConfig], bool]:
    """
    Render the centralized scenario configuration panel.
    
    Args:
        compact: If True, render a more compact version
        show_run_button: If True, show the run analysis button
    
    Returns:
        Tuple of (ScenarioConfig, run_clicked)
    """
    inject_config_css()
    init_config_state()
    
    run_clicked = False
    
    st.markdown('<div class="config-panel">', unsafe_allow_html=True)
    st.markdown('<div class="config-header">⚙️ Scenario Configuration</div>', unsafe_allow_html=True)
    
    if compact:
        # Compact single-row layout
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        
        with col1:
            trigger_options = {k: f"{v['icon']} {v['name']}" for k, v in SCENARIO_TRIGGERS.items()}
            selected = st.selectbox(
                "Scenario",
                options=list(trigger_options.keys()),
                format_func=lambda x: trigger_options[x],
                key="config_trigger",
            )
        
        with col2:
            duration_unit = st.selectbox(
                "Time Scale",
                options=[u.value for u in DurationUnit],
                format_func=lambda x: x.capitalize(),
                key="config_duration_unit",
            )
        
        with col3:
            unit = DurationUnit(duration_unit)
            if unit == DurationUnit.HOURS:
                max_val, default_val = 168, 24
            elif unit == DurationUnit.DAYS:
                max_val, default_val = 90, 7
            elif unit == DurationUnit.WEEKS:
                max_val, default_val = 52, 4
            else:  # MONTHS
                max_val, default_val = 24, 3
            
            st.number_input(
                f"Duration ({unit.value})",
                min_value=1,
                max_value=max_val,
                value=min(st.session_state.config_duration_value, max_val),
                key="config_duration_value",
            )
        
        with col4:
            st.slider(
                "Magnitude",
                min_value=0.5,
                max_value=3.0,
                step=0.1,
                key="config_magnitude",
            )
        
        with col5:
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            if show_run_button:
                run_clicked = st.button("🚀 Run", type="primary", use_container_width=True)
    
    else:
        # Full detailed layout
        tab1, tab2, tab3 = st.tabs(["🎯 Scenario", "🔧 Parameters", "✏️ Custom"])
        
        with tab1:
            # Scenario selection grid
            cols = st.columns(3)
            trigger_keys = list(SCENARIO_TRIGGERS.keys())
            
            for i, key in enumerate(trigger_keys):
                with cols[i % 3]:
                    info = SCENARIO_TRIGGERS[key]
                    is_selected = st.session_state.config_trigger == key
                    
                    if st.button(
                        f"{info['icon']} {info['name']}",
                        key=f"scenario_btn_{key}",
                        type="primary" if is_selected else "secondary",
                        use_container_width=True,
                    ):
                        st.session_state.config_trigger = key
                        st.session_state.config_magnitude = info.get("default_magnitude", 1.0)
                        st.rerun()
            
            # Show selected scenario description
            selected_info = SCENARIO_TRIGGERS[st.session_state.config_trigger]
            st.info(f"**{selected_info['name']}**: {selected_info['description']}")
            
            # Duration configuration
            st.markdown("### ⏱️ Duration")
            col1, col2 = st.columns(2)
            
            with col1:
                duration_unit = st.selectbox(
                    "Time Scale",
                    options=[u.value for u in DurationUnit],
                    format_func=lambda x: x.capitalize(),
                    key="config_duration_unit",
                    help="Select the time unit for simulation duration",
                )
            
            with col2:
                unit = DurationUnit(duration_unit)
                if unit == DurationUnit.HOURS:
                    max_val, default_val, step = 168, 24, 1
                    help_text = "1-168 hours (up to 1 week)"
                elif unit == DurationUnit.DAYS:
                    max_val, default_val, step = 90, 7, 1
                    help_text = "1-90 days (up to 3 months)"
                elif unit == DurationUnit.WEEKS:
                    max_val, default_val, step = 52, 4, 1
                    help_text = "1-52 weeks (up to 1 year)"
                else:  # MONTHS
                    max_val, default_val, step = 24, 3, 1
                    help_text = "1-24 months (up to 2 years)"
                
                st.number_input(
                    f"Duration ({unit.value})",
                    min_value=1,
                    max_value=max_val,
                    value=min(st.session_state.config_duration_value, max_val),
                    step=step,
                    key="config_duration_value",
                    help=help_text,
                )
            
            # Show duration summary
            config = get_current_config()
            st.caption(f"📅 Total simulation duration: **{config.get_duration_display()}**")
            
            # Magnitude
            st.markdown("### 📊 Event Magnitude")
            st.slider(
                "Intensity Multiplier",
                min_value=0.5,
                max_value=3.0,
                step=0.1,
                key="config_magnitude",
                help="1.0 = normal intensity, 2.0 = double intensity, 3.0 = extreme",
            )
            
            magnitude = st.session_state.config_magnitude
            if magnitude < 1.0:
                st.caption("🟢 Mild scenario - Below normal intensity")
            elif magnitude < 1.5:
                st.caption("🟡 Moderate scenario - Normal to elevated intensity")
            elif magnitude < 2.0:
                st.caption("🟠 High scenario - Significant stress on system")
            else:
                st.caption("🔴 Extreme scenario - Critical stress level")
        
        with tab2:
            st.markdown("### 📉 Supply Adjustments")
            
            st.slider(
                "Supply Capacity Adjustment",
                min_value=-50.0,
                max_value=50.0,
                step=5.0,
                key="config_supply_adj",
                help="Adjust total supply capacity. Negative = reduction, Positive = increase",
                format="%+.0f%%",
            )
            
            st.markdown("### 📈 Demand Adjustments")
            
            st.slider(
                "Demand Level Adjustment",
                min_value=-50.0,
                max_value=50.0,
                step=5.0,
                key="config_demand_adj",
                help="Adjust overall demand. Negative = reduction, Positive = increase",
                format="%+.0f%%",
            )
            
            st.markdown("### 🔌 Import Capacity")
            
            st.slider(
                "Import Capacity Utilization",
                min_value=0.0,
                max_value=150.0,
                step=10.0,
                key="config_import_cap",
                help="100% = normal capacity, <100% = reduced imports, >100% = emergency imports",
                format="%.0f%%",
            )
            
            st.markdown("### Zone-Specific Adjustments")
            
            # Professional zone colors
            zone_colors = {"SE1": "#059669", "SE2": "#0891b2", "SE3": "#0066cc", "SE4": "#7c3aed"}
            zone_names = {"SE1": "Luleå (North)", "SE2": "Sundsvall", "SE3": "Stockholm", "SE4": "Malmö (South)"}
            
            cols = st.columns(2)
            for i, (zone, color) in enumerate(zone_colors.items()):
                with cols[i % 2]:
                    # Initialize zone key if not exists
                    zone_key = f"zone_adj_{zone}"
                    if zone_key not in st.session_state:
                        st.session_state[zone_key] = 0.0
                    
                    st.slider(
                        f"{zone}: {zone_names[zone]}",
                        min_value=-100.0,
                        max_value=100.0,
                        step=5.0,
                        key=zone_key,
                        format="%+.0f%%",
                    )
                    # Sync back to config_zone_adj
                    st.session_state.config_zone_adj[zone] = st.session_state[zone_key]
            
            st.markdown("### Data Sources")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.checkbox("Include Weather Data", key="config_include_weather")
            with col2:
                st.checkbox("Include Commodity Prices", key="config_include_commodities")
            with col3:
                st.checkbox("Include Policy Events", key="config_include_policy")
        
        with tab3:
            st.markdown("### Custom Scenario Prompt")
            st.caption("Describe a custom scenario in natural language. The AI agents will interpret and simulate it.")
            
            st.text_area(
                "Scenario Description",
                placeholder="Example: 'SE1 is completely hacked for 72 hours, causing total blackout in the northern region while a cold wave hits Stockholm...'",
                key="config_custom_prompt",
                height=150,
            )
            
            if st.session_state.config_custom_prompt:
                st.success("✅ Custom scenario will be used in addition to selected trigger")
                
                # Show interpreted parameters
                with st.expander("📋 Preview Scenario Context"):
                    config = get_current_config()
                    st.code(config.to_prompt_context(), language="text")
            
            st.markdown("### 💡 Example Scenarios")
            
            examples = [
                ("🏜️ Drought + Cold", "Nordic drought reduces hydro capacity by 40% while a severe cold wave increases heating demand by 30%"),
                ("☢️ Nuclear Crisis", "All three nuclear plants (Forsmark, Ringhals, Oskarshamn) experience simultaneous unplanned outages"),
                ("🔐 Cyber Attack", "SE1 zone is completely compromised by cyber attack for 72 hours, losing all SCADA control"),
                ("⚡ Perfect Storm", "Combination of low wind, nuclear outage, and extreme cold creates critical supply shortage"),
            ]
            
            for emoji_title, description in examples:
                if st.button(emoji_title, key=f"example_{emoji_title}"):
                    st.session_state.config_custom_prompt = description
                    st.rerun()
        
        # Run button for full layout
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if show_run_button:
                run_clicked = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get final config
    config = get_current_config()
    st.session_state.scenario_config = config
    
    return config, run_clicked


def render_config_summary():
    """Render a summary of current configuration (for sidebar or compact display)."""
    config = get_current_config()
    trigger_info = SCENARIO_TRIGGERS.get(config.trigger, {})
    
    st.markdown(f"""
    <div style="background: rgba(0,51,102,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #003366;">
        <div style="font-size: 1.1rem; font-weight: 600; color: #003366; margin-bottom: 10px;">
            {trigger_info.get('icon', '⚙️')} Current Scenario
        </div>
        <div style="color: #111827; font-weight: 500;">{trigger_info.get('name', config.trigger)}</div>
        <div style="color: #6B7280; font-size: 0.85rem; margin-top: 5px;">
            Duration: {config.get_duration_display()}<br>
            Magnitude: {config.magnitude:.1f}x<br>
            Supply Adj: {config.supply_adjustment_pct:+.0f}%<br>
            Demand Adj: {config.demand_adjustment_pct:+.0f}%
        </div>
        {f'<div style="color: #059669; font-size: 0.85rem; margin-top: 8px;">📝 Custom prompt active</div>' if config.custom_prompt else ''}
    </div>
    """, unsafe_allow_html=True)


# Export
__all__ = [
    "ScenarioConfig",
    "DurationUnit",
    "SCENARIO_TRIGGERS",
    "render_scenario_config",
    "render_config_summary",
    "get_current_config",
    "inject_config_css",
    "init_config_state",
]
