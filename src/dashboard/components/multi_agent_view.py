"""
Swedish Energy Digital Twin - Multi-Agent View Component

Redesigned for Riksbanken economists:
- Professional, futuristic aesthetic
- Clear data visualization
- Scenario breakpoints and critical events
- Responsive design
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
import asyncio

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def inject_multi_agent_css():
    """Inject custom CSS for professional multi-agent visualization."""
    # Import modern design system CSS
    try:
        from src.dashboard.styles.modern_design import get_professional_css, COLORS
        st.markdown(get_professional_css(), unsafe_allow_html=True)
    except ImportError:
        pass  # Fall back to basic Streamlit styling
    
    # Additional multi-agent specific styles - BLACK bg, WHITE text, SHARP edges
    st.markdown("""
    <style>
    /* Professional agent card styling - BLACK theme */
    .agent-card {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 20px;
        margin: 10px 0;
        transition: all 0.2s ease;
    }
    
    .agent-card:hover {
        background: rgba(255, 255, 255, 0.02);
    }
    
    /* Domain indicators - Supply=Blue, Demand=Red */
    .domain-supply { border-left: 3px solid #3b82f6; }
    .domain-demand { border-left: 3px solid #ef4444; }
    .domain-external { border-left: 3px solid #7C3AED; }
    
    /* Status indicators */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    
    .status-active { background: #4ade80; }
    .status-processing { background: #fbbf24; }
    .status-idle { background: #808080; }
    .status-error { background: #ef4444; }
    
    /* Clean metric cards - BLACK theme */
    .metric-card {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 16px;
        text-align: center;
    }
    
    .metric-value {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 900;
        color: #FFFFFF;
    }
    
    .metric-label {
        font-size: 0.6875rem;
        color: #808080;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }
    
    /* Professional breakpoint cards - BLACK theme */
    .breakpoint-card {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 15px;
        margin: 8px 0;
    }
    
    .breakpoint-critical { border-left: 3px solid #ef4444; }
    .breakpoint-warning { border-left: 3px solid #fbbf24; }
    .breakpoint-info { border-left: 3px solid #3b82f6; }
    
    /* Executive summary - BLACK theme */
    .executive-summary {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 24px;
        margin: 16px 0;
    }
    
    .summary-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        font-weight: 900;
        color: #FFFFFF;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)


def create_scenario_metrics(result: Dict[str, Any]) -> None:
    """Display key scenario metrics in a professional grid."""
    
    summary = result.get("summary", {})
    
    st.markdown("### 📊 Scenario Metrics")
    
    cols = st.columns(6)
    
    metrics = [
        ("Agents Active", summary.get("total_agents", 13), "🤖"),
        ("API Calls", summary.get("api_calls", 0), "🌐"),
        ("Predictions", len(result.get("predictions", [])), "🔮"),
        ("Breakpoints", len(result.get("breakpoints", [])), "⚠️"),
        ("Confidence", f"{summary.get('avg_confidence', 0):.0%}", "📈"),
        ("Runtime", f"{summary.get('runtime_seconds', 0):.1f}s", "⏱️"),
    ]
    
    for col, (label, value, icon) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">{icon} {label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)


def create_agent_hierarchy_chart(agent_tree: List[Dict[str, Any]]) -> go.Figure:
    """Create an interactive sunburst/tree visualization of the agent hierarchy."""
    
    if not agent_tree:
        # Default structure for preview
        agent_tree = [
            {"id": "master", "name": "Master Orchestrator", "level": 0, "domain": "SYSTEM", "status": "idle"},
            {"id": "supply", "name": "Supply Domain", "level": 1, "domain": "SUPPLY", "status": "idle", "parent_id": "master"},
            {"id": "demand", "name": "Demand Domain", "level": 1, "domain": "DEMAND", "status": "idle", "parent_id": "master"},
            {"id": "external", "name": "External Domain", "level": 1, "domain": "EXTERNAL", "status": "idle", "parent_id": "master"},
            {"id": "hydro", "name": "Hydro Power", "level": 2, "domain": "SUPPLY", "status": "idle", "parent_id": "supply"},
            {"id": "wind", "name": "Wind Power", "level": 2, "domain": "SUPPLY", "status": "idle", "parent_id": "supply"},
            {"id": "nuclear", "name": "Nuclear Power", "level": 2, "domain": "SUPPLY", "status": "idle", "parent_id": "supply"},
            {"id": "industrial", "name": "Industrial", "level": 2, "domain": "DEMAND", "status": "idle", "parent_id": "demand"},
            {"id": "residential", "name": "Residential", "level": 2, "domain": "DEMAND", "status": "idle", "parent_id": "demand"},
            {"id": "grid", "name": "Grid Balance", "level": 2, "domain": "DEMAND", "status": "idle", "parent_id": "demand"},
            {"id": "weather", "name": "Weather", "level": 2, "domain": "EXTERNAL", "status": "idle", "parent_id": "external"},
            {"id": "commodities", "name": "Commodities", "level": 2, "domain": "EXTERNAL", "status": "idle", "parent_id": "external"},
            {"id": "policy", "name": "Policy", "level": 2, "domain": "EXTERNAL", "status": "idle", "parent_id": "external"},
        ]
    
    # Create sunburst data
    ids = []
    labels = []
    parents = []
    values = []
    colors = []
    
    # Professional domain colors - Supply=Blue, Demand=Red
    domain_colors = {
        "SYSTEM": "#003366",  # Primary blue
        "SUPPLY": "#3b82f6",  # Blue - ALWAYS for supply
        "DEMAND": "#ef4444",  # Red - ALWAYS for demand
        "EXTERNAL": "#7C3AED", # Muted purple
    }
    
    for node in agent_tree:
        ids.append(node["id"])
        labels.append(node["name"])
        parents.append(node.get("parent_id", ""))
        values.append(1)
        colors.append(domain_colors.get(node.get("domain", "SYSTEM"), "#666666"))
    
    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        branchvalues="total",
        hovertemplate="<b>%{label}</b><extra></extra>",
        textfont=dict(size=12, color="white"),
    ))
    
    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        height=400,
    )
    
    return fig


def create_agent_network_graph(agent_tree: List[Dict[str, Any]], result: Optional[Dict] = None) -> go.Figure:
    """Create a network graph showing agent relationships and data flow."""
    
    if not agent_tree:
        agent_tree = [
            {"id": "master", "name": "Master Orchestrator", "level": 0, "domain": "SYSTEM"},
            {"id": "supply", "name": "Supply Domain", "level": 1, "domain": "SUPPLY", "parent_id": "master"},
            {"id": "demand", "name": "Demand Domain", "level": 1, "domain": "DEMAND", "parent_id": "master"},
            {"id": "external", "name": "External Domain", "level": 1, "domain": "EXTERNAL", "parent_id": "master"},
            {"id": "hydro", "name": "Hydro Power", "level": 2, "domain": "SUPPLY", "parent_id": "supply"},
            {"id": "wind", "name": "Wind Power", "level": 2, "domain": "SUPPLY", "parent_id": "supply"},
            {"id": "nuclear", "name": "Nuclear Power", "level": 2, "domain": "SUPPLY", "parent_id": "supply"},
            {"id": "industrial", "name": "Industrial", "level": 2, "domain": "DEMAND", "parent_id": "demand"},
            {"id": "residential", "name": "Residential", "level": 2, "domain": "DEMAND", "parent_id": "demand"},
            {"id": "grid", "name": "Grid Balance", "level": 2, "domain": "DEMAND", "parent_id": "demand"},
            {"id": "weather", "name": "Weather", "level": 2, "domain": "EXTERNAL", "parent_id": "external"},
            {"id": "commodities", "name": "Commodities", "level": 2, "domain": "EXTERNAL", "parent_id": "external"},
            {"id": "policy", "name": "Policy", "level": 2, "domain": "EXTERNAL", "parent_id": "external"},
        ]
    
    # Infer levels if not set - based on parent relationships
    # First, find the root node (no parent)
    for node in agent_tree:
        if node.get("parent_id") is None and node.get("parent") is None:
            if "level" not in node:
                node["level"] = 0
    
    # Then assign levels based on type or parent chain
    for node in agent_tree:
        if "level" not in node:
            node_type = node.get("type", "")
            if "master" in node.get("id", "").lower() or "orchestrator" in node_type.lower():
                if node.get("parent_id") is None:
                    node["level"] = 0
                else:
                    node["level"] = 1
            elif "domain" in node_type.lower():
                node["level"] = 1
            elif "specialist" in node_type.lower():
                node["level"] = 2
            else:
                # Default based on parent
                parent_id = node.get("parent_id") or node.get("parent")
                if parent_id is None:
                    node["level"] = 0
                elif parent_id == "master":
                    node["level"] = 1
                else:
                    node["level"] = 2
    
    # Also convert "parent" to "parent_id" if needed
    for node in agent_tree:
        if "parent_id" not in node and "parent" in node:
            node["parent_id"] = node["parent"]
    
    # Position nodes by level
    level_positions = {0: (0.5, 1.0), 1: {}, 2: {}}
    
    # Level 1 positions (domain orchestrators)
    level_1_nodes = [n for n in agent_tree if n.get("level") == 1]
    if level_1_nodes:
        for i, node in enumerate(level_1_nodes):
            x = (i + 1) / (len(level_1_nodes) + 1)
            level_positions[1][node["id"]] = (x, 0.6)
    
    # Level 2 positions (specialists) - group by parent
    level_2_by_parent = {}
    for node in agent_tree:
        if node.get("level") == 2:
            parent = node.get("parent_id", "")
            if parent not in level_2_by_parent:
                level_2_by_parent[parent] = []
            level_2_by_parent[parent].append(node)
    
    # Calculate positions for level 2 nodes
    for parent_id, children in level_2_by_parent.items():
        # Get parent X position, default to even spread if parent not found
        if parent_id in level_positions[1]:
            parent_x = level_positions[1][parent_id][0]
        else:
            # Find the parent in level 1 nodes by matching domain
            parent_node = next((n for n in level_1_nodes if n["id"] == parent_id), None)
            if parent_node:
                parent_x = level_positions[1].get(parent_id, (0.5,))[0]
            else:
                # Use domain-based positioning
                domain = children[0].get("domain", "SYSTEM") if children else "SYSTEM"
                domain_x = {"SUPPLY": 0.25, "DEMAND": 0.5, "EXTERNAL": 0.75}.get(domain, 0.5)
                parent_x = domain_x
        
        # Spread children evenly under parent - wider spacing to prevent text overlap
        spread = 0.35
        num_children = len(children)
        for i, child in enumerate(children):
            if num_children == 1:
                offset = 0
            else:
                offset = (i - (num_children - 1) / 2) * (spread / max(num_children - 1, 1))
            level_positions[2][child["id"]] = (parent_x + offset, 0.1)
    
    # Build node coordinates
    node_x, node_y = [], []
    node_text, node_color, node_size = [], [], []
    
    # Professional domain colors - Supply=Blue, Demand=Red
    domain_colors = {
        "SYSTEM": "#003366",  # Primary blue
        "SUPPLY": "#3b82f6",  # Blue - ALWAYS for supply
        "DEMAND": "#ef4444",  # Red - ALWAYS for demand
        "EXTERNAL": "#7C3AED", # Muted purple
    }
    
    id_to_pos = {}
    
    for node in agent_tree:
        level = node.get("level", 0)
        nid = node["id"]
        
        if level == 0:
            pos = level_positions[0]
        elif level == 1:
            pos = level_positions[1].get(nid, (0.5, 0.6))
        else:
            # For level 2, fallback to domain-based positioning if not found
            if nid in level_positions[2]:
                pos = level_positions[2][nid]
            else:
                domain = node.get("domain", "SYSTEM")
                domain_x = {"SUPPLY": 0.25, "DEMAND": 0.5, "EXTERNAL": 0.75}.get(domain, 0.5)
                pos = (domain_x, 0.1)
        
        id_to_pos[nid] = pos
        node_x.append(pos[0])
        node_y.append(pos[1])
        node_text.append(node.get("name", nid))
        node_color.append(domain_colors.get(node.get("domain", "SYSTEM"), "#666"))
        node_size.append(30 if level == 0 else 25 if level == 1 else 20)
    
    # Build edges
    edge_x, edge_y = [], []
    for node in agent_tree:
        parent_id = node.get("parent_id")
        if parent_id and parent_id in id_to_pos:
            parent_pos = id_to_pos[parent_id]
            child_pos = id_to_pos[node["id"]]
            edge_x.extend([parent_pos[0], child_pos[0], None])
            edge_y.extend([parent_pos[1], child_pos[1], None])
    
    fig = go.Figure()
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(color="#1e3a5f", width=2),
        hoverinfo="none",
    ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(color="white", width=2),
        ),
        text=node_text,
        textposition="bottom center",
        textfont=dict(size=10, color="#FFFFFF"),
        hovertemplate="<b>%{text}</b><extra></extra>",
    ))
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=40, l=40, r=40, b=60),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.15, 1.15]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.2, 1.25]),
        height=450,
    )
    
    return fig


