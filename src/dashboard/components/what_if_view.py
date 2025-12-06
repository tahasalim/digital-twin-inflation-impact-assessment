"""
Swedish Energy Digital Twin - What If Scenario Analysis

Interactive "What If" scenario exploration:
- Aggregates ALL available simulation data
- Lets users prompt hypothetical scenarios
- Runs LLM analysis with fresh external data
- Displays detailed findings with metric changes
- Supports infinite scenario iteration
"""

import streamlit as st
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import traceback

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def inject_what_if_css():
    """Inject custom CSS for the What If view - BLACK theme, SHARP edges."""
    st.markdown("""
    <style>
    .what-if-container {
        background: transparent;
        border: 1px solid #1A1A1A;
        border-radius: 0;
        padding: 24px;
        margin: 16px 0;
    }
    
    .scenario-prompt-box {
        background: #0A0A0A;
        border: 1px solid #1A1A1A;
        border-radius: 0;
        padding: 20px;
        margin: 16px 0;
    }
    
    .result-card {
        background: transparent;
        border: 1px solid #1A1A1A;
        border-radius: 0;
        padding: 20px;
        margin: 12px 0;
    }
    
    .metric-change {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 0;
        font-size: 14px;
        font-weight: 900;
    }
    
    .metric-increase {
        background: transparent;
        color: #ef4444;
        border: 1px solid #ef4444;
    }
    
    .metric-decrease {
        background: transparent;
        color: #4ade80;
        border: 1px solid #4ade80;
    }
    
    .metric-neutral {
        background: transparent;
        color: #808080;
        border: 1px solid #808080;
    }
    
    .insight-box {
        background: transparent;
        border-left: 3px solid #3b82f6;
        padding: 16px;
        margin: 12px 0;
        border-radius: 0;
    }
    
    .trend-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 0;
        font-size: 11px;
        font-weight: 900;
        text-transform: uppercase;
    }
    
    .history-item {
        background: transparent;
        border: 1px solid #1A1A1A;
        border-radius: 0;
        padding: 12px 16px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .history-item:hover {
        background: #0A0A0A;
        border-color: #3A3A3A;
    }
    </style>
    """, unsafe_allow_html=True)


