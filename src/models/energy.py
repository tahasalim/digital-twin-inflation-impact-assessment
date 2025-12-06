"""
Energy Sector Data Models for Swedish Digital Twin.

Represents the complete Swedish energy system including:
- 4 bidding zones (SE1-SE4)
- Nordic and European interconnections
- Energy producers, consumers, and market dynamics
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ZoneId(str, Enum):
    """Swedish electricity bidding zones."""
    SE1 = "SE1"  # Luleå (North) - Hydro dominant, surplus
    SE2 = "SE2"  # Sundsvall - Transition zone
    SE3 = "SE3"  # Stockholm - Major consumption center
    SE4 = "SE4"  # Malmö (South) - Highest prices, import-dependent


class CountryCode(str, Enum):
    """Nordic and Baltic countries for interconnections."""
    SE = "SE"  # Sweden
    NO = "NO"  # Norway (multiple zones)
    FI = "FI"  # Finland
    DK = "DK"  # Denmark
    DE = "DE"  # Germany
    PL = "PL"  # Poland
    LT = "LT"  # Lithuania
    EE = "EE"  # Estonia
    LV = "LV"  # Latvia


class EnergySourceType(str, Enum):
    """Types of energy production."""
    HYDRO = "hydro"
    NUCLEAR = "nuclear"
    WIND = "wind"
    SOLAR = "solar"
    BIOMASS = "biomass"
    GAS = "gas"
    COAL = "coal"
    IMPORT = "import"


class ConsumerType(str, Enum):
    """Types of energy consumers."""
    INDUSTRIAL = "industrial"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    TRANSPORT = "transport"
    DATA_CENTER = "data_center"


class EventType(str, Enum):
    """Types of simulation events (shocks)."""
    # Supply-side shocks
    DROUGHT = "drought"  # Affects hydro production
    NUCLEAR_OUTAGE = "nuclear_outage"
    WIND_CALM = "wind_calm"
    CABLE_FAILURE = "cable_failure"
    
    # Demand-side shocks
    COLD_WAVE = "cold_wave"
    HEAT_WAVE = "heat_wave"
    INDUSTRIAL_SURGE = "industrial_surge"
    
    # Market/Geopolitical shocks
    GAS_PRICE_SPIKE = "gas_price_spike"
    CARBON_TAX_INCREASE = "carbon_tax_increase"
    TRADE_RESTRICTION = "trade_restriction"
    CURRENCY_SHOCK = "currency_shock"
    
    # Global events
    OIL_CRISIS = "oil_crisis"
    WAR_OUTBREAK = "war_outbreak"
    PANDEMIC = "pandemic"


class BiddingZone(BaseModel):
    """A Swedish electricity bidding zone."""
    
    zone_id: ZoneId
    name: str
    description: str
    
    # Capacity and production
    total_capacity_mw: float = Field(ge=0, description="Total generation capacity in MW")
    current_production_mw: float = Field(ge=0, description="Current production in MW")
    current_consumption_mw: float = Field(ge=0, description="Current consumption in MW")
    
    # Energy mix percentages
    hydro_share: float = Field(ge=0, le=1, default=0.0)
    nuclear_share: float = Field(ge=0, le=1, default=0.0)
    wind_share: float = Field(ge=0, le=1, default=0.0)
    other_share: float = Field(ge=0, le=1, default=0.0)
    
    # Market state
    spot_price_eur_mwh: float = Field(description="Current spot price EUR/MWh")
    
    # Calculated properties
    @property
    def net_position_mw(self) -> float:
        """Positive = export, Negative = import."""
        return self.current_production_mw - self.current_consumption_mw
    
    @property
    def is_surplus_zone(self) -> bool:
        return self.net_position_mw > 0


class GridConnection(BaseModel):
    """An interconnection between zones or countries."""
    
    connection_id: str
    from_zone: str  # ZoneId or CountryCode
    to_zone: str
    
    capacity_mw: float = Field(ge=0, description="Maximum transfer capacity")
    current_flow_mw: float = Field(description="Current flow (positive = from->to)")
    
    # Status
    is_operational: bool = True
    outage_reason: Optional[str] = None
    
    @property
    def utilization_pct(self) -> float:
        if self.capacity_mw == 0:
            return 0.0
        return abs(self.current_flow_mw) / self.capacity_mw * 100


class EnergyProducer(BaseModel):
    """An energy producer in the system."""
    
    producer_id: str
    name: str
    zone: ZoneId
    source_type: EnergySourceType
    
    capacity_mw: float = Field(ge=0)
    current_output_mw: float = Field(ge=0)
    marginal_cost_eur_mwh: float = Field(ge=0)
    
    # Behavioral parameters for simulation
    ramp_rate_mw_per_min: float = Field(ge=0, default=10.0)
    min_output_pct: float = Field(ge=0, le=1, default=0.0)
    
    # Shock sensitivity
    drought_sensitivity: float = Field(ge=0, le=1, default=0.0)
    wind_dependency: float = Field(ge=0, le=1, default=0.0)
    fuel_price_sensitivity: float = Field(ge=0, le=1, default=0.0)


class EnergyConsumer(BaseModel):
    """An energy consumer in the system."""
    
    consumer_id: str
    name: str
    zone: ZoneId
    consumer_type: ConsumerType
    
    base_demand_mw: float = Field(ge=0)
    current_demand_mw: float = Field(ge=0)
    
    # Price elasticity (-1 = reduces demand 1% per 1% price increase)
    price_elasticity: float = Field(le=0, default=-0.1)
    
    # Temperature sensitivity (demand change per degree C)
    temperature_sensitivity: float = Field(default=0.02)
    
    # Industrial specific
    can_shed_load: bool = False
    shedding_threshold_eur_mwh: Optional[float] = None


class MarketPrice(BaseModel):
    """Market price data point."""
    
    timestamp: datetime
    zone: ZoneId
    
    spot_price_eur_mwh: float
    day_ahead_price_eur_mwh: Optional[float] = None
    intraday_price_eur_mwh: Optional[float] = None
    
    # Volume
    volume_mwh: Optional[float] = None
    
    # Comparison to historical
    price_vs_avg_30d_pct: Optional[float] = None


class EnergySystemState(BaseModel):
    """Complete state of the Swedish energy system at a point in time."""
    
    timestamp: datetime
    is_simulation: bool = False
    simulation_id: Optional[str] = None
    
    # All zones
    zones: dict[ZoneId, BiddingZone]
    
    # All connections (internal + cross-border)
    connections: list[GridConnection]
    
    # Aggregated metrics
    total_production_mw: float
    total_consumption_mw: float
    total_import_mw: float
    total_export_mw: float
    
    # System-wide price metrics
    volume_weighted_avg_price_eur: float
    price_spread_se1_se4_eur: float  # North-South price difference
    
    # Economic indicators
    estimated_hourly_cost_meur: float
    
    def clone_for_simulation(self, sim_id: str) -> "EnergySystemState":
        """Create a simulation branch from current state."""
        data = self.model_dump()
        data["is_simulation"] = True
        data["simulation_id"] = sim_id
        return EnergySystemState(**data)


class DominoEffect(BaseModel):
    """A single domino effect in a chain of consequences."""
    
    step: int = Field(ge=1, description="Order in the domino chain")
    
    source: str  # What caused this effect
    target: str  # What is affected
    effect_type: str  # Type of effect (price_increase, demand_drop, etc.)
    
    magnitude: float  # Size of the effect
    unit: str  # Unit of measurement
    
    description: str  # Human-readable description
    
    # Timing
    delay_hours: float = Field(ge=0, description="Time delay from trigger")
    duration_hours: Optional[float] = None
    
    # Economic impact
    cost_impact_eur: Optional[float] = None
    cpi_impact_bps: Optional[float] = None  # Basis points impact on CPI


class SimulationEvent(BaseModel):
    """An event to simulate in the digital twin."""
    
    event_id: str
    event_type: EventType
    name: str
    description: str
    
    # Timing
    start_time: datetime
    duration_hours: float = Field(ge=0)
    
    # Scope
    affected_zones: list[ZoneId] = Field(default_factory=list)
    affected_countries: list[CountryCode] = Field(default_factory=list)
    is_global: bool = False
    
    # Magnitude (0-1 scale, 1 = maximum severity)
    severity: float = Field(ge=0, le=1)
    
    # Shock parameters (event-type specific)
    parameters: dict = Field(default_factory=dict)
    
    # Results (populated after simulation)
    domino_effects: list[DominoEffect] = Field(default_factory=list)
    total_cost_impact_eur: Optional[float] = None
    peak_price_impact_pct: Optional[float] = None


# Default Swedish energy system configuration
SWEDEN_ZONES_CONFIG = {
    ZoneId.SE1: {
        "name": "Luleå",
        "description": "Northern Sweden - Hydro dominant, major exporter",
        "total_capacity_mw": 8500,
        "hydro_share": 0.85,
        "nuclear_share": 0.0,
        "wind_share": 0.10,
    },
    ZoneId.SE2: {
        "name": "Sundsvall",
        "description": "North-Central Sweden - Transition zone",
        "total_capacity_mw": 4500,
        "hydro_share": 0.60,
        "nuclear_share": 0.0,
        "wind_share": 0.25,
    },
    ZoneId.SE3: {
        "name": "Stockholm",
        "description": "Central Sweden - Major consumption, nuclear power",
        "total_capacity_mw": 15000,
        "hydro_share": 0.15,
        "nuclear_share": 0.45,
        "wind_share": 0.20,
    },
    ZoneId.SE4: {
        "name": "Malmö",
        "description": "Southern Sweden - Import dependent, highest prices",
        "total_capacity_mw": 5000,
        "hydro_share": 0.05,
        "nuclear_share": 0.0,
        "wind_share": 0.40,
    },
}

# Nordic interconnections (simplified)
NORDIC_CONNECTIONS = [
    # Internal Swedish
    {"from": "SE1", "to": "SE2", "capacity_mw": 3300},
    {"from": "SE2", "to": "SE3", "capacity_mw": 7300},
    {"from": "SE3", "to": "SE4", "capacity_mw": 5400},
    
    # Cross-border
    {"from": "SE1", "to": "FI", "capacity_mw": 1500},
    {"from": "SE2", "to": "NO", "capacity_mw": 600},
    {"from": "SE3", "to": "NO", "capacity_mw": 2145},
    {"from": "SE3", "to": "FI", "capacity_mw": 1200},
    {"from": "SE3", "to": "DK", "capacity_mw": 1700},
    {"from": "SE4", "to": "DK", "capacity_mw": 1400},
    {"from": "SE4", "to": "DE", "capacity_mw": 615},
    {"from": "SE4", "to": "PL", "capacity_mw": 600},
    {"from": "SE4", "to": "LT", "capacity_mw": 700},
]