def display_breakpoints(breakpoints: List[Dict[str, Any]]) -> None:
    """Display critical breakpoints in a professional format."""
    
    if not breakpoints:
        st.info("No critical breakpoints detected in this scenario.")
        return
    
    st.markdown("### ⚠️ Critical Breakpoints")
    st.markdown("*Key decision points and threshold crossings identified by agents*")
    
    for bp in breakpoints:
        severity = bp.get("severity", "warning")
        severity_class = {
            "critical": "breakpoint-critical",
            "warning": "breakpoint-warning",
            "info": "breakpoint-info",
        }.get(severity, "breakpoint-info")
        
        severity_icon = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵",
        }.get(severity, "⚪")
        
        timestamp = bp.get("timestamp", "")
        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M")
        
        # Get values with safe fallbacks
        title = bp.get('title', bp.get('name', 'Breakpoint'))
        agent = bp.get('agent', 'System')
        threshold_value = bp.get('threshold_value', bp.get('current_value', 'N/A'))
        metric = bp.get('metric', 'threshold')
        description = bp.get('description', '')
        impact = bp.get('impact', 'Unknown')
        domain = bp.get('domain', 'System')
        
        severity_color = '#DC2626' if severity == 'critical' else '#D97706' if severity == 'warning' else '#003366'
        
        # Use st.container to ensure proper rendering
        with st.container():
            st.markdown(f"""
<div class="breakpoint-card {severity_class}" style="background: #000000; border: none; border-left: 3px solid {severity_color}; border-radius: 0; padding: 16px; margin: 10px 0;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <strong style="font-family: 'Inter', sans-serif; font-size: 1.25rem; font-weight: 700; color: #FFFFFF;">{severity_icon} {title}</strong>
            <div style="font-family: 'Roboto Mono', monospace; color: #808080; font-size: 0.75rem; margin-top: 5px;">{agent} | {timestamp}</div>
        </div>
        <div style="text-align: right;">
            <div style="font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 900; color: {severity_color};">{threshold_value}</div>
            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.625rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">{metric}</div>
        </div>
    </div>
    <div style="font-family: 'Roboto Mono', monospace; margin-top: 10px; color: #B0B0B0; font-size: 0.875rem;">{description}</div>
    <div style="margin-top: 10px; display: flex; gap: 10px;">
        <span style="background: transparent; border-left: 2px solid {severity_color}; padding: 4px 8px; font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #FFFFFF;">Impact: {impact}</span>
        <span style="background: transparent; border-left: 2px solid #3b82f6; padding: 4px 8px; font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #FFFFFF;">Domain: {domain}</span>
    </div>
</div>
            """, unsafe_allow_html=True)


