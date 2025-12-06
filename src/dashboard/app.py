"""
Swedish Inflation Energy Digital Twin - Interactive Dashboard

AI-Powered Economic Scenario Analysis for Riksbanken.

Real-time visualization of:
- Swedish electricity zones (SE1-SE4)
- Timeline-based simulation with playable time slider
- Multi-agent economic impact analysis
- Domino effect visualization
- Inflation forecasting with alternative data sources
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import time

# Add repo root to path for Streamlit Cloud compatibility
import sys
from pathlib import Path
# Go up from app.py -> dashboard -> src -> repo root
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from src.twin.engine import get_twin_engine
from src.agents.energy_agents import EnergyMarketModel
from src.simulation.scenarios import get_all_scenarios, ScenarioBuilder
from src.simulation.timeline import (
    TimelineSimulator,
    Timeline,
    SystemSnapshot,
    SimulationEvent,
    SimulationSummary,
    KeyMoment,
    EVENT_TEMPLATES,
    get_event_template,
    list_event_templates,
)
from src.orchestrator.agent import get_orchestrator
from src.models.energy import ZoneId, EventType
from src.agents.multi_agent import (
    get_multi_agent_system,
    MultiAgentSystem,
    AgentRole,
    AgentStatus,
    DomainCategory,
)

# Import economic indicators service
try:
    from src.data.economic_indicators import get_current_indicators, EconomicIndicators
    ECONOMIC_INDICATORS_AVAILABLE = True
except ImportError:
    ECONOMIC_INDICATORS_AVAILABLE = False

# Import new dashboard components
try:
    from src.dashboard.components import (
        render_multi_agent_view,
        render_summary_view,
        inject_multi_agent_css,
        inject_summary_css,
        # Centralized config
        render_scenario_config,
        render_config_summary,
        get_current_config,
        init_config_state,
        inject_config_css,
        # Agent outputs
        render_all_agent_outputs,
        inject_agent_output_css,
        # What If view
        render_what_if_view,
        inject_what_if_css,
    )
    NEW_COMPONENTS_AVAILABLE = True
except ImportError:
    NEW_COMPONENTS_AVAILABLE = False

# Import modern design system
try:
    from src.dashboard.styles.modern_design import (
        get_main_css,
        COLORS,
        TYPOGRAPHY,
        ZONE_COLORS,
        ZONE_COLOR_LIST,
    )
    # Legacy imports for compatibility
    from src.dashboard.styles.riksbank_modern import (
        render_header,
        render_key_metrics_header,
    )
    
    MODERN_STYLES_AVAILABLE = True
except ImportError:
    MODERN_STYLES_AVAILABLE = False
    COLORS = {
        "primary_600": "#003366",
        "primary_400": "#0066cc",
        "primary_300": "#3399ff",
        "text_primary": "#e7e9ea",
        "text_secondary": "#8899a6",
        "text_tertiary": "#536471",
        "success": "#2d6a4f",
        "success_text": "#74c69d",
        "warning": "#7c5e10",
        "warning_text": "#fbbf24",
        "danger": "#7f1d1d",
        "danger_text": "#f87171",
    }
    ZONE_COLORS = {"SE1": "#059669", "SE2": "#0891b2", "SE3": "#0066cc", "SE4": "#7c3aed"}
    ZONE_COLOR_LIST = ["#059669", "#0891b2", "#0066cc", "#7c3aed"]


# Page config
st.set_page_config(
    page_title="Swedish Inflation Energy Digital Twin",
    page_icon="🇸🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply modern CSS
if MODERN_STYLES_AVAILABLE:
    st.markdown(get_main_css(), unsafe_allow_html=True)
else:
    # Fallback basic CSS
    st.markdown("""
    <style>
        .stMetric {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #003366;
        }
    </style>
    """, unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "twin_initialized" not in st.session_state:
        st.session_state.twin_initialized = False
    if "current_scenario" not in st.session_state:
        st.session_state.current_scenario = None
    if "domino_effects" not in st.session_state:
        st.session_state.domino_effects = []
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
    if "simulation_results" not in st.session_state:
        st.session_state.simulation_results = None
    # Timeline simulation state
    if "timeline" not in st.session_state:
        st.session_state.timeline = None
    if "current_hour" not in st.session_state:
        st.session_state.current_hour = 0
    if "is_playing" not in st.session_state:
        st.session_state.is_playing = False
    if "play_speed" not in st.session_state:
        st.session_state.play_speed = 0.3
    if "selected_events" not in st.session_state:
        st.session_state.selected_events = ["nordic_drought"]
    # Multi-agent system state
    if "multi_agent_result" not in st.session_state:
        st.session_state.multi_agent_result = None
    if "multi_agent_running" not in st.session_state:
        st.session_state.multi_agent_running = False
    
    # Initialize centralized scenario config state
    if NEW_COMPONENTS_AVAILABLE:
        try:
            init_config_state()
        except Exception:
            pass  # Fallback if config not available


def initialize_twin():
    """Initialize the digital twin engine."""
    if not st.session_state.twin_initialized:
        twin = get_twin_engine()
        twin.initialize()
        orchestrator = get_orchestrator()
        orchestrator.initialize()
        st.session_state.twin_initialized = True


def create_sweden_map():
    """Create an interactive map of Swedish electricity zones."""
    
    twin = get_twin_engine()
    reality = twin.get_reality()
    
    # Zone coordinates (approximate centroids)
    zone_data = {
        "zone": ["SE1", "SE2", "SE3", "SE4"],
        "name": ["Luleå (North)", "Sundsvall", "Stockholm", "Malmö (South)"],
        "lat": [66.5, 62.5, 59.3, 55.6],
        "lon": [20.5, 17.5, 18.0, 13.0],
        "price": [
            reality.zones[ZoneId.SE1].spot_price_eur_mwh,
            reality.zones[ZoneId.SE2].spot_price_eur_mwh,
            reality.zones[ZoneId.SE3].spot_price_eur_mwh,
            reality.zones[ZoneId.SE4].spot_price_eur_mwh,
        ],
        "production": [
            reality.zones[ZoneId.SE1].current_production_mw,
            reality.zones[ZoneId.SE2].current_production_mw,
            reality.zones[ZoneId.SE3].current_production_mw,
            reality.zones[ZoneId.SE4].current_production_mw,
        ],
        "consumption": [
            reality.zones[ZoneId.SE1].current_consumption_mw,
            reality.zones[ZoneId.SE2].current_consumption_mw,
            reality.zones[ZoneId.SE3].current_consumption_mw,
            reality.zones[ZoneId.SE4].current_consumption_mw,
        ],
    }
    
    df = pd.DataFrame(zone_data)
    df["net_position"] = df["production"] - df["consumption"]
    df["size"] = df["price"] * 2  # Size based on price
    
    # Create map
    fig = go.Figure()
    
    # Add zone markers - use professional zone colors
    colors = ZONE_COLOR_LIST
    
    for i, row in df.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[row["lon"]],
            lat=[row["lat"]],
            mode="markers+text",
            marker=dict(
                size=max(20, row["price"] * 0.5),
                color=colors[i],
                opacity=0.8,
                line=dict(width=2, color="white"),
            ),
            text=f"{row['zone']}<br>€{row['price']:.0f}/MWh",
            textposition="top center",
            name=row["zone"],
            hovertemplate=(
                f"<b>{row['zone']} - {row['name']}</b><br>"
                f"Price: €{row['price']:.1f}/MWh<br>"
                f"Production: {row['production']:.0f} MW<br>"
                f"Consumption: {row['consumption']:.0f} MW<br>"
                f"Net: {row['net_position']:+.0f} MW<br>"
                "<extra></extra>"
            ),
        ))
    
    # Add flow arrows between zones (simplified)
    flows = [
        (66.5, 20.5, 62.5, 17.5, "SE1→SE2"),
        (62.5, 17.5, 59.3, 18.0, "SE2→SE3"),
        (59.3, 18.0, 55.6, 13.0, "SE3→SE4"),
    ]
    
    for lat1, lon1, lat2, lon2, name in flows:
        fig.add_trace(go.Scattergeo(
            lon=[lon1, lon2],
            lat=[lat1, lat2],
            mode="lines",
            line=dict(width=3, color=COLORS["primary_400"]),
            opacity=0.5,
            name=name,
            showlegend=False,
        ))
    
    fig.update_layout(
        title="🇸🇪 Swedish Electricity Zones",
        geo=dict(
            scope="europe",
            center=dict(lat=62, lon=17),
            projection_scale=5,
            showland=True,
            landcolor="rgb(30, 30, 30)",
            showocean=True,
            oceancolor="rgb(20, 20, 40)",
            showlakes=True,
            lakecolor="rgb(30, 30, 50)",
            showcountries=True,
            countrycolor="rgb(60, 60, 60)",
        ),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF"),
        margin=dict(l=0, r=0, t=40, b=0),
        height=500,
    )
    
    return fig


def create_zone_metrics():
    """Create metric cards for each zone."""
    twin = get_twin_engine()
    reality = twin.get_reality()
    
    cols = st.columns(4)
    
    zone_colors = {
        ZoneId.SE1: "🟢",
        ZoneId.SE2: "🟡",
        ZoneId.SE3: "🟠",
        ZoneId.SE4: "🔴",
    }
    
    for i, zone_id in enumerate(ZoneId):
        zone = reality.zones[zone_id]
        with cols[i]:
            st.markdown(f"### {zone_colors[zone_id]} {zone_id.value} - {zone.name}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Spot Price",
                    f"€{zone.spot_price_eur_mwh:.1f}/MWh",
                    delta=f"{(zone.spot_price_eur_mwh - 50):.1f}" if zone.spot_price_eur_mwh != 50 else None,
                )
            with col2:
                net = zone.net_position_mw
                st.metric(
                    "Net Position",
                    f"{net:+.0f} MW",
                    delta="Exporting" if net > 0 else "Importing",
                    delta_color="normal" if net > 0 else "inverse",
                )
            
            # Energy mix bar
            mix_data = pd.DataFrame({
                "Source": ["Hydro", "Nuclear", "Wind", "Other"],
                "Share": [zone.hydro_share, zone.nuclear_share, zone.wind_share, zone.other_share],
            })
            
            fig = px.bar(
                mix_data,
                x="Share",
                y="Source",
                orientation="h",
                color="Source",
                color_discrete_map={
                    "Hydro": COLORS["primary_400"],
                    "Nuclear": COLORS["danger_text"],
                    "Wind": COLORS["success_text"],
                    "Other": COLORS["text_tertiary"],
                },
            )
            fig.update_layout(
                height=120,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis=dict(range=[0, 1], showticklabels=False),
                yaxis=dict(showticklabels=True),
                paper_bgcolor="#000000",
                plot_bgcolor="#000000",
                font=dict(color="#FFFFFF"),
            )
            st.plotly_chart(fig, use_container_width=True)


def run_scenario_simulation(scenario_name: str):
    """Run a scenario and display results."""
    
    with st.spinner(f"Running simulation: {scenario_name}..."):
        orchestrator = get_orchestrator()
        results = orchestrator.run_scenario_analysis(scenario_name)
        
        st.session_state.current_scenario = scenario_name
        st.session_state.simulation_results = results
        st.session_state.domino_effects = results["domino_effects"]["effects"]
    
    return results


def display_domino_effects():
    """Display domino effects as a cascade flow: Precursors → Event → After-Effects."""
    
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.875rem; font-weight: 400; color: #B0B0B0; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;">
            Cascade Analysis
        </div>
        <h1 style="font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 900; color: #FFFFFF; margin: 0; line-height: 1;">
            Domino Effects
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.domino_effects:
        st.markdown("""
        <div style="background: transparent; border: 1px solid #1A1A1A; padding: 1.5rem; margin: 1rem 0;">
            <div style="color: #B0B0B0; font-size: 0.875rem;">Run a simulation from the Executive Summary tab to see domino effects.</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    effects = st.session_state.domino_effects
    
    # Get the current trigger scenario
    trigger = st.session_state.get("current_trigger", "nordic_drought")
    trigger_labels = {
        "nordic_drought": "DROUGHT",
        "nuclear_outage": "NUCLEAR OUTAGE",
        "cold_wave": "COLD WAVE",
        "wind_lull": "WIND LULL",
        "gas_crisis": "GAS CRISIS",
        "cable_failure": "CABLE FAILURE",
    }
    central_event = trigger_labels.get(trigger, "ENERGY SHOCK")
    
    st.markdown("### 🎯 Cascade Flow Diagram")
    st.markdown("<p style='color: #808080; font-size: 0.875rem;'>Precursor conditions → Central Event → Propagated Effects</p>", unsafe_allow_html=True)
    
    # Build cascade structure: Precursors → Event → After-Effects
    # Use dynamically generated precursors from LLM or template
    
    # Get precursors from session state (generated by LLM/template)
    if hasattr(st.session_state, 'domino_precursors') and st.session_state.domino_precursors:
        # Convert from LLM format to display format
        raw_precursors = st.session_state.domino_precursors
        precursors = []
        for p in raw_precursors:
            if isinstance(p, dict):
                precursors.append({
                    "name": p.get("name", "Unknown"),
                    "bps": p.get("cpi_impact_bps", 0),
                    "pct": f"{p.get('contribution_pct', 0)}%",
                    "description": p.get("description", ""),
                })
    else:
        # Fallback to minimal defaults if no precursors generated
        precursors = [
            {"name": "Primary Cause", "bps": 0, "pct": "60%", "description": "Main triggering factor"},
            {"name": "Contributing Factor", "bps": 0, "pct": "30%", "description": "Secondary influence"},
            {"name": "Background Condition", "bps": 0, "pct": "10%", "description": "Enabling context"},
        ]
    
    # Calculate total CPI impact from effects
    total_cpi = sum(e.get("cpi_impact_bps", 0) for e in effects)
    
    # Build the network graph
    fig = go.Figure()
    
    # Node positions - horizontal layout with precursors left, event center, effects right
    # Precursors: x = 0.0, spread vertically
    # Central Event: x = 0.4
    # Intermediate effects: x = 0.6
    # Final effects: x = 0.85
    
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    hover_text = []
    
    # Add precursor nodes (left side, x=0.05)
    n_precursors = len(precursors)
    for i, p in enumerate(precursors):
        y_pos = 0.5 + (i - (n_precursors - 1) / 2) * 0.25
        node_x.append(0.05)
        node_y.append(y_pos)
        node_text.append(f"{p['name']}\n({p['pct']})")
        node_color.append("#7C3AED")  # Purple for precursors
        node_size.append(35)
        hover_text.append(f"{p['name']}: {p['pct']} contribution")
    
    # Add central event node (center, x=0.35)
    node_x.append(0.35)
    node_y.append(0.5)
    node_text.append(f"{central_event}\n+{total_cpi:.0f} bps")
    node_color.append("#ef4444")  # Red for central event
    node_size.append(55)
    hover_text.append(f"Central Event: {central_event}\nTotal CPI Impact: +{total_cpi:.0f} bps")
    central_idx = len(node_x) - 1
    
    # Group effects by their level for multi-layer cascade
    # Each level gets its own x-position for unlimited depth
    level_effects = {}
    for e in effects:
        level = e.get("level", 1)  # Default to level 1 if not specified
        if level not in level_effects:
            level_effects[level] = []
        level_effects[level].append(e)
    
    # Calculate x positions dynamically based on number of levels
    max_level = max(level_effects.keys()) if level_effects else 1
    # Start at x=0.45 (after central event at 0.35), end at x=0.95
    x_start = 0.45
    x_end = 0.95
    x_step = (x_end - x_start) / max(max_level, 1)
    
    # Store level -> indices mapping for edges
    level_indices = {}
    
    # Level colors: gradient from blue to green to orange to red as cascade deepens
    level_colors = {
        1: "#3b82f6",  # Blue - immediate
        2: "#22c55e",  # Green - secondary
        3: "#f97316",  # Orange - tertiary
        4: "#ef4444",  # Red - critical
        5: "#dc2626",  # Dark red - severe
    }
    
    # Add effect nodes grouped by level
    for level in sorted(level_effects.keys()):
        level_effects_list = level_effects[level]
        n_effects = len(level_effects_list)
        x_pos = x_start + (level - 1) * x_step
        level_indices[level] = []
        
        for i, e in enumerate(level_effects_list):
            # Spread vertically based on count
            y_spread = 0.25 if n_effects <= 3 else 0.18 if n_effects <= 5 else 0.12
            y_pos = 0.5 + (i - (n_effects - 1) / 2) * y_spread
            
            node_x.append(x_pos)
            node_y.append(y_pos)
            
            cpi = e.get("cpi_impact_bps", 0)
            node_text.append(f"{e['target']}\n+{cpi:.0f} bps")
            
            # Color based on category or level
            category = e.get("category", "").lower()
            if category == "price":
                color = "#ef4444"  # Red
            elif category == "demand" or category == "consumer":
                color = "#f97316"  # Orange
            elif category == "policy":
                color = "#a855f7"  # Purple
            else:
                color = level_colors.get(level, "#3b82f6")
            
            node_color.append(color)
            node_size.append(max(40 - level * 3, 28))  # Smaller as cascade deepens
            hover_text.append(f"Level {level}: {e['target']}\n+{cpi:.0f} bps CPI\n{e['description']}")
            level_indices[level].append(len(node_x) - 1)
    
    # Build edges
    edge_x = []
    edge_y = []
    
    # Precursors → Central Event
    for i in range(n_precursors):
        edge_x.extend([node_x[i], node_x[central_idx], None])
        edge_y.extend([node_y[i], node_y[central_idx], None])
    
    # Central Event → Level 1 Effects
    if 1 in level_indices:
        for idx in level_indices[1]:
            edge_x.extend([node_x[central_idx], node_x[idx], None])
            edge_y.extend([node_y[central_idx], node_y[idx], None])
    
    # Level N → Level N+1 (connect based on proximity)
    sorted_levels = sorted(level_indices.keys())
    for i, level in enumerate(sorted_levels[:-1]):
        next_level = sorted_levels[i + 1]
        current_indices = level_indices[level]
        next_indices = level_indices[next_level]
        
        # Connect each node in current level to closest node in next level
        for curr_idx in current_indices:
            # Find closest node in next level by y-position
            curr_y = node_y[curr_idx]
            closest_idx = min(next_indices, key=lambda idx: abs(node_y[idx] - curr_y))
            edge_x.extend([node_x[curr_idx], node_x[closest_idx], None])
            edge_y.extend([node_y[curr_idx], node_y[closest_idx], None])
    
    # Add edges trace
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(color="rgba(255, 255, 255, 0.3)", width=2),
        hoverinfo="none",
    ))
    
    # Add nodes trace
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(color="#FFFFFF", width=2),
        ),
        text=node_text,
        textposition="bottom center",
        textfont=dict(size=10, color="#FFFFFF", family="Inter"),
        hovertext=hover_text,
        hoverinfo="text",
    ))
    
    # Add stage labels dynamically
    fig.add_annotation(x=0.05, y=1.0, text="PRECURSORS", showarrow=False,
                       font=dict(size=12, color="#7C3AED", family="Inter"), xanchor="center")
    fig.add_annotation(x=0.35, y=1.0, text="CENTRAL EVENT", showarrow=False,
                       font=dict(size=12, color="#ef4444", family="Inter"), xanchor="center")
    
    # Dynamic labels for each cascade level
    level_labels = {1: "IMMEDIATE", 2: "SECONDARY", 3: "TERTIARY", 4: "QUATERNARY", 5: "CRITICAL"}
    for level in sorted(level_indices.keys()):
        x_pos = x_start + (level - 1) * x_step
        label = level_labels.get(level, f"LEVEL {level}")
        color = level_colors.get(level, "#3b82f6")
        fig.add_annotation(x=x_pos, y=1.0, text=label, showarrow=False,
                           font=dict(size=11, color=color, family="Inter"), xanchor="center")
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=60, l=20, r=20, b=80),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.05, 1.0]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.1, 1.15]),
        height=500,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary metrics
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Precursors</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #7C3AED;">{len(precursors)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Total Effects</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #3b82f6;">{len(effects)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">CPI Impact</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #ef4444;">+{total_cpi:.0f}<span style="font-size: 1rem;"> bps</span></div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        avg_cpi = total_cpi / len(effects) if effects else 0
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Cascade Depth</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #f97316;">{max_level}<span style="font-size: 1rem;"> levels</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Effect Details - grouped by level
    st.markdown("### 📋 Effect Chain Details")
    
    # Group effects by level for display
    for level in sorted(level_effects.keys()):
        level_label = level_labels.get(level, f"Level {level}")
        level_color = level_colors.get(level, "#3b82f6")
        
        st.markdown(f"""
        <div style="padding: 0.5rem 0; margin-top: 0.5rem; border-left: 3px solid {level_color}; padding-left: 0.75rem;">
            <span style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: {level_color}; text-transform: uppercase; letter-spacing: 0.05em;">{level_label} EFFECTS</span>
        </div>
        """, unsafe_allow_html=True)
        
        for effect in level_effects[level]:
            cpi = effect.get("cpi_impact_bps", 0)
            cpi_color = "#ef4444" if cpi > 10 else "#f97316" if cpi > 5 else "#22c55e"
            category = effect.get("category", "supply").upper()
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid #1A1A1A; margin-left: 0.75rem;">
                <div style="flex: 0 0 50px; text-align: center;">
                    <div style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 900; color: {level_color};">{effect['step']}</div>
                </div>
                <div style="flex: 1; padding: 0 1rem;">
                    <div style="font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 700; color: #FFFFFF;">{effect['source']} → {effect['target']}</div>
                    <div style="font-family: 'Roboto Mono', monospace; color: #808080; font-size: 0.8125rem; margin-top: 0.25rem;">{effect['description']}</div>
                    <span style="font-family: 'Roboto Mono', monospace; font-size: 0.6rem; color: #606060; text-transform: uppercase; letter-spacing: 0.05em; background: #1a1a1a; padding: 0.15rem 0.4rem; margin-top: 0.25rem; display: inline-block;">{category}</span>
                </div>
                <div style="flex: 0 0 120px; text-align: right;">
                    <div style="font-family: 'Inter', sans-serif; font-size: 1.25rem; font-weight: 900; color: {cpi_color};">+{cpi:.0f} bps</div>
                    <div style="font-family: 'Roboto Mono', monospace; color: #808080; font-size: 0.6875rem;">{effect['magnitude']:.1f} {effect['unit']}</div>
                </div>
        </div>
        """, unsafe_allow_html=True)


def display_insights():
    """Display economic insights from the orchestrator."""
    
    if not st.session_state.simulation_results:
        return
    
    insights = st.session_state.simulation_results.get("insights", [])
    
    if not insights:
        return
    
    st.markdown("### 💡 Economic Insights")
    
    severity_icons = {
        "info": "🔵",
        "warning": "🟡",
        "alert": "🟠",
        "critical": "🔴",
    }
    
    severity_colors = {
        "info": "#3b82f6",
        "warning": "#fbbf24",
        "alert": "#f97316",
        "critical": "#ef4444",
    }
    
    for insight in insights:
        icon = severity_icons.get(insight["severity"], "🔵")
        color = severity_colors.get(insight["severity"], "#3b82f6")
        
        st.markdown(f"""
        <div style="background: transparent; border-left: 3px solid {color}; padding: 0.75rem 1rem; margin-bottom: 0.75rem;">
            <div style="font-family: 'Inter', sans-serif; font-size: 0.875rem; font-weight: 900; color: #FFFFFF; margin-bottom: 0.25rem;">
                {icon} {insight['title']}
            </div>
            <div style="color: #B0B0B0; font-size: 0.8125rem; line-height: 1.5;">{insight['description']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if insight.get("cpi_impact_bps"):
            st.markdown(f"""
            <div style="margin-left: 1rem; margin-bottom: 1rem;">
                <span style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 900; color: #ef4444;">+{insight['cpi_impact_bps']:.0f}</span>
                <span style="font-size: 0.75rem; color: #808080; margin-left: 0.25rem;">basis points (CPI impact)</span>
            </div>
            """, unsafe_allow_html=True)


def create_comparison_chart():
    """Create comparison chart between simulation and reality."""
    
    if not st.session_state.simulation_results:
        return None
    
    comparison = st.session_state.simulation_results.get("comparison", {})
    
    if not comparison:
        return None
    
    zones = list(comparison.get("zones", {}).keys())
    sim_prod = [comparison["zones"][z]["simulated_production_mw"] for z in zones]
    actual_prod = [comparison["zones"][z]["actual_production_mw"] for z in zones]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Production (MW)", "Demand (MW)"),
        specs=[[{"type": "bar"}, {"type": "bar"}]],
    )
    
    # Production comparison - professional colors
    fig.add_trace(
        go.Bar(name="Simulated", x=zones, y=sim_prod, marker_color=COLORS["warning_text"]),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(name="Actual", x=zones, y=actual_prod, marker_color=COLORS["primary_400"]),
        row=1, col=1,
    )
    
    # Demand comparison
    sim_demand = [comparison["zones"][z]["simulated_demand_mw"] for z in zones]
    actual_demand = [comparison["zones"][z]["actual_demand_mw"] for z in zones]
    
    fig.add_trace(
        go.Bar(name="Simulated", x=zones, y=sim_demand, marker_color=COLORS["warning_text"], showlegend=False),
        row=1, col=2,
    )
    fig.add_trace(
        go.Bar(name="Actual", x=zones, y=actual_demand, marker_color=COLORS["primary_400"], showlegend=False),
        row=1, col=2,
    )
    
    fig.update_layout(
        title=f"Simulation vs Reality (Alignment: {comparison.get('alignment_score', 0):.0%})",
        barmode="group",
        height=350,
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF"),
    )
    
    return fig


