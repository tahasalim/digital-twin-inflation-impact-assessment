"""
LLM Agent Output Component

Provides natural language reasoning for each agent with:
- Clear input/output visibility
- Hover tooltips showing full agent reasoning
- Step-by-step analysis breakdown
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class AgentReasoning:
    """Structured agent reasoning output."""
    agent_name: str
    agent_id: str
    domain: str
    
    # Input context
    input_scenario: str
    input_parameters: Dict[str, Any]
    input_data_sources: List[str]
    
    # Reasoning chain
    reasoning_steps: List[str]
    
    # Output
    output_summary: str
    output_metrics: Dict[str, Any]
    output_confidence: float
    
    # Metadata
    processing_time_ms: int
    api_calls_made: int
    timestamp: datetime
    
    def to_natural_language(self) -> str:
        """Generate natural language summary."""
        return f"""
Given scenario: {self.input_scenario}

Analysis by {self.agent_name}:
{chr(10).join(f'  • {step}' for step in self.reasoning_steps)}

Conclusion: {self.output_summary}
Confidence: {self.output_confidence:.0%}
        """.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "domain": self.domain,
            "input_scenario": self.input_scenario,
            "input_parameters": self.input_parameters,
            "input_data_sources": self.input_data_sources,
            "reasoning_steps": self.reasoning_steps,
            "output_summary": self.output_summary,
            "output_metrics": self.output_metrics,
            "output_confidence": self.output_confidence,
            "processing_time_ms": self.processing_time_ms,
            "api_calls_made": self.api_calls_made,
            "timestamp": self.timestamp.isoformat(),
        }


def inject_agent_output_css():
    """Inject CSS for agent output visualization."""
    st.markdown("""
    <style>
    /* Agent Output Cards */
    .agent-output-card {
        background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%);
        border: 1px solid rgba(0, 51, 102, 0.2);
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .agent-output-card:hover {
        border-color: rgba(0, 51, 102, 0.6);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 51, 102, 0.15);
    }
    
    .agent-output-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
    }
    
    .agent-output-card.supply::before { background: linear-gradient(180deg, #3b82f6, #2563eb); }
    .agent-output-card.demand::before { background: linear-gradient(180deg, #ef4444, #dc2626); }
    .agent-output-card.external::before { background: linear-gradient(180deg, #7c5e10, #92400e); }
    .agent-output-card.system::before { background: linear-gradient(180deg, #003366, #004080); }
    
    .agent-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    
    .agent-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #fff;
    }
    
    .agent-domain {
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 12px;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    .agent-domain.supply { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
    .agent-domain.demand { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
    .agent-domain.external { background: rgba(124, 94, 16, 0.2); color: #a16207; }
    .agent-domain.system { background: rgba(0, 51, 102, 0.2); color: #003366; }
    
    .agent-io-section {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    
    .io-label {
        font-size: 0.75rem;
        color: #888;
        text-transform: uppercase;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .io-content {
        color: #e0e0e0;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    .reasoning-chain {
        border-left: 2px solid rgba(0, 51, 102, 0.3);
        margin: 12px 0;
        padding-left: 15px;
    }
    
    .reasoning-step {
        position: relative;
        padding: 8px 0;
        color: #b0b0b0;
        font-size: 0.85rem;
    }
    
    .reasoning-step::before {
        content: '';
        position: absolute;
        left: -19px;
        top: 50%;
        transform: translateY(-50%);
        width: 8px;
        height: 8px;
        background: #003366;
        border-radius: 50%;
    }
    
    .output-summary {
        background: linear-gradient(135deg, rgba(0, 51, 102, 0.1) 0%, rgba(0, 64, 128, 0.1) 100%);
        border: 1px solid rgba(0, 51, 102, 0.3);
        border-radius: 8px;
        padding: 12px;
        margin-top: 12px;
    }
    
    .output-text {
        color: #fff;
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    .confidence-bar {
        height: 6px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
        margin-top: 10px;
        overflow: hidden;
    }
    
    .confidence-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease;
    }
    
    .confidence-high { background: linear-gradient(90deg, #2d6a4f, #22543d); }
    .confidence-medium { background: linear-gradient(90deg, #7c5e10, #92400e); }
    .confidence-low { background: linear-gradient(90deg, #7f1d1d, #991b1b); }
    
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 10px;
        margin-top: 12px;
    }
    
    .metric-item {
        background: rgba(0, 0, 0, 0.2);
        padding: 8px;
        border-radius: 6px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #003366;
    }
    
    .metric-label {
        font-size: 0.7rem;
        color: #888;
        text-transform: uppercase;
    }
    
    /* Hover tooltip */
    .agent-tooltip {
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: #1a2332;
        border: 1px solid rgba(0, 51, 102, 0.5);
        border-radius: 8px;
        padding: 15px;
        z-index: 100;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    
    .agent-output-card:hover .agent-tooltip {
        display: block;
    }
    
    /* Expand/collapse */
    .expand-btn {
        background: none;
        border: 1px solid rgba(0, 51, 102, 0.3);
        color: #003366;
        padding: 5px 12px;
        border-radius: 15px;
        cursor: pointer;
        font-size: 0.8rem;
        transition: all 0.3s ease;
    }
    
    .expand-btn:hover {
        background: rgba(0, 51, 102, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)


def generate_agent_reasoning(
    agent_name: str,
    agent_id: str,
    domain: str,
    scenario_trigger: str,
    duration_hours: int,
    magnitude: float,
    custom_prompt: Optional[str] = None,
) -> AgentReasoning:
    """
    Generate structured reasoning for an agent.
    In production, this would call the LLM. For now, generates structured mock reasoning.
    """
    import random
    
    # Domain-specific reasoning templates
    reasoning_templates = {
        "SUPPLY": {
            "Hydro Power": {
                "input_data_sources": ["SMHI Weather API", "Reservoir Level Database", "Historical Hydro Data"],
                "reasoning_steps": [
                    f"Analyzing reservoir levels across Swedish hydro facilities",
                    f"Current scenario '{scenario_trigger}' affects water availability by {magnitude * 15:.0f}%",
                    f"Cross-referencing with SMHI precipitation forecasts for next {duration_hours} hours",
                    f"Calculating capacity factor reduction based on historical drought patterns",
                    f"Estimating spillage risk and downstream flow requirements",
                ],
                "output_template": "Hydro generation capacity projected to decrease by {impact:.0f}% over {duration} period due to {scenario}. Peak reduction expected at hour {peak_hour}.",
            },
            "Wind Power": {
                "input_data_sources": ["SMHI Wind Forecast", "Wind Farm SCADA", "Nordic Wind Atlas"],
                "reasoning_steps": [
                    f"Fetching wind speed forecasts from SMHI API",
                    f"Analyzing wind patterns across SE1-SE4 zones",
                    f"Scenario impact on atmospheric conditions assessed",
                    f"Calculating expected capacity factors per wind farm cluster",
                    f"Accounting for seasonal and diurnal variations",
                ],
                "output_template": "Wind generation expected to {direction} by {impact:.0f}% with high variability. Northern zones (SE1-SE2) showing {north_trend}, southern zones (SE3-SE4) showing {south_trend}.",
            },
            "Nuclear Power": {
                "input_data_sources": ["Forsmark Status API", "Ringhals Status API", "Oskarshamn Status API", "Nuclear Fuel Inventory"],
                "reasoning_steps": [
                    f"Checking operational status of all Swedish nuclear reactors",
                    f"Evaluating scenario '{scenario_trigger}' impact on nuclear operations",
                    f"Analyzing cooling water availability and temperature constraints",
                    f"Assessing maintenance schedules and unplanned outage risks",
                    f"Calculating total baseload capacity availability",
                ],
                "output_template": "Nuclear baseload capacity at {capacity:.0f}% of nominal. {reactor_status}. Magnitude {magnitude:.1f}x scenario suggests {risk_level} risk of additional outages.",
            },
        },
        "DEMAND": {
            "Industrial": {
                "input_data_sources": ["Industrial Load Registry", "SCB Economic Data", "Energy Intensive Industries Report"],
                "reasoning_steps": [
                    f"Analyzing industrial consumption patterns across sectors",
                    f"Scenario '{scenario_trigger}' impact on manufacturing operations",
                    f"Evaluating price elasticity of major industrial consumers",
                    f"Checking demand response program participation rates",
                    f"Forecasting industrial load flexibility potential",
                ],
                "output_template": "Industrial demand projected at {demand:.0f} MW, {change:+.0f}% from baseline. Primary sectors affected: {sectors}. Demand response potential: {dr_potential:.0f} MW.",
            },
            "Residential": {
                "input_data_sources": ["Temperature Forecast", "Heating Degree Days", "Population Density Data"],
                "reasoning_steps": [
                    f"Calculating heating/cooling demand based on weather forecast",
                    f"Applying magnitude {magnitude:.1f}x to temperature deviation scenarios",
                    f"Analyzing regional population and housing stock differences",
                    f"Accounting for time-of-use patterns and peak hours",
                    f"Estimating price sensitivity for residential consumers",
                ],
                "output_template": "Residential peak demand forecast: {peak_demand:.0f} MW at hour {peak_hour}. Temperature impact: {temp_impact:+.1f}°C deviation drives {heat_demand} additional heating load.",
            },
            "Grid Balance": {
                "input_data_sources": ["Nord Pool Spot Prices", "TSO Balancing Data", "Cross-border Flow Data"],
                "reasoning_steps": [
                    f"Calculating supply-demand balance across all zones",
                    f"Analyzing interconnector capacity and utilization",
                    f"Evaluating imbalance costs and regulation needs",
                    f"Forecasting spot price trajectory based on fundamentals",
                    f"Assessing cross-border import/export requirements",
                ],
                "output_template": "Grid balance: {balance:+.0f} MW ({balance_status}). Import requirement: {import_need:.0f} MW. Spot price forecast: €{price:.0f}/MWh.",
            },
        },
        "EXTERNAL": {
            "Weather": {
                "input_data_sources": ["SMHI Open Data API", "ECMWF Forecasts", "Historical Climate Data"],
                "reasoning_steps": [
                    f"Fetching latest SMHI weather forecasts for all Swedish regions",
                    f"Analyzing temperature, precipitation, and wind patterns",
                    f"Scenario '{scenario_trigger}' weather implications assessed",
                    f"Correlating weather with historical energy consumption data",
                    f"Generating probabilistic weather scenarios for {duration_hours} hours",
                ],
                "output_template": "Weather forecast: {temp_summary}. Precipitation: {precip_summary}. Wind conditions: {wind_summary}. Confidence: {confidence:.0%}.",
            },
            "Commodities": {
                "input_data_sources": ["TTF Gas Prices", "EU ETS Carbon Prices", "Coal Import Data"],
                "reasoning_steps": [
                    f"Analyzing current commodity price levels and trends",
                    f"Evaluating scenario '{scenario_trigger}' impact on fuel costs",
                    f"Calculating marginal generation costs for thermal units",
                    f"Assessing carbon price trajectory and policy impacts",
                    f"Forecasting commodity price scenarios for simulation period",
                ],
                "output_template": "Commodity outlook: Gas at €{gas_price:.0f}/MWh ({gas_trend}), Carbon at €{carbon_price:.0f}/tCO2 ({carbon_trend}). Marginal cost impact: {cost_impact:+.0f}%.",
            },
            "Policy": {
                "input_data_sources": ["Energy Policy Database", "EU Regulatory Updates", "Svenska kraftnät Announcements"],
                "reasoning_steps": [
                    f"Scanning for relevant policy and regulatory developments",
                    f"Analyzing potential government intervention triggers",
                    f"Evaluating EU energy security measures applicability",
                    f"Assessing probability of emergency market interventions",
                    f"Modeling policy impact on market prices and operations",
                ],
                "output_template": "Policy analysis: {intervention_prob:.0%} probability of government intervention. Key triggers: {triggers}. Regulatory risk level: {risk_level}.",
            },
        },
    }
    
    # Get template for this agent
    domain_templates = reasoning_templates.get(domain, {})
    agent_template = domain_templates.get(agent_name, {
        "input_data_sources": ["General API", "Internal Database"],
        "reasoning_steps": [
            f"Initializing analysis for {agent_name}",
            f"Processing scenario '{scenario_trigger}' with magnitude {magnitude:.1f}x",
            f"Analyzing {duration_hours} hour forecast window",
            f"Computing metrics and generating predictions",
            f"Validating results against historical patterns",
        ],
        "output_template": f"Analysis complete for {agent_name}. Scenario impact assessed with {{confidence:.0%}} confidence.",
    })
    
    # Generate dynamic values
    impact = magnitude * random.uniform(10, 25)
    confidence = random.uniform(0.65, 0.92)
    
    # Format output
    output_summary = agent_template["output_template"].format(
        impact=impact,
        duration=f"{duration_hours} hours",
        scenario=scenario_trigger.replace("_", " "),
        peak_hour=random.randint(1, min(24, duration_hours)),
        direction="increase" if random.random() > 0.5 else "decrease",
        north_trend="stable production" if random.random() > 0.5 else "reduced output",
        south_trend="elevated output" if random.random() > 0.5 else "variable output",
        capacity=100 - (magnitude * random.uniform(5, 15)),
        reactor_status="All reactors operational" if magnitude < 2 else "1 reactor in reduced output mode",
        magnitude=magnitude,
        risk_level="elevated" if magnitude > 1.5 else "moderate" if magnitude > 1 else "low",
        demand=random.uniform(4000, 6000),
        change=magnitude * random.uniform(-10, 20),
        sectors="Steel, Paper & Pulp, Chemical",
        dr_potential=random.uniform(200, 500),
        peak_demand=random.uniform(2500, 3500),
        temp_impact=magnitude * random.uniform(-3, 3),
        heat_demand=f"{random.uniform(100, 300):.0f} MW",
        balance=random.uniform(-500, 500),
        balance_status="surplus" if random.random() > 0.5 else "deficit",
        import_need=magnitude * random.uniform(200, 600),
        price=random.uniform(50, 150) + (magnitude * 20),
        temp_summary=f"{random.uniform(-5, 15):.1f}°C average",
        precip_summary="moderate rainfall expected" if random.random() > 0.5 else "dry conditions",
        wind_summary=f"{random.uniform(3, 12):.1f} m/s average",
        confidence=confidence,
        gas_price=random.uniform(30, 60) + (magnitude * 10),
        gas_trend="rising" if random.random() > 0.5 else "stable",
        carbon_price=random.uniform(60, 100),
        carbon_trend="stable" if random.random() > 0.5 else "rising",
        cost_impact=magnitude * random.uniform(5, 15),
        intervention_prob=min(0.9, magnitude * random.uniform(0.1, 0.3)),
        triggers="price spikes, supply shortage" if magnitude > 1.5 else "market volatility",
    )
    
    # Generate metrics
    output_metrics = {
        "impact_pct": impact,
        "confidence": confidence,
        "data_points": random.randint(100, 1000),
        "forecast_hours": duration_hours,
    }
    
    # Build input scenario description
    input_scenario = f"{scenario_trigger.replace('_', ' ').title()}"
    if custom_prompt:
        input_scenario += f" - {custom_prompt[:100]}..."
    
    return AgentReasoning(
        agent_name=agent_name,
        agent_id=agent_id,
        domain=domain,
        input_scenario=input_scenario,
        input_parameters={
            "trigger": scenario_trigger,
            "duration_hours": duration_hours,
            "magnitude": magnitude,
            "custom_prompt": custom_prompt,
        },
        input_data_sources=agent_template["input_data_sources"],
        reasoning_steps=agent_template["reasoning_steps"],
        output_summary=output_summary,
        output_metrics=output_metrics,
        output_confidence=confidence,
        processing_time_ms=random.randint(150, 800),
        api_calls_made=len(agent_template["input_data_sources"]),
        timestamp=datetime.now(),
    )


def render_agent_output_card(reasoning: AgentReasoning, expanded: bool = False):
    """Render a single agent output card using Streamlit native components."""
    domain_lower = reasoning.domain.lower()
    
    # Confidence level and color - professional muted palette
    if reasoning.output_confidence > 0.8:
        conf_color = "#2d6a4f"
        conf_label = "HIGH"
    elif reasoning.output_confidence > 0.6:
        conf_color = "#7c5e10"
        conf_label = "MEDIUM"
    else:
        conf_color = "#7f1d1d"
        conf_label = "LOW"
    
    # Domain colors - professional muted palette
    domain_colors = {
        "supply": "#3b82f6",
        "demand": "#ef4444",
        "external": "#7c5e10",
        "system": "#003366",
    }
    domain_color = domain_colors.get(domain_lower, "#003366")
    
    # Use Streamlit expander as the card container
    with st.expander(f"🤖 {reasoning.agent_name} — {reasoning.domain}", expanded=expanded):
        # Input section
        st.markdown(f"**📥 Input:** {reasoning.input_scenario}")
        
        # Output section
        st.markdown(f"**📤 Output:** {reasoning.output_summary}")
        
        # Confidence bar using columns
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(reasoning.output_confidence, text=f"Confidence: {reasoning.output_confidence:.0%}")
        with col2:
            st.caption(f"{reasoning.processing_time_ms}ms | {reasoning.api_calls_made} API calls")
        
        # Reasoning chain in a nested expander
        with st.expander("🔍 View Reasoning Details"):
            st.markdown("**📊 Data Sources:**")
            for source in reasoning.input_data_sources:
                st.markdown(f"• {source}")
            
            st.markdown("---")
            st.markdown("**🧠 Reasoning Chain:**")
            for i, step in enumerate(reasoning.reasoning_steps, 1):
                st.markdown(f"{i}. {step}")
            
            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**📥 Input Parameters:**")
                st.json(reasoning.input_parameters)
            with col_b:
                st.markdown("**📈 Output Metrics:**")
                st.json(reasoning.output_metrics)


def render_all_agent_outputs(
    agent_tree: List[Dict[str, Any]],
    scenario_trigger: str,
    duration_hours: int,
    magnitude: float,
    custom_prompt: Optional[str] = None,
) -> List[AgentReasoning]:
    """
    Render all agent outputs with their reasoning.
    
    Returns list of AgentReasoning objects for further processing.
    """
    inject_agent_output_css()
    
    st.markdown("### 🧠 Agent Analysis & Reasoning")
    st.caption("Each agent provides natural language analysis. Click to expand for full reasoning chain and data sources.")
    
    all_reasoning = []
    
    # Group agents by domain
    domains = {}
    for agent in agent_tree:
        domain = agent.get("domain", "SYSTEM")
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(agent)
    
    # Domain order
    domain_order = ["SYSTEM", "SUPPLY", "DEMAND", "EXTERNAL"]
    domain_icons = {
        "SYSTEM": "🎛️",
        "SUPPLY": "⚡",
        "DEMAND": "🏭",
        "EXTERNAL": "🌍",
    }
    
    for domain in domain_order:
        if domain not in domains:
            continue
        
        st.markdown(f"#### {domain_icons.get(domain, '📦')} {domain} Domain")
        
        for agent in domains[domain]:
            # Only generate reasoning for leaf agents (level 2)
            if agent.get("level", 0) >= 1:
                reasoning = generate_agent_reasoning(
                    agent_name=agent.get("name", "Unknown"),
                    agent_id=agent.get("id", "unknown"),
                    domain=domain,
                    scenario_trigger=scenario_trigger,
                    duration_hours=duration_hours,
                    magnitude=magnitude,
                    custom_prompt=custom_prompt,
                )
                all_reasoning.append(reasoning)
                render_agent_output_card(reasoning)
    
    return all_reasoning


def render_agent_summary_tooltip(reasoning: AgentReasoning) -> str:
    """Generate tooltip HTML for agent summary."""
    return f"""
    <div class="tooltip-content">
        <strong>{reasoning.agent_name}</strong><br>
        <em>Input:</em> {reasoning.input_scenario}<br>
        <em>Output:</em> {reasoning.output_summary}<br>
        <em>Confidence:</em> {reasoning.output_confidence:.0%}
    </div>
    """


# Export
__all__ = [
    "AgentReasoning",
    "generate_agent_reasoning",
    "render_agent_output_card",
    "render_all_agent_outputs",
    "inject_agent_output_css",
]