def display_scenario_events(events: List[Dict[str, Any]]) -> None:
    """Display scenario events in a timeline format."""
    
    if not events:
        return
    
    st.markdown("### 📅 Scenario Timeline")
    
    for event in events[:10]:  # Limit to 10 events
        timestamp = event.get("timestamp", "")
        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%H:%M")
        
        domain = event.get("domain", "System")
        domain_color = {
            "SUPPLY": "#3b82f6",
            "DEMAND": "#ef4444",
            "EXTERNAL": "#7C3AED",
            "SYSTEM": "#003366",
        }.get(domain, "#003366")
        
        title = event.get('title', 'Event')
        description = event.get('description', '')
        
        with st.container():
            st.markdown(f"""
<div style="background: #000000; border: none; border-left: 3px solid {domain_color}; border-radius: 0; padding: 12px 16px; margin: 8px 0;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
            <strong style="font-family: 'Inter', sans-serif; font-size: 1.125rem; font-weight: 700; color: #FFFFFF;">{title}</strong>
            <div style="font-family: 'Roboto Mono', monospace; color: #808080; font-size: 0.75rem; margin-top: 5px;">{description}</div>
        </div>
        <div style="text-align: right; min-width: 100px;">
            <div style="font-family: 'Inter', sans-serif; color: {domain_color}; font-size: 1.5rem; font-weight: 900;">{timestamp}</div>
            <div style="font-family: 'Roboto Mono', monospace; color: #808080; font-size: 0.625rem; text-transform: uppercase; letter-spacing: 0.05em;">{domain}</div>
        </div>
    </div>
</div>
            """, unsafe_allow_html=True)