# ============================================================================
# TIMELINE SIMULATION FUNCTIONS
# ============================================================================

def run_timeline_simulation(duration_hours: int, event_names: list[str]) -> Timeline:
    """Create and run a timeline simulation."""
    events = [get_event_template(name) for name in event_names if get_event_template(name)]
    
    simulator = TimelineSimulator()
    simulator.create_timeline(
        name="Interactive Simulation",
        duration_hours=duration_hours,
        events=events,
    )
    return simulator.run_simulation()


def get_current_checkpoint() -> SystemSnapshot | None:
    """Get the checkpoint at current hour."""
    if not st.session_state.timeline:
        return None
    timeline: Timeline = st.session_state.timeline
    return timeline.get_checkpoint(st.session_state.current_hour)


def create_timeline_prices_chart(timeline: Timeline, current_hour: int) -> go.Figure:
    """Create price evolution chart for timeline."""
    
    hours = [cp.hour for cp in timeline.checkpoints]
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Spot Prices by Zone (€/MWh)", "System Balance (MW)"),
        shared_xaxes=True,
        vertical_spacing=0.12,
        row_heights=[0.6, 0.4],
    )
    
    # Zone prices - professional zone colors
    zone_color_map = list(zip(
        [ZoneId.SE1, ZoneId.SE2, ZoneId.SE3, ZoneId.SE4],
        ZONE_COLOR_LIST
    ))
    for zone_id, color in zone_color_map:
        prices = [cp.zones[zone_id].spot_price_eur_mwh for cp in timeline.checkpoints]
        fig.add_trace(go.Scatter(
            x=hours, y=prices, name=zone_id.value, 
            line=dict(color=color, width=2),
        ), row=1, col=1)
    
    # System balance - professional colors
    balance = [cp.system_balance_mw for cp in timeline.checkpoints]
    colors = [COLORS["success_text"] if b >= 0 else COLORS["danger_text"] for b in balance]
    fig.add_trace(go.Bar(
        x=hours, y=balance, name="Balance",
        marker_color=colors, showlegend=False,
    ), row=2, col=1)
    
    # Add event shading
    for event in timeline.events:
        fig.add_vrect(
            x0=event.start_hour, x1=event.start_hour + event.duration_hours,
            fillcolor="rgba(255, 100, 100, 0.15)", layer="below", line_width=0,
            row=1, col=1,
        )
    
    # Current position line
    fig.add_vline(x=current_hour, line_dash="dash", line_color="white", line_width=2)
    
    fig.update_layout(
        height=350,
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF"),
        legend=dict(orientation="h", y=1.15),
        margin=dict(t=60, b=40),
    )
    fig.update_xaxes(title_text="Hour", row=2, col=1)
    
    return fig