def aggregate_all_results() -> Dict[str, Any]:
    """
    Aggregate ALL available results from all tabs into one comprehensive JSON.
    """
    aggregated = {
        "timestamp": datetime.now().isoformat(),
        "data_sources": [],
        "scenario_config": {},
        "timeline_simulation": {},
        "multi_agent_analysis": {},
        "historical_events": [],
        "external_data": {},
        "grid_state": {},
        "domino_effects": {},
    }
    
    # 1. Get scenario configuration
    try:
        from src.dashboard.components.scenario_config import get_current_config
        config = get_current_config()
        aggregated["scenario_config"] = {
            "trigger": config.trigger,
            "duration_hours": config.get_duration_hours(),
            "magnitude": config.magnitude,
            "supply_adjustment": config.supply_adjustment,
            "demand_adjustment": config.demand_adjustment,
            "custom_prompt": config.custom_prompt,
        }
        aggregated["data_sources"].append("scenario_config")
    except Exception as e:
        aggregated["scenario_config"] = {"error": str(e)}
    
    # 2. Get timeline simulation results
    if st.session_state.get("timeline"):
        try:
            timeline = st.session_state.timeline
            checkpoints = []
            if hasattr(timeline, 'checkpoints'):
                for cp in timeline.checkpoints[:20]:  # Limit for size
                    checkpoints.append({
                        "hour": cp.hour,
                        "timestamp": cp.timestamp.isoformat() if hasattr(cp, 'timestamp') else None,
                        "total_production_mw": getattr(cp, 'total_production_mw', None),
                        "total_consumption_mw": getattr(cp, 'total_consumption_mw', None),
                        "avg_price_eur": getattr(cp, 'avg_price_eur', None),
                    })
            
            aggregated["timeline_simulation"] = {
                "name": getattr(timeline, 'name', 'Unknown'),
                "duration_hours": getattr(timeline, 'duration_hours', 0),
                "checkpoint_count": len(timeline.checkpoints) if hasattr(timeline, 'checkpoints') else 0,
                "checkpoints_sample": checkpoints,
                "summary": timeline.summary.to_dict() if hasattr(timeline, 'summary') and timeline.summary else None,
            }
            aggregated["data_sources"].append("timeline_simulation")
        except Exception as e:
            aggregated["timeline_simulation"] = {"error": str(e)}
    
    # 3. Get multi-agent analysis results (LLM)
    if st.session_state.get("llm_analysis_result"):
        try:
            llm_result = st.session_state.llm_analysis_result
            aggregated["multi_agent_analysis"] = {
                "master_summary": llm_result.get("master_summary", {}),
                "domain_summaries": llm_result.get("domain_summaries", {}),
                "specialist_count": len(llm_result.get("specialist_results", [])),
                "specialist_results": [
                    {
                        "agent_name": s.get("agent_name"),
                        "domain": s.get("domain"),
                        "analysis": s.get("analysis", "")[:500],  # Truncate for size
                        "confidence": s.get("confidence"),
                        "data_sources": s.get("data_sources", []),
                    }
                    for s in llm_result.get("specialist_results", [])
                ],
                "total_processing_time_ms": llm_result.get("total_processing_time_ms"),
                "agent_count": llm_result.get("agent_count"),
            }
            aggregated["data_sources"].append("llm_multi_agent")
        except Exception as e:
            aggregated["multi_agent_analysis"] = {"error": str(e)}
    
    # 4. Get transformed multi-agent result (for UI)
    if st.session_state.get("multi_agent_result"):
        try:
            result = st.session_state.multi_agent_result
            aggregated["multi_agent_analysis"]["executive_summary"] = result.get("executive_summary", {})
            aggregated["multi_agent_analysis"]["predictions"] = result.get("predictions", [])[:10]
            aggregated["multi_agent_analysis"]["breakpoints"] = result.get("breakpoints", [])
            aggregated["multi_agent_analysis"]["events"] = result.get("events", [])
        except Exception:
            pass
    
    # 5. Get historical events
    if st.session_state.get("historical_events"):
        aggregated["historical_events"] = st.session_state.historical_events
        aggregated["data_sources"].append("historical_events")
    
    # 6. Get fetched external data (Google Trends, News, etc.)
    if st.session_state.get("fetched_data"):
        try:
            fetched = st.session_state.fetched_data
            aggregated["external_data"] = {
                "trends": fetched.get("trends", {}),
                "news": fetched.get("news", [])[:5],  # Limit
                "real_prices": fetched.get("real_prices") is not None,
            }
            aggregated["data_sources"].append("external_apis")
        except Exception as e:
            aggregated["external_data"] = {"error": str(e)}
    
    # 7. Get current grid state from Digital Twin
    try:
        from src.twin.engine import get_twin_engine
        twin = get_twin_engine()
        reality = twin.get_reality()
        
        aggregated["grid_state"] = {
            "total_production_mw": reality.total_production_mw,
            "total_consumption_mw": reality.total_consumption_mw,
            "volume_weighted_avg_price_eur": reality.volume_weighted_avg_price_eur,
            "price_spread_se1_se4_eur": reality.price_spread_se1_se4_eur,
            "zones": {
                zone_id: {
                    "price_eur": zone.spot_price_eur,
                    "production_mw": zone.production_mw,
                    "consumption_mw": zone.consumption_mw,
                }
                for zone_id, zone in reality.zones.items()
            } if hasattr(reality, 'zones') else {},
        }
        aggregated["data_sources"].append("digital_twin")
    except Exception as e:
        aggregated["grid_state"] = {"error": str(e)}
    
    # 8. Get simulation results
    if st.session_state.get("simulation_results"):
        try:
            sim_results = st.session_state.simulation_results
            aggregated["domino_effects"] = {
                "insights": sim_results.get("insights", []),
                "comparison": sim_results.get("comparison", {}),
            }
            aggregated["data_sources"].append("simulation_results")
        except Exception:
            pass
    
    return aggregated