def display_predictions_grid(predictions: List[Dict[str, Any]]) -> None:
    """Display agent predictions in a professional grid layout."""
    
    if not predictions:
        st.info("No predictions generated yet.")
        return
    
    st.markdown("### Agent Predictions")
    
    # Group by domain
    by_domain = {}
    for pred in predictions:
        domain = pred.get("domain", "SYSTEM")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(pred)
    
    # Professional domain colors - Supply=Blue, Demand=Red
    domain_colors = {
        "SUPPLY": "#3b82f6",
        "DEMAND": "#ef4444",
        "EXTERNAL": "#7C3AED",
        "SYSTEM": "#003366",
    }
    
    for domain, preds in by_domain.items():
        color = domain_colors.get(domain, "#6B7280")
        st.markdown(f"""
        <div style="margin: 15px 0; padding-left: 10px; border-left: 3px solid {color};">
            <h4 style="font-family: 'Inter', sans-serif; font-weight: 900; color: #FFFFFF; margin: 0;">{domain}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(min(3, len(preds)))
        for col, pred in zip(cols, preds[:3]):
            with col:
                conf = pred.get("confidence", 0)
                value = pred.get("predicted_value", 0)
                metric = pred.get("metric", "Unknown")
                agent = pred.get("agent", "Agent")
                
                conf_color = "#059669" if conf > 0.7 else "#D97706" if conf > 0.5 else "#DC2626"
                
                st.markdown(f"""
                <div class="agent-card domain-{domain.lower()}" style="border-left: 3px solid {color};">
                    <div style="font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">{agent}</div>
                    <div style="font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 600; color: #FFFFFF; margin: 8px 0;">{metric}</div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                        <div>
                            <div style="font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 900; color: {color};">
                                {value:.1f}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-family: 'Inter', sans-serif; font-size: 2rem; font-weight: 700; color: {conf_color};">
                                {conf:.0%}
                            </div>
                            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.625rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">confidence</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


def display_executive_summary(result: Dict[str, Any]) -> None:
    """Display an executive summary for Riksbank economists."""
    
    summary = result.get("executive_summary", result.get("summary", {}))
    
    st.markdown("""
    <div class="executive-summary">
        <div class="summary-title" style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 900; color: #FFFFFF; margin-bottom: 1.5rem;">
            📋 Executive Summary
        </div>
    """, unsafe_allow_html=True)
    
    # Key findings - HIGHLIGHTED and PROMINENT
    key_findings = summary.get("key_findings", [])
    if key_findings:
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <div style="font-family: 'Inter', sans-serif; font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin-bottom: 1rem;">Key Findings</div>
        </div>
        """, unsafe_allow_html=True)
        for i, finding in enumerate(key_findings[:5]):
            st.markdown(f"""
            <div style="border-left: 3px solid #3b82f6; padding: 12px 16px; margin: 8px 0; background: transparent;">
                <span style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 900; color: #3b82f6; margin-right: 12px;">{i+1}</span>
                <span style="font-family: 'Roboto Mono', monospace; font-size: 1rem; color: #FFFFFF;">{finding}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Risk assessment - MUCH BIGGER values
    risk_level = summary.get("risk_level", "moderate")
    risk_colors = {"low": "#059669", "moderate": "#D97706", "high": "#DC2626", "critical": "#991B1B"}
    risk_color = risk_colors.get(risk_level, "#6B7280")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Overall Risk Level</div>
        <div style="font-family: 'Inter', sans-serif; font-size: 3.5rem; color: {risk_color}; font-weight: 900; text-transform: uppercase; line-height: 1;">
            {risk_level}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        impact = summary.get("price_impact_pct", 0)
        impact_color = '#DC2626' if impact > 20 else '#D97706' if impact > 10 else '#059669'
        st.markdown(f"""
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Projected Price Impact</div>
        <div style="font-family: 'Inter', sans-serif; font-size: 3.5rem; color: {impact_color}; font-weight: 900; line-height: 1;">
            {impact:+.1f}<span style="font-size: 1.5rem;">%</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        confidence = summary.get("overall_confidence", 0)
        conf_color = '#059669' if confidence > 0.7 else '#D97706' if confidence > 0.5 else '#DC2626'
        st.markdown(f"""
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Model Confidence</div>
        <div style="font-family: 'Inter', sans-serif; font-size: 3.5rem; color: {conf_color}; font-weight: 900; line-height: 1;">
            {confidence:.0%}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Recommendations - properly styled
    recommendations = summary.get("recommendations", [])
    if recommendations:
        st.markdown("""
        <div style="font-family: 'Inter', sans-serif; font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin-bottom: 1rem;">Recommendations</div>
        """, unsafe_allow_html=True)
        for rec in recommendations[:3]:
            st.markdown(f"""
            <div style="border-left: 2px solid #7C3AED; padding: 8px 16px; margin: 8px 0;">
                <span style="font-family: 'Roboto Mono', monospace; font-size: 0.9375rem; color: #B0B0B0;">{rec}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def create_confidence_gauge(value: float, title: str = "Confidence") -> go.Figure:
    """Create a gauge chart for confidence levels."""
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        domain=dict(x=[0, 1], y=[0, 1]),
        title=dict(text=title, font=dict(size=14, color="#111827")),
        number=dict(suffix="%", font=dict(color="#003366")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#6B7280"),
            bar=dict(color="#003366"),
            bgcolor="white",
            borderwidth=0,
            steps=[
                dict(range=[0, 50], color="#58151c"),  # Dark red
                dict(range=[50, 70], color="#664d03"),  # Dark amber
                dict(range=[70, 100], color="#0f5132"),  # Dark green
            ],
        )
    ))
    
    fig.update_layout(
        paper_bgcolor="#000000",
        font=dict(color="#FFFFFF"),
        height=200,
        margin=dict(t=50, b=20, l=20, r=20),
    )
    
    return fig


def create_domain_distribution_chart(predictions: List[Dict[str, Any]]) -> go.Figure:
    """Create a chart showing distribution across domains."""
    
    domain_counts = {}
    domain_confidence = {}
    
    for pred in predictions:
        domain = pred.get("domain", "SYSTEM")
        if domain not in domain_counts:
            domain_counts[domain] = 0
            domain_confidence[domain] = []
        domain_counts[domain] += 1
        domain_confidence[domain].append(pred.get("confidence", 0))
    
    domains = list(domain_counts.keys())
    counts = list(domain_counts.values())
    avg_conf = [sum(domain_confidence[d]) / len(domain_confidence[d]) if domain_confidence[d] else 0 for d in domains]
    
    # Professional domain colors - Supply=Blue, Demand=Red
    domain_colors = {
        "SUPPLY": "#3b82f6",
        "DEMAND": "#ef4444",
        "EXTERNAL": "#7C3AED",
        "SYSTEM": "#003366",
    }
    colors = [domain_colors.get(d, "#6B7280") for d in domains]
    
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "bar"}]])
    
    fig.add_trace(
        go.Pie(labels=domains, values=counts, marker=dict(colors=colors), hole=0.4),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=domains, y=avg_conf, marker=dict(color=colors)),
        row=1, col=2
    )
    
    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF"),
        height=250,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
    )
    
    return fig


def render_multi_agent_view(debug_mode: bool = False):
    """
    Main function to render the redesigned multi-agent view.
    Shows results only - configuration is centralized in Summary tab.
    
    Args:
        debug_mode: If True, uses mock data and skips API calls
    """
    # Inject CSS
    inject_multi_agent_css()
    
    # Header - matching Executive Summary design
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.875rem; font-weight: 400; color: #B0B0B0; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;">
            Multi-Agent Analysis
        </div>
        <h1 style="font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 900; color: #FFFFFF; margin: 0; line-height: 1;">
            Multi-Agent Orchestrator
        </h1>
        <p style="font-family: 'Roboto Mono', monospace; font-size: 1rem; color: #B0B0B0; margin-top: 0.5rem;">
            Hierarchical agent system for Swedish Energy Market simulation
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mode indicator
    if debug_mode:
        st.info("🔧 **Debug Mode Active** - Using simulated data")
    
    # Check if we have results - if not, direct to Summary tab
    if not st.session_state.get("multi_agent_result"):
        st.warning("""
        ⚠️ **No Analysis Data Available**
        
        Please go to the **📊 Summary** tab to configure and run a scenario analysis.
        
        The Summary tab is your central configuration hub where you can:
        - Select scenario triggers (drought, nuclear outage, cold wave, etc.)
        - Set duration (hours, days, weeks, months)
        - Adjust magnitude and other parameters
        - Run all subsystems with a single click
        """)
        
        if st.button("📊 Go to Summary Tab", type="primary"):
            st.info("Please click on the 'Summary' tab above to configure your scenario.")
        return
    
    # Display results
    result = st.session_state.multi_agent_result
    
    # Executive Summary
    display_executive_summary(result)
    
    # Metrics
    create_scenario_metrics(result)
    
    st.markdown("---")
    
    # Two-column layout for main visualizations
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.markdown("### 🌳 Agent Hierarchy")
        # Network View only
        fig_network = create_agent_network_graph(result.get("agent_tree", []), result)
        st.plotly_chart(fig_network, use_container_width=True)
        
        # Predictions grid
        display_predictions_grid(result.get("predictions", []))
    
    with col_right:
        # Breakpoints
        display_breakpoints(result.get("breakpoints", []))
        
        # Domain distribution
        st.markdown("### 📊 Domain Distribution")
        fig_dist = create_domain_distribution_chart(result.get("predictions", []))
        st.plotly_chart(fig_dist, use_container_width=True)
        
        # Scenario timeline
        display_scenario_events(result.get("events", []))
    
    # Agent Reasoning Section - Full width below the two columns
    st.markdown("---")
    
    # Check if we have LLM-powered results
    llm_result = st.session_state.get("llm_analysis_result")
    
    if llm_result and llm_result.get("master_summary"):
        # Display real LLM analysis
        st.markdown("### 🧠 LLM-Powered Agent Analysis")
        st.caption("Each agent fetched real data and used AI to generate analysis.")
        
        # Master Summary
        master = llm_result.get("master_summary", {})
        with st.expander("🎯 **Master Orchestrator Summary**", expanded=True):
            st.markdown(master.get("analysis", "No analysis available"))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Confidence", f"{master.get('confidence', 0):.0%}")
            with col2:
                st.metric("Processing Time", f"{master.get('processing_time_ms', 0)}ms")
            with col3:
                st.metric("Data Sources", len(master.get("data_sources", [])))
        
        # Domain Summaries
        st.markdown("#### 📊 Domain Analysis")
        domain_summaries = llm_result.get("domain_summaries", {})
        
        domain_tabs = st.tabs(["⚡ Supply", "🏭 Demand", "🌍 External"])
        
        for tab, (domain_key, domain_name) in zip(domain_tabs, [
            ("supply", "Supply"), ("demand", "Demand"), ("external", "External")
        ]):
            with tab:
                domain_data = domain_summaries.get(domain_key, {})
                if domain_data:
                    st.markdown(domain_data.get("analysis", "No analysis available"))
                    
                    # Show key findings
                    findings = domain_data.get("key_findings", [])
                    if findings:
                        st.markdown("**Key Findings:**")
                        for finding in findings[:5]:
                            st.markdown(f"• {finding}")
        
        # Specialist Agent Results
        st.markdown("#### 🔬 Specialist Agent Details")
        specialist_results = llm_result.get("specialist_results", [])
        
        for specialist in specialist_results:
            agent_name = specialist.get("agent_name", "Unknown")
            domain = specialist.get("domain", "SYSTEM")
            with st.expander(f"🤖 {agent_name} ({domain})"):
                st.markdown(specialist.get("analysis", "No analysis"))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Data Sources:**")
                    for source in specialist.get("data_sources", []):
                        st.markdown(f"• {source}")
                with col2:
                    st.markdown("**Metrics:**")
                    st.json(specialist.get("metrics", {}))
    else:
        # Fallback to simulated agent outputs
        try:
            from src.dashboard.components.agent_outputs import render_all_agent_outputs, inject_agent_output_css
            
            # Get config values for reasoning generation
            try:
                from src.dashboard.components.scenario_config import get_current_config
                config = get_current_config()
                trigger_for_reasoning = config.trigger
                duration_for_reasoning = config.get_duration_hours()
                magnitude_for_reasoning = config.magnitude
                custom_prompt_for_reasoning = config.custom_prompt
            except ImportError:
                trigger_for_reasoning = result.get("trigger", "nordic_drought")
                duration_for_reasoning = result.get("duration", 24)
                magnitude_for_reasoning = result.get("magnitude", 1.0)
                custom_prompt_for_reasoning = None
            
            # Render agent outputs with reasoning
            render_all_agent_outputs(
                agent_tree=result.get("agent_tree", []),
                scenario_trigger=trigger_for_reasoning,
                duration_hours=duration_for_reasoning,
                magnitude=magnitude_for_reasoning,
                custom_prompt=custom_prompt_for_reasoning,
            )
        except ImportError:
            st.info("Agent reasoning module not available")


def generate_mock_result(trigger: str, duration: int, magnitude: float, custom_prompt: str = None) -> Dict[str, Any]:
    """Generate mock result for debug mode."""
    import random
    from datetime import datetime, timedelta
    
    base_time = datetime.now()
    
    # Agent tree
    agent_tree = [
        {"id": "master", "name": "Master Orchestrator", "level": 0, "domain": "SYSTEM", "status": "completed"},
        {"id": "supply", "name": "Supply Domain", "level": 1, "domain": "SUPPLY", "status": "completed", "parent_id": "master"},
        {"id": "demand", "name": "Demand Domain", "level": 1, "domain": "DEMAND", "status": "completed", "parent_id": "master"},
        {"id": "external", "name": "External Domain", "level": 1, "domain": "EXTERNAL", "status": "completed", "parent_id": "master"},
        {"id": "hydro", "name": "Hydro Power", "level": 2, "domain": "SUPPLY", "status": "completed", "parent_id": "supply"},
        {"id": "wind", "name": "Wind Power", "level": 2, "domain": "SUPPLY", "status": "completed", "parent_id": "supply"},
        {"id": "nuclear", "name": "Nuclear Power", "level": 2, "domain": "SUPPLY", "status": "completed", "parent_id": "supply"},
        {"id": "industrial", "name": "Industrial", "level": 2, "domain": "DEMAND", "status": "completed", "parent_id": "demand"},
        {"id": "residential", "name": "Residential", "level": 2, "domain": "DEMAND", "status": "completed", "parent_id": "demand"},
        {"id": "grid", "name": "Grid Balance", "level": 2, "domain": "DEMAND", "status": "completed", "parent_id": "demand"},
        {"id": "weather", "name": "Weather", "level": 2, "domain": "EXTERNAL", "status": "completed", "parent_id": "external"},
        {"id": "commodities", "name": "Commodities", "level": 2, "domain": "EXTERNAL", "status": "completed", "parent_id": "external"},
        {"id": "policy", "name": "Policy", "level": 2, "domain": "EXTERNAL", "status": "completed", "parent_id": "external"},
    ]
    
    # Predictions
    predictions = [
        {"agent": "Hydro Power", "domain": "SUPPLY", "metric": "Reservoir Level", "predicted_value": 65.0 - magnitude * 15, "confidence": 0.85},
        {"agent": "Wind Power", "domain": "SUPPLY", "metric": "Capacity Factor", "predicted_value": 35.0 + random.uniform(-5, 5), "confidence": 0.72},
        {"agent": "Nuclear Power", "domain": "SUPPLY", "metric": "Output MW", "predicted_value": 6200 - magnitude * 500, "confidence": 0.91},
        {"agent": "Industrial", "domain": "DEMAND", "metric": "Load MW", "predicted_value": 4500 + magnitude * 200, "confidence": 0.78},
        {"agent": "Residential", "domain": "DEMAND", "metric": "Peak Demand", "predicted_value": 2800 + magnitude * 150, "confidence": 0.82},
        {"agent": "Grid Balance", "domain": "DEMAND", "metric": "Import Needed", "predicted_value": 500 + magnitude * 300, "confidence": 0.68},
        {"agent": "Weather", "domain": "EXTERNAL", "metric": "Temp Deviation", "predicted_value": -5.0 * magnitude, "confidence": 0.88},
        {"agent": "Commodities", "domain": "EXTERNAL", "metric": "Gas Price EUR/MWh", "predicted_value": 45.0 + magnitude * 12, "confidence": 0.75},
        {"agent": "Policy", "domain": "EXTERNAL", "metric": "Intervention Probability", "predicted_value": 0.3 * magnitude, "confidence": 0.55},
    ]
    
    # Breakpoints
    breakpoints = [
        {
            "title": f"Critical Threshold: {trigger.replace('_', ' ').title()}",
            "severity": "critical" if magnitude > 2 else "warning",
            "timestamp": base_time + timedelta(hours=int(duration * 0.3)),
            "agent": "Master Orchestrator",
            "metric": "System Stress Index",
            "threshold_value": f"{75 + magnitude * 10:.0f}%",
            "description": f"System stress exceeds critical threshold due to {trigger.replace('_', ' ')}",
            "impact": "High",
            "domain": "SYSTEM",
        },
        {
            "title": "Price Spike Warning",
            "severity": "warning",
            "timestamp": base_time + timedelta(hours=int(duration * 0.5)),
            "agent": "Grid Balance",
            "metric": "Spot Price",
            "threshold_value": f"€{120 + magnitude * 40:.0f}/MWh",
            "description": "Electricity prices projected to exceed normal range",
            "impact": "Moderate",
            "domain": "DEMAND",
        },
    ]
    
    if magnitude > 1.5:
        breakpoints.append({
            "title": "Supply Shortage Alert",
            "severity": "critical",
            "timestamp": base_time + timedelta(hours=int(duration * 0.7)),
            "agent": "Supply Domain",
            "metric": "Reserve Margin",
            "threshold_value": f"{8 - magnitude * 3:.1f}%",
            "description": "Reserve margin falls below safe operating threshold",
            "impact": "Critical",
            "domain": "SUPPLY",
        })
    
    # Events
    events = [
        {
            "title": f"{trigger.replace('_', ' ').title()} Initiated",
            "description": f"Scenario begins with magnitude {magnitude:.1f}x",
            "timestamp": base_time,
            "domain": "EXTERNAL",
        },
        {
            "title": "Supply Response Activated",
            "description": "Generation units responding to market signals",
            "timestamp": base_time + timedelta(hours=2),
            "domain": "SUPPLY",
        },
        {
            "title": "Demand Side Adjustment",
            "description": "Industrial load management activated",
            "timestamp": base_time + timedelta(hours=4),
            "domain": "DEMAND",
        },
        {
            "title": "Price Signal Propagation",
            "description": "Elevated prices reach all market zones",
            "timestamp": base_time + timedelta(hours=6),
            "domain": "SYSTEM",
        },
    ]
    
    # Executive summary
    risk_level = "critical" if magnitude > 2.5 else "high" if magnitude > 1.5 else "moderate" if magnitude > 0.8 else "low"
    price_impact = 15 * magnitude + random.uniform(-5, 10)
    
    executive_summary = {
        "key_findings": [
            f"Scenario '{trigger.replace('_', ' ').title()}' triggers significant market response",
            f"Supply-demand imbalance peaks at hour {int(duration * 0.6)}",
            f"Cross-border imports expected to increase by {20 * magnitude:.0f}%",
            "All electricity zones affected, SE4 experiences highest price volatility",
        ],
        "risk_level": risk_level,
        "price_impact_pct": price_impact,
        "overall_confidence": 0.78,
        "recommendations": [
            "Monitor reserve margin closely during peak stress periods",
            "Consider activating demand response programs proactively",
            "Coordinate with Nordic TSOs for potential support",
        ],
    }
    
    return {
        "agent_tree": agent_tree,
        "predictions": predictions,
        "breakpoints": breakpoints,
        "events": events,
        "executive_summary": executive_summary,
        "summary": {
            "total_agents": 13,
            "api_calls": 3 if magnitude > 1 else 2,
            "avg_confidence": 0.78,
            "runtime_seconds": 2.3,
        },
    }


# Make the view available when imported
__all__ = ["render_multi_agent_view", "inject_multi_agent_css"]
