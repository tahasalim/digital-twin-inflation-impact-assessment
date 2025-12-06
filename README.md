# Swedish Energy Digital Twin 🇸🇪⚡

A digital twin of Sweden's energy sector for Riksbanken (Swedish Central Bank) that enables **simulation of economic shocks** and visualization of **domino effects** on inflation.

## 🎯 Features

- **Digital Twin Engine**: Real-time state management with simulation branching
- **Agent-Based Simulation**: Mesa 3.x agents (producers, consumers, retailers, grid operator)
- **Shock Scenarios**: Pre-built Swedish and global event simulations
- **Domino Effect Tracking**: Visualize cascade effects through the energy system
- **CPI Impact Analysis**: Estimate inflation impact from energy shocks
- **Orchestrator Agent**: Compares simulations vs reality, produces insights

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install the package
pip install -e .
```

### 2. Run the CLI

```powershell
# Initialize the digital twin
python -m src.cli init

# List available scenarios
python -m src.cli scenarios

# Run a simulation
python -m src.cli run nordic_drought

# Launch interactive dashboard
python -m src.cli dashboard
```

### 3. Launch Dashboard

```powershell
streamlit run src/dashboard/app.py
```

Open http://localhost:8501

## 📊 Available Scenarios

### 🇸🇪 Swedish Events
| Scenario | Description |
|----------|-------------|
| `nordic_drought` | Hydro production drops 50% in SE1/SE2 |
| `nuclear_outage` | Forsmark reactor trip, 1.4 GW offline |
| `winter_cold_wave` | -30°C temperatures, heating demand +50% |
| `baltic_cable_failure` | NordBalt/SwePol cables damaged |
| `wind_lull` | Wind production at 10% for 5 days |

### 🌍 Global Events
| Scenario | Description |
|----------|-------------|
| `european_gas_crisis` | TTF gas price triples |
| `continental_heatwave` | Nuclear cooling issues across Europe |
| `trade_war_rare_earths` | China restricts rare earth exports |
| `oil_price_shock` | Brent crude doubles |
| `carbon_price_surge` | EU ETS jumps to €150/ton |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│  (Compares simulations vs reality, produces insights)       │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌───────────────┐           ┌───────────────┐
│  Simulation   │           │   Reality     │
│   Branch      │           │   State       │
└───────┬───────┘           └───────┬───────┘
        │                           │
        ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Mesa Agent Model                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Producer │ │Industry │ │Household│ │Retailer │           │
│  │ Agent   │ │ Agent   │ │ Agent   │ │ Agent   │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └───────────┴───────────┴───────────┘                 │
│                       │                                      │
│                       ▼                                      │
│              ┌─────────────────┐                            │
│              │  Grid Operator  │                            │
│              │     Agent       │                            │
│              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
src/
├── models/          # Pydantic data models
│   └── energy.py    # Zones, producers, consumers, events
├── twin/            # Digital twin core
│   └── engine.py    # State management, branching
├── agents/          # Mesa agents
│   └── energy_agents.py  # Producer, consumer, retailer agents
├── simulation/      # Scenario definitions
│   └── scenarios.py # Pre-built shock scenarios
├── orchestrator/    # Comparison & insights
│   └── agent.py     # Orchestrator agent
├── dashboard/       # Streamlit UI
│   └── app.py       # Interactive dashboard
└── cli.py           # Command-line interface
```

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Simulation | Mesa 3.x |
| Data Models | Pydantic 2.x |
| API | FastAPI |
| Visualization | Streamlit + Plotly |
| CLI | Typer + Rich |
| DataFrames | Polars + Pandas |

## 🎓 For Riksbank Economists

The digital twin produces insights relevant to monetary policy:

1. **CPI Transmission**: Track how energy price shocks propagate to consumer prices
2. **Early Warning**: Detect anomalies before they appear in official statistics
3. **Scenario Planning**: Test "what-if" scenarios for policy preparation
4. **Domino Effects**: Visualize cascading impacts across economic sectors

## 📈 Example Output

```
💥 Running scenario: nordic_drought

🎯 Domino Effects (12 total)

Step | Source → Target        | Effect              | Magnitude   | CPI Impact
-----|------------------------|---------------------|-------------|------------
1    | producer_0 → zone_SE1  | production_reduction| 3000.0 MW   | -
2    | zone_SE1 → zone_SE2    | price_increase      | 15.0 EUR    | -
3    | industrial_1 → economy | output_reduction    | 50000.0 EUR | -
4    | households_SE3 → cpi   | energy_cost         | 1200000 EUR | +45 bps

💰 Total Cost Impact: €2,450,000

💡 Economic Insights
🚨 CPI Pressure from Nordic Drought 2024
   Total estimated impact: 45 basis points
```

## 🤝 Contributing

Built for the Riksbank Hackathon 2024 - Building inflation forecasting models with alternative data sources and AI.