def create_checkpoint_map(checkpoint: SystemSnapshot) -> go.Figure:
    """Create Sweden map from checkpoint data."""
    
    zone_data = []
    for zone_id in [ZoneId.SE1, ZoneId.SE2, ZoneId.SE3, ZoneId.SE4]:
        zone = checkpoint.zones[zone_id]
        zone_data.append({
            "zone": zone_id.value,
            "name": zone.name,
            "price": zone.spot_price_eur_mwh,
            "production": zone.production_mw,
            "consumption": zone.consumption_mw,
            "balance": zone.balance_mw,
        })
    
    coords = {"SE1": (66.5, 20.5), "SE2": (62.5, 17.5), "SE3": (59.3, 18.0), "SE4": (55.6, 13.0)}
    
    fig = go.Figure()
    
    for d in zone_data:
        lat, lon = coords[d["zone"]]
        fig.add_trace(go.Scattergeo(
            lon=[lon], lat=[lat],
            mode="markers+text",
            marker=dict(size=max(20, d["price"] * 0.4), color=ZONE_COLORS[d["zone"]], opacity=0.8),
            text=f"{d['zone']}<br>€{d['price']:.0f}",
            textposition="top center",
            name=d["zone"],
            hovertemplate=(
                f"<b>{d['zone']} - {d['name']}</b><br>"
                f"Price: €{d['price']:.1f}/MWh<br>"
                f"Prod: {d['production']:.0f} MW<br>"
                f"Cons: {d['consumption']:.0f} MW<br>"
                f"Balance: {d['balance']:+.0f} MW<extra></extra>"
            ),
        ))
    
    # Flow arrows
    for lat1, lon1, lat2, lon2 in [(66.5, 20.5, 62.5, 17.5), (62.5, 17.5, 59.3, 18.0), (59.3, 18.0, 55.6, 13.0)]:
        fig.add_trace(go.Scattergeo(
            lon=[lon1, lon2], lat=[lat1, lat2], mode="lines",
            line=dict(width=2, color=COLORS["primary_400"]), opacity=0.4, showlegend=False,
        ))
    
    fig.update_layout(
        title=f"Hour {checkpoint.hour} - {checkpoint.timestamp.strftime('%H:%M')}",
        geo=dict(scope="europe", center=dict(lat=62, lon=17), projection_scale=5,
                 showland=True, landcolor="rgb(30, 30, 30)", showocean=True, 
                 oceancolor="rgb(20, 20, 40)", showcountries=True, countrycolor="rgb(60, 60, 60)"),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF"),
        margin=dict(l=0, r=0, t=40, b=0),
        height=350,
    )
    return fig