async def fetch_fresh_external_data(scenario_prompt: str) -> Dict[str, Any]:
    """
    Fetch fresh external data based on the what-if scenario.
    """
    fresh_data = {
        "google_trends": {},
        "news": [],
        "timestamp": datetime.now().isoformat(),
    }
    
    try:
        from src.api.providers import GoogleTrendsProvider, NewsAPIProvider
        
        # Extract keywords from the prompt
        keywords = extract_keywords_from_prompt(scenario_prompt)
        
        # Fetch Google Trends
        trends_provider = GoogleTrendsProvider()
        trends_data, trends_real = await trends_provider.get_data(
            keywords=keywords[:3],  # Limit to 3 keywords
            geo="SE"
        )
        fresh_data["google_trends"] = {
            "data": trends_data,
            "is_real": trends_real,
            "keywords": keywords[:3],
        }
        
        # Fetch news
        news_provider = NewsAPIProvider()
        news_query = " OR ".join(keywords[:2])
        news_data, news_real = await news_provider.get_data(
            query=news_query,
            page_size=5
        )
        fresh_data["news"] = news_data if isinstance(news_data, list) else []
        fresh_data["news_is_real"] = news_real
        
    except ImportError:
        fresh_data["error"] = "External data providers not available"
    except Exception as e:
        fresh_data["error"] = str(e)
    
    return fresh_data


def extract_keywords_from_prompt(prompt: str) -> List[str]:
    """Extract relevant keywords from user prompt for API searches."""
    # Energy-related keywords to look for
    energy_keywords = [
        "electricity", "power", "energy", "price", "grid",
        "nuclear", "hydro", "wind", "solar", "gas",
        "drought", "cold", "winter", "heat", "storm",
        "outage", "failure", "crisis", "shortage", "surplus",
        "import", "export", "interconnector", "cable",
        "sweden", "nordic", "europe",
    ]
    
    prompt_lower = prompt.lower()
    found = []
    
    # Find energy keywords in prompt
    for kw in energy_keywords:
        if kw in prompt_lower:
            found.append(f"sweden {kw}")
    
    # Add generic Swedish energy keywords if none found
    if not found:
        found = ["sweden electricity", "swedish energy market"]
    
    return found[:5]


async def run_what_if_analysis(
    aggregated_data: Dict[str, Any],
    what_if_prompt: str,
    fresh_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run LLM analysis for the what-if scenario.
    Uses the master orchestrator pattern with all aggregated data.
    """
    import streamlit as st
    from src.agents.llm_agents import get_llm_client
    
    st.write("🔧 Loading LLM client...")
    
    # Build comprehensive context for the LLM
    context_parts = []
    
    # Add scenario context
    if aggregated_data.get("scenario_config"):
        config = aggregated_data["scenario_config"]
        context_parts.append(f"""
CURRENT SCENARIO:
- Trigger: {config.get('trigger', 'Unknown')}
- Duration: {config.get('duration_hours', 24)} hours
- Magnitude: {config.get('magnitude', 1.0):.0%}
""")
    
    # Add grid state
    if aggregated_data.get("grid_state") and not aggregated_data["grid_state"].get("error"):
        grid = aggregated_data["grid_state"]
        context_parts.append(f"""
CURRENT GRID STATE:
- Total Production: {grid.get('total_production_mw', 0):,.0f} MW
- Total Consumption: {grid.get('total_consumption_mw', 0):,.0f} MW
- Avg Price: {grid.get('volume_weighted_avg_price_eur', 0):.1f} EUR/MWh
- N-S Price Spread: {grid.get('price_spread_se1_se4_eur', 0):.1f} EUR
""")
    
    # Add multi-agent summary
    if aggregated_data.get("multi_agent_analysis"):
        ma = aggregated_data["multi_agent_analysis"]
        master = ma.get("master_summary", {})
        if master.get("analysis"):
            context_parts.append(f"""
MULTI-AGENT ANALYSIS SUMMARY:
{master.get('analysis', '')[:2000]}
""")
    
    # Add historical context
    if aggregated_data.get("historical_events"):
        events = aggregated_data["historical_events"][:3]
        if events:
            events_text = "\n".join([
                f"- {e.get('name', 'Event')}: Severity {e.get('severity', 0):.0%}"
                for e in events
            ])
            context_parts.append(f"""
HISTORICAL PRECEDENTS:
{events_text}
""")
    
    # Add fresh external data
    if fresh_data.get("google_trends"):
        trends = fresh_data["google_trends"]
        context_parts.append(f"""
FRESH GOOGLE TRENDS DATA:
Keywords: {', '.join(trends.get('keywords', []))}
Data available: {'Real API data' if trends.get('is_real') else 'Simulated'}
""")
    
    if fresh_data.get("news"):
        news_items = fresh_data["news"][:3]
        if news_items:
            news_text = "\n".join([
                f"- {n.get('title', 'News item')[:100]}"
                for n in news_items if isinstance(n, dict)
            ])
            context_parts.append(f"""
CURRENT NEWS:
{news_text}
""")
    
    full_context = "\n".join(context_parts)
    
    # Create the what-if prompt for the LLM
    system_prompt = """You are the What-If Scenario Analyst for the Swedish Energy Digital Twin.

Your role is to analyze hypothetical scenarios and their potential impacts on the Swedish energy market.

Given the current state of the system and the user's what-if scenario, provide:

1. **Scenario Impact Assessment** (2-3 sentences on the overall impact)

2. **Key Metric Changes** (provide specific numerical estimates):
   - Price Impact: +/- X% (explain reasoning)
   - Supply Impact: +/- X MW (explain which sources affected)
   - Demand Impact: +/- X MW (explain which sectors affected)
   - Grid Stability: rating from 1-10
   - Inflation Impact: +/- X basis points on CPIF

3. **Timeline of Effects**:
   - Immediate (0-6 hours): What happens first
   - Short-term (6-24 hours): Secondary effects
   - Medium-term (24-72 hours): Market adjustments

4. **Risk Assessment**:
   - Primary risks
   - Mitigation options
   - Confidence level in predictions

5. **Recommendations** for Riksbanken:
   - Policy considerations
   - Monitoring priorities
   - Contingency preparations

Be specific with numbers and percentages. Reference the actual data provided when making estimates.
Format your response with clear headers and bullet points."""

    user_prompt = f"""CURRENT SYSTEM STATE:
{full_context}

USER'S WHAT-IF SCENARIO:
"{what_if_prompt}"

Analyze this hypothetical scenario and provide a comprehensive impact assessment.
Be specific about metric changes and reference the current state data in your analysis."""

    # Run the LLM analysis
    try:
        st.write("🧠 Initializing What-If Analyst...")
        
        start_time = datetime.now()
        
        # Get the LLM client
        st.write("🔌 Connecting to LLM service...")
        client = get_llm_client()
        
        st.write(f"📡 Sending analysis request to {client.provider.value}...")
        
        # Call the LLM using generate method
        response = await client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )
        
        analysis_text = response.content
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        st.write(f"✅ Analysis complete in {processing_time/1000:.1f}s ({response.tokens_used} tokens)")
        
        # Parse the response to extract structured data
        result = {
            "analysis": analysis_text,
            "processing_time_ms": processing_time,
            "timestamp": datetime.now().isoformat(),
            "what_if_prompt": what_if_prompt,
            "metrics_extracted": extract_metrics_from_analysis(analysis_text),
            "fresh_data_used": fresh_data,
            "data_sources_count": len(aggregated_data.get("data_sources", [])),
            "llm_provider": response.provider.value,
            "model": response.model,
            "tokens_used": response.tokens_used,
            "latency_ms": response.latency_ms,
        }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat(),
        }


def extract_metrics_from_analysis(analysis: str) -> Dict[str, Any]:
    """Extract numerical metrics from the analysis text."""
    import re
    
    metrics = {
        "price_change": None,
        "supply_change": None,
        "demand_change": None,
        "grid_stability": None,
        "inflation_impact": None,
    }
    
    # Try to extract price change
    price_match = re.search(r'[Pp]rice[^:]*:\s*([+-]?\d+(?:\.\d+)?)\s*%', analysis)
    if price_match:
        metrics["price_change"] = float(price_match.group(1))
    
    # Try to extract supply change
    supply_match = re.search(r'[Ss]upply[^:]*:\s*([+-]?\d+(?:,\d{3})*(?:\.\d+)?)\s*MW', analysis)
    if supply_match:
        metrics["supply_change"] = float(supply_match.group(1).replace(',', ''))
    
    # Try to extract grid stability
    stability_match = re.search(r'[Ss]tability[^:]*:\s*(\d+(?:\.\d+)?)\s*(?:/10|out of 10)?', analysis)
    if stability_match:
        metrics["grid_stability"] = float(stability_match.group(1))
    
    # Try to extract inflation impact
    inflation_match = re.search(r'[Ii]nflation[^:]*:\s*([+-]?\d+(?:\.\d+)?)\s*(?:basis points|bps|bp)', analysis)
    if inflation_match:
        metrics["inflation_impact"] = float(inflation_match.group(1))
    
    return metrics


def display_what_if_result(result: Dict[str, Any]):
    """Display the what-if analysis result in a professional format."""
    
    if result.get("error"):
        st.error(f"Analysis failed: {result['error']}")
        with st.expander("Error Details"):
            st.code(result.get("traceback", "No traceback available"))
        return
    
    # Header with timestamp
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin: 1.5rem 0 1rem 0;">
        <div style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 900; color: #FFFFFF;">📊 Analysis Result</div>
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #808080;">
            ⏱️ {result.get('processing_time_ms', 0)/1000:.1f}s | 📅 {datetime.now().strftime('%H:%M:%S')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Extracted metrics
    metrics = result.get("metrics_extracted", {})
    
    if any(v is not None for v in metrics.values()):
        st.markdown("""
        <div style="font-family: 'Inter', sans-serif; font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin: 1.5rem 0 1rem 0;">📈 Key Metric Changes</div>
        """, unsafe_allow_html=True)
        metric_cols = st.columns(5)
        
        metric_displays = [
            ("Price", metrics.get("price_change"), "%", "💰"),
            ("Supply", metrics.get("supply_change"), "MW", "⚡"),
            ("Demand", metrics.get("demand_change"), "MW", "🏭"),
            ("Stability", metrics.get("grid_stability"), "/10", "🔌"),
            ("Inflation", metrics.get("inflation_impact"), "bps", "📊"),
        ]
        
        for col, (name, value, unit, icon) in zip(metric_cols, metric_displays):
            with col:
                if value is not None:
                    if isinstance(value, float) and name in ["Price", "Supply", "Demand", "Inflation"]:
                        if value > 0:
                            color = "#ef4444" if name == "Price" else "#22c55e"
                            prefix = "+"
                        elif value < 0:
                            color = "#22c55e" if name == "Price" else "#ef4444"
                            prefix = ""
                        else:
                            color = "#808080"
                            prefix = ""
                        st.markdown(f"""
                        <div style="background: transparent; border-left: 3px solid {color}; padding: 12px 16px;">
                            <div style="font-size: 1.25rem;">{icon}</div>
                            <div style="font-family: 'Inter', sans-serif; font-size: 2rem; font-weight: 900; color: {color};">{prefix}{value:.1f}<span style="font-size: 1rem;">{unit}</span></div>
                            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">{name}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: transparent; border-left: 3px solid #3b82f6; padding: 12px 16px;">
                            <div style="font-size: 1.25rem;">{icon}</div>
                            <div style="font-family: 'Inter', sans-serif; font-size: 2rem; font-weight: 900; color: #FFFFFF;">{value}{unit}</div>
                            <div style="font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">{name}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: transparent; border-left: 3px solid #1A1A1A; padding: 12px 16px;">
                        <div style="font-size: 1.25rem;">{icon}</div>
                        <div style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 700; color: #4A4A4A;">N/A</div>
                        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #808080; text-transform: uppercase; letter-spacing: 0.05em;">{name}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1.5rem; border-top: 1px solid #1A1A1A; margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Main analysis
    st.markdown("""
    <div style="font-family: 'Inter', sans-serif; font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin: 1rem 0;">📝 Detailed Analysis</div>
    """, unsafe_allow_html=True)
    analysis = result.get("analysis", "No analysis available")
    
    # Split analysis into sections for better display
    st.markdown(f"""
    <div style="background: transparent; border-left: 3px solid #3b82f6; padding: 16px 20px; margin: 12px 0;">
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.9375rem; color: #B0B0B0; line-height: 1.6;">
            {analysis.replace(chr(10), '<br>')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Fresh data used
    fresh_data = result.get("fresh_data_used", {})
    if fresh_data and not fresh_data.get("error"):
        with st.expander("🌐 Fresh External Data Used", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Google Trends**")
                trends = fresh_data.get("google_trends", {})
                if trends:
                    st.write(f"Keywords: {', '.join(trends.get('keywords', []))}")
                    st.write(f"Data type: {'Real API' if trends.get('is_real') else 'Simulated'}")
            
            with col2:
                st.markdown("**News Articles**")
                news = fresh_data.get("news", [])
                if news:
                    for article in news[:3]:
                        if isinstance(article, dict):
                            st.caption(f"• {article.get('title', 'Article')[:80]}...")


def render_what_if_view(debug_mode: bool = False):
    """
    Main render function for the What-If Scenario tab.
    """
    inject_what_if_css()
    
    # Header - matching Executive Summary design
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.875rem; font-weight: 400; color: #B0B0B0; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;">
            Scenario Exploration
        </div>
        <h1 style="font-family: 'Inter', sans-serif; font-size: 3rem; font-weight: 900; color: #FFFFFF; margin: 0; line-height: 1;">
            What-If Explorer
        </h1>
        <p style="font-family: 'Roboto Mono', monospace; font-size: 1rem; color: #B0B0B0; margin-top: 0.5rem;">
            Explore hypothetical scenarios and their potential impacts on the Swedish energy market
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for what-if history
    if "what_if_history" not in st.session_state:
        st.session_state.what_if_history = []
    
    # Check if we have any data to analyze
    aggregated = aggregate_all_results()
    data_sources = aggregated.get("data_sources", [])
    
    if not data_sources:
        st.warning("""
        ⚠️ **No Simulation Data Available**
        
        Please go to the **📊 Executive Summary** tab first and run a complete system analysis.
        The What-If Explorer needs simulation data to build hypothetical scenarios on top of.
        """)
        
        with st.expander("📋 What data is needed?"):
            st.markdown("""
            The What-If Explorer aggregates data from:
            - **Timeline Simulation** - Hourly projections
            - **Multi-Agent Analysis** - LLM-powered insights
            - **Historical Events** - Swedish energy history
            - **External APIs** - Google Trends, news
            - **Grid State** - Current system status
            
            Run a full analysis from the Executive Summary tab to populate these.
            """)
        return
    
    # Show available data sources
    with st.expander(f"📊 Available Data ({len(data_sources)} sources)", expanded=False):
        cols = st.columns(len(data_sources))
        source_icons = {
            "scenario_config": "⚙️",
            "timeline_simulation": "⏱️",
            "llm_multi_agent": "🤖",
            "historical_events": "📚",
            "external_apis": "🌐",
            "digital_twin": "🔌",
            "simulation_results": "📈",
        }
        for col, source in zip(cols, data_sources):
            with col:
                icon = source_icons.get(source, "📦")
                st.markdown(f"""
                <div style="background: transparent; border-left: 3px solid #22c55e; padding: 12px 16px;">
                    <div style="font-size: 1.5rem;">{icon}</div>
                    <div style="font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; color: #22c55e; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;">{source.replace('_', ' ')}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1.5rem; border-top: 1px solid #1A1A1A; margin-top: 1rem;'></div>", unsafe_allow_html=True)
    
    # Main prompt area
    st.markdown("""
    <div style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 900; color: #FFFFFF; margin: 1rem 0;">💭 Ask a What-If Question</div>
    """, unsafe_allow_html=True)
    
    # Example prompts
    example_prompts = [
        "What if we fix the hydro shortage issue halfway through the scenario?",
        "What if nuclear output increases by 20% due to a reactor restart?",
        "What if demand drops suddenly due to industrial shutdown?",
        "What if the interconnector cable to Norway fails?",
        "What if temperatures drop another 5°C across Sweden?",
        "What if gas prices in Europe spike by 50%?",
    ]
    
    # Initialize selected example state
    if "selected_example_prompt" not in st.session_state:
        st.session_state.selected_example_prompt = ""
    
    # Handle example selection (must be before the widget)
    example_clicked = None
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("""
        <div style="font-family: 'Inter', sans-serif; font-size: 0.875rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Quick Examples:</div>
        """, unsafe_allow_html=True)
        for i, example in enumerate(example_prompts[:3]):
            if st.button(f"💡 {example[:40]}...", key=f"example_{i}", use_container_width=True):
                example_clicked = example
    
    # If example was clicked, set it before the text area is rendered
    if example_clicked:
        st.session_state.selected_example_prompt = example_clicked
    
    with col1:
        # Use the selected example as default value
        default_value = st.session_state.selected_example_prompt
        what_if_prompt = st.text_area(
            "Describe your hypothetical scenario:",
            value=default_value,
            placeholder="e.g., What if we increase nuclear output by 15% and reduce industrial demand?",
            height=100,
            key="what_if_prompt_area",
        )
        # Clear the selected example after it's used
        if st.session_state.selected_example_prompt and what_if_prompt != st.session_state.selected_example_prompt:
            st.session_state.selected_example_prompt = ""
    
    # Rerun if example was clicked to update the text area
    if example_clicked:
        st.rerun()
    
    # Run analysis button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_button = st.button(
            "🚀 Analyze What-If Scenario",
            type="primary",
            use_container_width=True,
            disabled=not what_if_prompt,
        )
    
    if run_button and what_if_prompt:
        with st.status("🔮 Analyzing What-If Scenario...", expanded=True) as status:
            # Step 1: Aggregate all data
            st.write("📊 Aggregating all simulation data...")
            aggregated = aggregate_all_results()
            
            # Step 2: Fetch fresh external data
            st.write("🌐 Fetching fresh Google Trends & news data...")
            fresh_data = asyncio.run(fetch_fresh_external_data(what_if_prompt))
            
            # Step 3: Run LLM analysis
            st.write("🤖 Running AI analysis (this may take 15-30 seconds)...")
            result = asyncio.run(run_what_if_analysis(aggregated, what_if_prompt, fresh_data))
            
            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
        
        # Store in history
        st.session_state.what_if_history.insert(0, {
            "prompt": what_if_prompt,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Keep only last 10 analyses
        st.session_state.what_if_history = st.session_state.what_if_history[:10]
        
        # Display result
        display_what_if_result(result)
    
    # Display history
    if st.session_state.what_if_history:
        st.markdown("<div style='height: 1.5rem; border-top: 1px solid #1A1A1A; margin-top: 2rem;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 900; color: #FFFFFF; margin: 1rem 0;">📜 Analysis History</div>
        """, unsafe_allow_html=True)
        
        for i, item in enumerate(st.session_state.what_if_history):
            with st.expander(
                f"{'🔮' if i == 0 else '📋'} {item['prompt'][:60]}... ({item['timestamp'][11:19]})",
                expanded=(i == 0 and not run_button)
            ):
                display_what_if_result(item["result"])
    
    # Debug mode
    if debug_mode:
        with st.expander("🔧 Debug: Aggregated Data"):
            st.json(aggregated)