def display_checkpoint_stats(checkpoint: SystemSnapshot):
    """Display statistics for a checkpoint."""
    
    # Alert banner
    if checkpoint.alert_level == 2:
        st.error("🚨 CRITICAL: Severe system imbalance!")
    elif checkpoint.alert_level == 1:
        st.warning("⚠️ ELEVATED: System under stress")
    
    # Active events
    if checkpoint.active_events:
        st.info(f"📢 **Active:** {', '.join(checkpoint.active_events)}")
    
    # Main metrics - horizontal row with styled units
    balance_color = "#3b82f6" if checkpoint.system_balance_mw > 0 else "#ef4444"
    balance_status = "Surplus" if checkpoint.system_balance_mw > 0 else "Deficit"
    
    st.markdown(f"""
    <div style="display: flex; gap: 3rem; margin: 1.5rem 0; flex-wrap: wrap;">
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Avg Price</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #FFFFFF; line-height: 1.2;">€{checkpoint.avg_price_eur_mwh:.1f}<span style="font-size: 1rem; font-weight: 500; color: #808080; margin-left: 0.125rem;">/MWh</span></div>
        </div>
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Production</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #3b82f6; line-height: 1.2;">{checkpoint.total_production_mw:,.0f}<span style="font-size: 1rem; font-weight: 500; color: #808080; margin-left: 0.25rem;">MW</span></div>
        </div>
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Consumption</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #ef4444; line-height: 1.2;">{checkpoint.total_consumption_mw:,.0f}<span style="font-size: 1rem; font-weight: 500; color: #808080; margin-left: 0.25rem;">MW</span></div>
        </div>
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Balance</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: {balance_color}; line-height: 1.2;">{checkpoint.system_balance_mw:+,.0f}<span style="font-size: 1rem; font-weight: 500; color: #808080; margin-left: 0.25rem;">MW</span></div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: {balance_color};">{balance_status}</div>
        </div>
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">CPI Pressure</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #ef4444; line-height: 1.2;">+{checkpoint.cpi_pressure_bps:.0f}<span style="font-size: 1rem; font-weight: 500; color: #808080; margin-left: 0.25rem;">bps</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Zone details
    st.markdown("##### Zone Details")
    zone_cols = st.columns(4)
    icons = {ZoneId.SE1: "🟢", ZoneId.SE2: "🟡", ZoneId.SE3: "🟠", ZoneId.SE4: "🔴"}
    
    for i, zone_id in enumerate(ZoneId):
        zone = checkpoint.zones[zone_id]
        with zone_cols[i]:
            status = "🔻" if zone.is_deficit else "✓"
            st.markdown(f"**{icons[zone_id]} {zone_id.value}** {status}")
            st.caption(f"€{zone.spot_price_eur_mwh:.0f} | {zone.balance_mw:+.0f}MW")


def display_simulation_summary(summary: SimulationSummary):
    """Display simulation summary with key moments."""
    
    st.markdown("""
    <div style="font-family: 'Inter', sans-serif; font-size: 1.25rem; font-weight: 900; color: #FFFFFF; margin-bottom: 1rem;">Simulation Summary</div>
    """, unsafe_allow_html=True)
    
    # Key stats - horizontal row with styled units
    peak_zone = summary.peak_price_zone.value if summary.peak_price_zone else ''
    alert_color = "#ef4444" if summary.total_alert_hours > 0 else "#808080"
    
    st.markdown(f"""
    <div style="display: flex; gap: 3rem; margin: 1rem 0; flex-wrap: wrap;">
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Duration</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #FFFFFF; line-height: 1.2;">{summary.total_hours}<span style="font-size: 1rem; font-weight: 500; color: #808080; margin-left: 0.125rem;">h</span></div>
        </div>
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Peak Price</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #FFFFFF; line-height: 1.2;">€{summary.peak_price_eur:.0f}</div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080;">H{summary.peak_price_hour} {peak_zone}</div>
        </div>
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Lowest Balance</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #ef4444; line-height: 1.2;">{summary.lowest_balance_mw:+,.0f}<span style="font-size: 1rem; font-weight: 500; color: #808080; margin-left: 0.25rem;">MW</span></div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080;">Hour {summary.lowest_balance_hour}</div>
        </div>
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Alert Hours</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: {alert_color}; line-height: 1.2;">{summary.total_alert_hours}</div>
        </div>
        <div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">Max CPI Impact</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: #ef4444; line-height: 1.2;">+{summary.max_cpi_pressure_bps:.0f}<span style="font-size: 1rem; font-weight: 500; color: #808080; margin-left: 0.25rem;">bps</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key moments
    if summary.key_moments:
        st.markdown("### 🚨 Key Moments")
        for idx, moment in enumerate(summary.key_moments[:12]):
            severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(moment.severity, "⚪")
            col1, col2 = st.columns([5, 1])
            with col1:
                value_str = f" ({moment.value:.0f} {moment.unit})" if moment.value else ""
                st.markdown(f"{severity_icon} **H{moment.hour}**: {moment.title}{value_str}")
            with col2:
                if st.button("→", key=f"jump_{idx}_{moment.hour}"):
                    st.session_state.current_hour = moment.hour
                    st.session_state.is_playing = False
                    st.rerun()


def render_timeline_tab():
    """Render the main timeline simulation interface - results only, config is in Summary tab."""
    
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.875rem; font-weight: 400; color: #B0B0B0; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;">
            Simulation
        </div>
        <h1 style="font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 900; color: #FFFFFF; margin: 0; line-height: 1;">
            Timeline Simulation
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    # No simulation yet - direct to Summary
    if not st.session_state.timeline:
        st.markdown("""
        <div style="background: transparent; border: 1px solid #1A1A1A; padding: 1.5rem; margin: 1rem 0;">
            <div style="font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 900; color: #fbbf24; margin-bottom: 0.5rem;">⚠️ No Timeline Data Available</div>
            <div style="color: #B0B0B0; font-size: 0.875rem; line-height: 1.6;">
                Please go to the <strong style="color: #FFFFFF;">📊 Executive Summary</strong> tab to configure and run a scenario.<br><br>
                The Summary tab is your central configuration hub where you can:
                <ul style="margin-top: 0.5rem; color: #808080;">
                    <li>Select scenario triggers (drought, nuclear outage, cold wave, etc.)</li>
                    <li>Set duration (hours, days, weeks, months)</li>
                    <li>Adjust magnitude and other parameters</li>
                    <li>Click <strong style="color: #FFFFFF;">"Run"</strong> to generate timeline data</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📊 Go to Summary Tab", type="primary", key="timeline_goto_summary"):
            st.info("Please click on the 'Executive Summary' tab above to configure your scenario.")
        return
    
    timeline: Timeline = st.session_state.timeline
    max_hour = timeline.total_hours
    
    # Summary panel
    if timeline.summary:
        with st.expander("📊 Summary & Key Moments", expanded=True):
            display_simulation_summary(timeline.summary)
    
    # Timeline chart
    st.plotly_chart(
        create_timeline_prices_chart(timeline, st.session_state.current_hour),
        use_container_width=True,
    )
    
    # =========================================================================
    # PLAYABLE SLIDER CONTROLS
    # =========================================================================
    st.markdown("### ▶️ Timeline Player")
    
    ctrl_cols = st.columns([1, 1, 1, 5, 1])
    
    with ctrl_cols[0]:
        if st.button("⏮️", use_container_width=True, help="Start"):
            st.session_state.current_hour = 0
            st.session_state.is_playing = False
            st.rerun()
    
    with ctrl_cols[1]:
        if st.session_state.is_playing:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.is_playing = False
                st.rerun()
        else:
            if st.button("▶️ Play", type="primary", use_container_width=True):
                st.session_state.is_playing = True
                st.rerun()
    
    with ctrl_cols[2]:
        if st.button("⏭️", use_container_width=True, help="End"):
            st.session_state.current_hour = max_hour
            st.session_state.is_playing = False
            st.rerun()
    
    with ctrl_cols[3]:
        hour = st.slider("Hour", 0, max_hour, st.session_state.current_hour, label_visibility="collapsed")
        if hour != st.session_state.current_hour:
            st.session_state.current_hour = hour
            st.session_state.is_playing = False
            st.rerun()
    
    with ctrl_cols[4]:
        speed = st.selectbox("Speed", [0.1, 0.2, 0.5, 1.0], index=2, format_func=lambda x: f"{x}s", label_visibility="collapsed")
        st.session_state.play_speed = speed
    
    # Auto-advance when playing
    if st.session_state.is_playing:
        st.markdown(f"### 🕐 Playing: Hour **{st.session_state.current_hour}** / {max_hour}")
        if st.session_state.current_hour < max_hour:
            time.sleep(st.session_state.play_speed)
            st.session_state.current_hour += 1
            st.rerun()
        else:
            st.session_state.is_playing = False
            st.success("✅ Playback complete")
    
    st.markdown("---")
    
    # Current checkpoint visualization
    checkpoint = get_current_checkpoint()
    if checkpoint:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(create_checkpoint_map(checkpoint), use_container_width=True)
        with col2:
            display_checkpoint_stats(checkpoint)


# ============================================================================
# MULTI-AGENT VISUALIZATION
# ============================================================================

def render_multi_agent_tab():
    """Render the multi-agent system visualization tab - results only, config is in Summary tab."""
    
    st.markdown("## 🤖 Multi-Agent Orchestration System")
    st.markdown("""
    *Hierarchical agent simulation with MECE domain coverage. 
    Each agent can make API calls and simulate specific scenarios.*
    """)
    
    # Display results
    if st.session_state.multi_agent_result:
        result = st.session_state.multi_agent_result
        
        # Summary metrics
        st.markdown("### 📊 Simulation Summary")
        summary = result.get("summary", {})
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Agents", summary.get("total_agents", 0))
        with col2:
            st.metric("Domain Orchestrators", summary.get("domain_orchestrators", 0))
        with col3:
            st.metric("Signals Emitted", len(result.get("signals", [])))
        with col4:
            st.metric("Predictions Made", len(result.get("predictions", [])))
        with col5:
            st.metric("API Calls", summary.get("api_calls_total", 0))
        
        st.markdown("---")
        
        # Two column layout
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # Agent hierarchy visualization
            st.markdown("### 🌳 Agent Hierarchy")
            fig_tree = create_agent_tree_visualization(result.get("agent_tree", []))
            st.plotly_chart(fig_tree, use_container_width=True)
            
            # Domino chains
            if result.get("domino_chains"):
                st.markdown("### ⛓️ Detected Domino Chains")
                for i, chain in enumerate(result["domino_chains"][:5]):
                    with st.expander(f"Chain {i+1}: {chain['source_domain']} → {chain['target_domain']}", expanded=i==0):
                        st.markdown(f"""
                        - **Source**: {chain['source_domain']}
                        - **Target**: {chain['target_domain']}
                        - **Time Lag**: {chain['time_lag_seconds']:.0f} seconds
                        - **Correlation Strength**: {chain['correlation_strength']:.2f}
                        """)
        
        with col_right:
            # Signals timeline
            st.markdown("### 📡 Signal Activity")
            signals = result.get("signals", [])
            if signals:
                signal_df = pd.DataFrame([
                    {
                        "time": s.get("timestamp", ""),
                        "type": s.get("signal_type", ""),
                        "domain": s.get("domain", ""),
                        "severity": s.get("severity", 0),
                        "metric": s.get("metric", "")
                    }
                    for s in signals[:20]
                ])
                
                if not signal_df.empty:
                    fig_signals = px.scatter(
                        signal_df,
                        x=range(len(signal_df)),
                        y="severity",
                        color="domain",
                        size="severity",
                        hover_data=["type", "metric"],
                        title="Signal Severity by Domain"
                    )
                    fig_signals.update_layout(
                        xaxis_title="Signal Sequence",
                        yaxis_title="Severity",
                        height=300,
                        paper_bgcolor="#000000",
                        plot_bgcolor="#000000",
                        font=dict(color="#FFFFFF"),
                    )
                    st.plotly_chart(fig_signals, use_container_width=True)
            
            # Top predictions
            st.markdown("### 🔮 Top Predictions")
            predictions = result.get("predictions", [])
            if predictions:
                for pred in predictions[:5]:
                    domain = pred.get("domain", "system")
                    conf = pred.get("confidence", 0)
                    value = pred.get("predicted_value", 0)
                    
                    st.markdown(f"""
                    <div style="background: #1a2332; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid {'#2d6a4f' if conf > 0.7 else '#7c5e10' if conf > 0.5 else '#7f1d1d'};">
                        <strong>{pred.get('metric', 'Unknown')}</strong><br>
                        <small>Value: {value:.1f} | Confidence: {conf:.0%}</small>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        # No results yet - direct to Summary
        st.warning("""
        ⚠️ **No Multi-Agent Results Available**
        
        Please go to the **📊 Summary** tab to configure and run a scenario.
        
        The Summary tab is your central configuration hub where you can:
        - Select scenario triggers (drought, nuclear outage, cold wave, etc.)
        - Set duration (hours, days, weeks, months)
        - Adjust magnitude and other parameters
        - Click **"Run All Systems"** to run the multi-agent analysis
        """)
        
        if st.button("📊 Go to Summary Tab", type="primary", key="multiagent_goto_summary"):
            st.info("Please click on the 'Summary' tab above to configure your scenario.")
        
        # Show preview of agent structure
        st.markdown("### 🌳 Agent Structure Preview")
        system = get_multi_agent_system()
        if not system.initialized:
            system.initialize()
        
        viz_data = system.get_visualization_data()
        if viz_data.get("nodes"):
            fig_preview = create_agent_tree_visualization([
                {
                    "id": n["id"],
                    "name": n["label"],
                    "role": n["role"],
                    "domain": n.get("domain"),
                    "level": n["level"],
                    "parent_id": None,
                    "status": "idle"
                }
                for n in viz_data["nodes"]
            ])
            st.plotly_chart(fig_preview, use_container_width=True)


def create_agent_tree_visualization(agent_tree: list) -> go.Figure:
    """Create a hierarchical tree visualization of agents."""
    
    if not agent_tree:
        return go.Figure()
    
    # Organize by level
    levels = {}
    for node in agent_tree:
        level = node.get("level", 0)
        if level not in levels:
            levels[level] = []
        levels[level].append(node)
    
    # Role colors - professional muted palette
    role_colors = {
        "master_orchestrator": "#003366",  # Riksbank Blue
        "domain_orchestrator": "#059669",  # Muted teal
        "specialist_agent": "#7c5e10",     # Muted amber
        "data_agent": "#7f1d1d"            # Muted red
    }
    
    # Status colors - professional muted palette
    status_colors = {
        "idle": "#6B7280",
        "running": "#2d6a4f",
        "completed": "#003366",
        "error": "#7f1d1d"
    }
    
    fig = go.Figure()
    
    # Calculate positions
    x_positions = {}
    y_positions = {}
    
    for level, nodes in sorted(levels.items()):
        n_nodes = len(nodes)
        for i, node in enumerate(nodes):
            # Spread horizontally
            x = (i - (n_nodes - 1) / 2) * (3 / (level + 1))
            y = -level * 1.5
            x_positions[node["id"]] = x
            y_positions[node["id"]] = y
    
    # Draw edges
    for node in agent_tree:
        parent_id = node.get("parent_id")
        if parent_id and parent_id in x_positions:
            fig.add_trace(go.Scatter(
                x=[x_positions[parent_id], x_positions[node["id"]]],
                y=[y_positions[parent_id], y_positions[node["id"]]],
                mode="lines",
                line=dict(color="#444444", width=1),
                hoverinfo="skip",
                showlegend=False
            ))
    
    # Draw nodes by role
    for role in ["master_orchestrator", "domain_orchestrator", "specialist_agent"]:
        role_nodes = [n for n in agent_tree if n.get("role") == role]
        if not role_nodes:
            continue
        
        x_vals = [x_positions[n["id"]] for n in role_nodes]
        y_vals = [y_positions[n["id"]] for n in role_nodes]
        names = [n.get("name", n["id"]) for n in role_nodes]
        statuses = [n.get("status", "idle") for n in role_nodes]
        
        # Size based on role
        sizes = {
            "master_orchestrator": 40,
            "domain_orchestrator": 25,
            "specialist_agent": 15
        }
        
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers+text",
            marker=dict(
                size=sizes.get(role, 15),
                color=role_colors.get(role, "#888888"),
                line=dict(color="white", width=2),
                opacity=0.9
            ),
            text=[n.split()[0] if len(n.split()) > 1 else n[:8] for n in names],
            textposition="bottom center",
            textfont=dict(size=8, color="white"),
            name=role.replace("_", " ").title(),
            hovertemplate="<b>%{customdata[0]}</b><br>Status: %{customdata[1]}<extra></extra>",
            customdata=list(zip(names, statuses))
        ))
    
    fig.update_layout(
        title="Agent Hierarchy",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#FFFFFF")
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-5, 5]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        ),
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF")
    )
    
    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    init_session_state()
    initialize_twin()
    
    # Modern Riksbank-inspired header
    if MODERN_STYLES_AVAILABLE:
        st.markdown(render_header(), unsafe_allow_html=True)
        
        # Key metrics bar - fetch real economic data
        twin = get_twin_engine()
        reality = twin.get_reality()
        avg_price = sum(z.spot_price_eur_mwh for z in reality.zones.values()) / 4
        
        # Get real economic indicators
        if ECONOMIC_INDICATORS_AVAILABLE:
            indicators = get_current_indicators()
            inflation_rate = indicators.cpif_rate
            policy_rate = indicators.policy_rate
        else:
            # Fallback values (current as of Dec 2025)
            inflation_rate = 2.3  # CPIF November 2025 flash estimate
            policy_rate = 1.75   # Policy rate effective Nov 12, 2025
        
        st.markdown(render_key_metrics_header(
            inflation_rate=inflation_rate,
            policy_rate=policy_rate,
            electricity_price=round(avg_price, 1),
            grid_balance="Stable" if avg_price < 100 else "Volatile"
        ), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin-bottom: 2rem;">
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.875rem; color: #B0B0B0; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Inflation → Energy</div>
            <h1 style="font-family: 'Inter', sans-serif; font-size: 5rem; font-weight: 900; color: #FFFFFF; margin: 0; letter-spacing: -0.03em; line-height: 1;">Digital Twin</h1>
        </div>
        """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎮 Control Panel")
        
        # Debug mode toggle
        st.session_state.debug_mode = st.toggle(
            "🔧 Debug Mode", 
            value=st.session_state.debug_mode, 
            help="Skip API calls, use mock data"
        )
        
        if st.session_state.debug_mode:
            st.info("🔧 Debug mode: Using simulated data")
        
        st.markdown("---")
        
        # Centralized Scenario Config Summary
        if NEW_COMPONENTS_AVAILABLE:
            st.markdown("### ⚙️ Active Scenario")
            render_config_summary()
            st.markdown("---")
        
        # Timeline status
        if st.session_state.timeline:
            st.markdown("### 📈 Simulation Status")
            timeline = st.session_state.timeline
            st.metric("Duration", f"{timeline.total_hours}h")
            st.metric("Current Hour", f"H{st.session_state.current_hour}")
            if timeline.summary:
                st.metric("Key Moments", f"{len(timeline.summary.key_moments)}")
            st.markdown("---")
        
        st.markdown("### 🎯 Quick Scenarios")
        
        model = EnergyMarketModel()
        scenarios = get_all_scenarios(model)
        
        swedish_scenarios = ["nordic_drought", "nuclear_outage", "winter_cold_wave", 
                           "baltic_cable_failure", "wind_lull"]
        global_scenarios = ["european_gas_crisis", "continental_heatwave",
                           "trade_war_rare_earths", "oil_price_shock", "carbon_price_surge"]
        
        st.markdown("#### 🇸🇪 Swedish Scenarios")
        for name in swedish_scenarios:
            if name in scenarios:
                scenario = scenarios[name]
                if st.button(f"▶️ {scenario.name}", key=f"btn_{name}", use_container_width=True):
                    run_scenario_simulation(name)
        
        st.markdown("#### 🌍 Global Shocks")
        for name in global_scenarios:
            if name in scenarios:
                scenario = scenarios[name]
                if st.button(f"▶️ {scenario.name}", key=f"btn_{name}", use_container_width=True):
                    run_scenario_simulation(name)
        
        if st.session_state.current_scenario:
            st.markdown("---")
            st.success(f"✅ {st.session_state.current_scenario}")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Executive Summary",
        "⏱️ Timeline Simulation",
        "🤖 Multi-Agent Analysis",
        "🗺️ Grid Overview", 
        "🔗 Domino Effects", 
        "📈 Deep Analysis",
        "🔮 What If"
    ])
    
    with tab1:
        # Summary tab - aggregates all subsystem outputs
        if NEW_COMPONENTS_AVAILABLE:
            render_summary_view(debug_mode=st.session_state.debug_mode)
        else:
            st.warning("Summary view component not available")
            st.info("Install dashboard components to enable this feature")
    
    with tab2:
        render_timeline_tab()
    
    with tab3:
        # Use new multi-agent view if available
        if NEW_COMPONENTS_AVAILABLE:
            render_multi_agent_view(debug_mode=st.session_state.debug_mode)
        else:
            render_multi_agent_tab()
    
    with tab4:
        # Grid Overview header - centered like other pages
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.875rem; font-weight: 400; color: #B0B0B0; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;">
                Real-Time
            </div>
            <h1 style="font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 900; color: #FFFFFF; margin: 0; line-height: 1;">
                Grid Overview
            </h1>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_map = create_sweden_map()
            st.plotly_chart(fig_map, use_container_width=True)
        
        with col2:
            twin = get_twin_engine()
            reality = twin.get_reality()
            
            st.markdown("""
            <div style="font-family: 'Inter', sans-serif; font-size: 0.875rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem;">System Status</div>
            """, unsafe_allow_html=True)
            
            # Custom styled metrics
            metrics_data = [
                ("Total Production", f"{reality.total_production_mw:,.0f}", "MW", "#3b82f6"),  # Blue for supply
                ("Total Consumption", f"{reality.total_consumption_mw:,.0f}", "MW", "#ef4444"),  # Red for demand
                ("Avg Price", f"€{reality.volume_weighted_avg_price_eur:.1f}", "/MWh", "#FFFFFF"),
                ("N-S Price Spread", f"€{reality.price_spread_se1_se4_eur:.1f}", "", "#FFFFFF"),
            ]
            
            for label, value, unit, color in metrics_data:
                st.markdown(f"""
                <div style="margin-bottom: 1rem;">
                    <div style="font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">{label}</div>
                    <div style="font-family: 'Inter', sans-serif; font-size: 2rem; font-weight: 900; color: {color};">{value}<span style="font-size: 0.875rem; color: #808080; margin-left: 0.25rem;">{unit}</span></div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        create_zone_metrics()
    
    with tab5:
        display_domino_effects()
    
    with tab6:
        # Deep Analysis header - centered like other pages
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.875rem; font-weight: 400; color: #B0B0B0; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;">
                Comparative
            </div>
            <h1 style="font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 900; color: #FFFFFF; margin: 0; line-height: 1;">
                Deep Analysis
            </h1>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_comparison = create_comparison_chart()
            if fig_comparison:
                st.plotly_chart(fig_comparison, use_container_width=True)
            else:
                st.markdown("""
                <div style="background: transparent; border: 1px solid #1A1A1A; padding: 1.5rem; margin: 1rem 0;">
                    <div style="color: #B0B0B0; font-size: 0.875rem;">Run a simulation from the Executive Summary tab to see comparison data.</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            display_insights()
        
        if st.session_state.simulation_results:
            comparison = st.session_state.simulation_results.get("comparison", {})
            if comparison:
                st.markdown("### 📝 Interpretation")
                st.markdown(f"""
                <div style="background: transparent; border-left: 3px solid #3b82f6; padding: 1rem; margin: 1rem 0;">
                    <div style="color: #B0B0B0; font-size: 0.875rem; line-height: 1.6;">{comparison.get("interpretation", "No interpretation available")}</div>
                </div>
                """, unsafe_allow_html=True)
    
    with tab7:
        # What If scenario analysis - aggregates all data and enables user prompts
        if NEW_COMPONENTS_AVAILABLE:
            render_what_if_view(debug_mode=st.session_state.debug_mode)
        else:
            st.warning("What If view component not available")
            st.info("Install dashboard components to enable this feature")


if __name__ == "__main__":
    main()
