"""
Timeline-Based Simulation Engine with Checkpoints.

This module provides a temporal simulation system where:
- Checkpoints capture complete system state at each hour
- Events trigger changes that propagate through the system
- Statistics are tracked and key moments identified
- Real-time data from APIs is integrated when available
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
from loguru import logger
import asyncio

from src.models.energy import (
    ZoneId,
    EventType,
    SWEDEN_ZONES_CONFIG,
)
from src.data.real_data_integration import (
    get_real_data_integration,
    RealTimeMarketData,
)


class CheckpointType(str, Enum):
    """Type of checkpoint."""
    INITIAL = "initial"
    HOURLY = "hourly"
    EVENT = "event"
    FINAL = "final"


class ZoneSnapshot(BaseModel):
    """Complete state of a single zone at a checkpoint."""
    
    zone_id: ZoneId
    name: str
    
    # Production
    production_mw: float
    production_by_source: dict[str, float] = Field(default_factory=dict)
    capacity_mw: float
    utilization_pct: float = 0
    
    # Consumption
    consumption_mw: float
    consumption_by_sector: dict[str, float] = Field(default_factory=dict)
    
    # Price
    spot_price_eur_mwh: float
    price_change_pct: float = 0  # Change from previous checkpoint
    
    # Balance
    @property
    def balance_mw(self) -> float:
        return self.production_mw - self.consumption_mw
    
    @property
    def is_deficit(self) -> bool:
        return self.balance_mw < -50  # Significant deficit threshold


class SystemSnapshot(BaseModel):
    """Complete system state at a checkpoint - all zones + aggregates."""
    
    checkpoint_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    checkpoint_type: CheckpointType
    
    # Time
    timestamp: datetime
    hour: int  # Hours from simulation start (0, 1, 2, ...)
    
    # Zone states
    zones: dict[ZoneId, ZoneSnapshot]
    
    # System aggregates
    total_production_mw: float
    total_consumption_mw: float
    system_balance_mw: float
    
    # Prices
    avg_price_eur_mwh: float
    min_price_eur_mwh: float
    max_price_eur_mwh: float
    price_spread_eur: float  # SE4 - SE1
    
    # Status
    alert_level: int = 0  # 0=normal, 1=elevated, 2=critical
    active_events: list[str] = Field(default_factory=list)
    
    # Economic impact
    hourly_cost_eur: float = 0
    cumulative_cost_eur: float = 0
    cpi_pressure_bps: float = 0
    
    # Changes
    changes_description: list[str] = Field(default_factory=list)


class SimulationEvent(BaseModel):
    """An event that triggers during simulation."""
    
    event_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    event_type: EventType
    name: str
    description: str
    
    # Timing
    start_hour: int
    duration_hours: int
    
    # Scope
    affected_zones: list[ZoneId] = Field(default_factory=list)  # Empty = all zones
    severity: float = Field(ge=0, le=1, default=0.5)
    
    # Effects
    production_impact_pct: dict[str, float] = Field(default_factory=dict)
    demand_impact_pct: float = 0
    price_impact_eur: float = 0
    
    def is_active_at(self, hour: int) -> bool:
        return self.start_hour <= hour < self.start_hour + self.duration_hours


class KeyMoment(BaseModel):
    """A significant moment detected during simulation."""
    
    hour: int
    severity: str  # "info", "warning", "critical"
    category: str
    zone: Optional[ZoneId] = None
    title: str
    description: str
    value: Optional[float] = None
    unit: Optional[str] = None


class SimulationSummary(BaseModel):
    """Summary of the entire simulation with key insights."""
    
    name: str
    total_hours: int
    num_checkpoints: int
    
    # Key moments
    key_moments: list[KeyMoment] = Field(default_factory=list)
    
    # Peak values
    peak_price_eur: float = 0
    peak_price_hour: int = 0
    peak_price_zone: Optional[ZoneId] = None
    
    lowest_balance_mw: float = 0
    lowest_balance_hour: int = 0
    
    # Totals
    total_system_cost_eur: float = 0
    total_deficit_hours: int = 0
    total_alert_hours: int = 0
    max_cpi_pressure_bps: float = 0


class Timeline(BaseModel):
    """A complete simulation timeline with all checkpoints."""
    
    timeline_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str
    description: str = ""
    
    # Time range
    start_time: datetime
    end_time: datetime
    
    # Data
    checkpoints: list[SystemSnapshot] = Field(default_factory=list)
    events: list[SimulationEvent] = Field(default_factory=list)
    summary: Optional[SimulationSummary] = None
    
    # Status
    is_complete: bool = False
    
    @property
    def total_hours(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 3600)
    
    def get_checkpoint(self, hour: int) -> Optional[SystemSnapshot]:
        """Get checkpoint at specific hour."""
        for cp in self.checkpoints:
            if cp.hour == hour:
                return cp
        return None


class TimelineSimulator:
    """
    Main simulation engine that generates checkpoints over time.
    
    Integrates real-time data from APIs when available:
    - Live electricity prices from Nord Pool
    - Weather data from SMHI (affects demand)
    - Economic indicators from SCB/FRED
    """
    
    # Default baseline prices by zone (EUR/MWh) - used when real data unavailable
    DEFAULT_BASELINE_PRICES = {
        ZoneId.SE1: 25.0,
        ZoneId.SE2: 35.0,
        ZoneId.SE3: 50.0,
        ZoneId.SE4: 65.0,
    }
    
    def __init__(self):
        self.current_timeline: Optional[Timeline] = None
        self._real_data_integration = get_real_data_integration()
        self._real_data: Optional[RealTimeMarketData] = None
        self._using_live_data: bool = False
    
    @property
    def BASELINE_PRICES(self) -> Dict[ZoneId, float]:
        """Get baseline prices - from real data if available, else defaults."""
        if self._real_data is not None and self._real_data.is_live_data:
            return self._real_data_integration.get_baseline_prices_from_real_data()
        return self.DEFAULT_BASELINE_PRICES
    
    async def initialize_with_real_data(self) -> bool:
        """
        Fetch real-time data before running simulation.
        
        Returns True if live data was successfully fetched.
        """
        try:
            logger.info("Fetching real-time market data for simulation...")
            self._real_data = await self._real_data_integration.fetch_market_data()
            self._using_live_data = self._real_data.is_live_data
            
            if self._using_live_data:
                logger.success(f"✓ Using LIVE data: {self._real_data.spot_prices}")
            else:
                logger.warning("Using fallback data - live APIs unavailable")
            
            return self._using_live_data
        except Exception as e:
            logger.error(f"Failed to fetch real data: {e}")
            self._using_live_data = False
            return False
    
    def get_data_status(self) -> Dict[str, Any]:
        """Get status of real-time data integration."""
        return {
            "using_live_data": self._using_live_data,
            "fetch_timestamp": self._real_data.fetch_timestamp if self._real_data else None,
            "sources": self._real_data.sources_used if self._real_data else {},
            "current_prices": self._real_data.spot_prices if self._real_data else self.DEFAULT_BASELINE_PRICES,
        }
    
    def create_timeline(
        self,
        name: str,
        duration_hours: int,
        events: list[SimulationEvent] = None,
        start_time: datetime = None,
    ) -> Timeline:
        """Create a new simulation timeline."""
        
        if start_time is None:
            start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        timeline = Timeline(
            name=name,
            start_time=start_time,
            end_time=start_time + timedelta(hours=duration_hours),
            events=events or [],
        )
        
        self.current_timeline = timeline
        return timeline
    
    def _create_zone_snapshot(
        self,
        zone_id: ZoneId,
        config: dict,
        prev_snapshot: Optional[ZoneSnapshot] = None,
        active_events: list[SimulationEvent] = None,
    ) -> ZoneSnapshot:
        """Create a zone snapshot, applying any active events and real-time data."""
        
        capacity = config["total_capacity_mw"]
        
        # Base utilization varies by zone
        base_util = {
            ZoneId.SE1: 0.65,
            ZoneId.SE2: 0.60,
            ZoneId.SE3: 0.75,
            ZoneId.SE4: 0.50,
        }.get(zone_id, 0.6)
        
        # Get weather-based demand modifier from real data
        weather_demand_modifier = 1.0
        if self._real_data is not None:
            weather_demand_modifier = self._real_data_integration.get_weather_demand_modifier(zone_id.value)
        
        # Start from previous values or baseline
        if prev_snapshot:
            production = prev_snapshot.production_mw
            consumption = prev_snapshot.consumption_mw
            price = prev_snapshot.spot_price_eur_mwh
            prod_by_source = prev_snapshot.production_by_source.copy()
        else:
            production = capacity * base_util
            # Apply weather modifier to initial consumption
            consumption = capacity * 0.5 * weather_demand_modifier
            price = self.BASELINE_PRICES[zone_id]  # Uses real data if available
            prod_by_source = {
                "hydro": production * config["hydro_share"],
                "nuclear": production * config.get("nuclear_share", 0),
                "wind": production * config["wind_share"],
                "other": production * (1 - config["hydro_share"] - config.get("nuclear_share", 0) - config["wind_share"]),
            }
        
        # Apply events
        for event in (active_events or []):
            if event.affected_zones and zone_id not in event.affected_zones:
                continue
            
            # Production impacts by source
            for source, impact_pct in event.production_impact_pct.items():
                if source in prod_by_source:
                    reduction = prod_by_source[source] * impact_pct * event.severity
                    prod_by_source[source] = max(0, prod_by_source[source] - reduction)
            
            # Demand impacts
            if event.demand_impact_pct != 0:
                consumption *= (1 + event.demand_impact_pct * event.severity)
            
            # Price impacts - apply as percentage modifier, not additive
            # A 20€ impact on a 50€ baseline = 40% increase
            price_impact_pct = event.price_impact_eur / 50.0  # Normalize to baseline ~50€
            price *= (1 + price_impact_pct * event.severity * 0.1)  # Dampened effect
        
        # Recalculate total production
        production = sum(prod_by_source.values())
        
        # Apply market dynamics (supply/demand affects price) - more moderate
        imbalance = consumption - production
        if imbalance > 0:  # Deficit pushes price up
            price += imbalance / 2000 * 2  # Reduced from /1000 * 5
        elif imbalance < 0:  # Surplus pushes price down
            price = max(10, price - abs(imbalance) / 2000 * 1)  # Floor at 10€
        
        # Mean reversion toward baseline - stronger pull to prevent runaway prices
        baseline = self.BASELINE_PRICES[zone_id]
        reversion_strength = 0.15  # Increased from 0.03
        price += (baseline - price) * reversion_strength
        
        # Hard cap on prices - even extreme crises rarely exceed 500€/MWh for extended periods
        price = min(max(10, price), 500)
        
        # Calculate price change
        prev_price = prev_snapshot.spot_price_eur_mwh if prev_snapshot else self.BASELINE_PRICES[zone_id]
        price_change_pct = ((price - prev_price) / prev_price * 100) if prev_price > 0 else 0
        
        return ZoneSnapshot(
            zone_id=zone_id,
            name=config["name"],
            production_mw=production,
            production_by_source=prod_by_source,
            capacity_mw=capacity,
            utilization_pct=production / capacity * 100,
            consumption_mw=consumption,
            consumption_by_sector={
                "industrial": consumption * 0.40,
                "residential": consumption * 0.35,
                "commercial": consumption * 0.25,
            },
            spot_price_eur_mwh=price,
            price_change_pct=price_change_pct,
        )
    
    def _create_system_snapshot(
        self,
        hour: int,
        timestamp: datetime,
        zones: dict[ZoneId, ZoneSnapshot],
        active_event_names: list[str],
        prev_snapshot: Optional[SystemSnapshot],
        checkpoint_type: CheckpointType,
    ) -> SystemSnapshot:
        """Create a complete system snapshot."""
        
        total_prod = sum(z.production_mw for z in zones.values())
        total_cons = sum(z.consumption_mw for z in zones.values())
        balance = total_prod - total_cons
        
        prices = [z.spot_price_eur_mwh for z in zones.values()]
        avg_price = sum(prices) / len(prices)
        
        # Alert level based on balance
        alert = 0
        if abs(balance) > 1500:
            alert = 2
        elif abs(balance) > 500:
            alert = 1
        
        # CPI pressure - more realistic calculation
        # Energy is ~4-5% of CPIF weight, price increases translate to CPI impact
        # A 50% electricity price increase would add ~2-2.5% to annual CPI = ~200-250 bps
        baseline_avg = sum(self.BASELINE_PRICES.values()) / 4  # ~43.75 €/MWh
        price_increase_pct = max(0, (avg_price - baseline_avg) / baseline_avg * 100)
        
        # Realistic: 100% price increase = ~250 bps annual CPI impact
        # For hourly calculation, divide by hours in month (720) to get hourly contribution
        # But we're showing cumulative pressure, so use monthly factor
        cpi_pressure = price_increase_pct * 2.5  # bps per 100% price increase
        cpi_pressure = min(cpi_pressure, 500)  # Cap at 500 bps - even extreme scenarios
        
        # Hourly cost
        hourly_cost = total_cons * avg_price
        cumulative = (prev_snapshot.cumulative_cost_eur if prev_snapshot else 0) + hourly_cost
        
        # Changes description
        changes = []
        if prev_snapshot:
            if abs(balance - prev_snapshot.system_balance_mw) > 200:
                changes.append(f"Balance shifted by {balance - prev_snapshot.system_balance_mw:+.0f} MW")
            if abs(avg_price - prev_snapshot.avg_price_eur_mwh) > 5:
                changes.append(f"Avg price changed by €{avg_price - prev_snapshot.avg_price_eur_mwh:+.1f}/MWh")
        
        return SystemSnapshot(
            checkpoint_type=checkpoint_type,
            timestamp=timestamp,
            hour=hour,
            zones=zones,
            total_production_mw=total_prod,
            total_consumption_mw=total_cons,
            system_balance_mw=balance,
            avg_price_eur_mwh=avg_price,
            min_price_eur_mwh=min(prices),
            max_price_eur_mwh=max(prices),
            price_spread_eur=zones[ZoneId.SE4].spot_price_eur_mwh - zones[ZoneId.SE1].spot_price_eur_mwh,
            alert_level=alert,
            active_events=active_event_names,
            hourly_cost_eur=hourly_cost,
            cumulative_cost_eur=cumulative,
            cpi_pressure_bps=cpi_pressure,
            changes_description=changes,
        )
    
    def run_simulation(self) -> Timeline:
        """Execute the simulation and generate all checkpoints."""
        
        if not self.current_timeline:
            raise RuntimeError("No timeline created")
        
        timeline = self.current_timeline
        logger.info(f"Running simulation: {timeline.name} ({timeline.total_hours}h)")
        
        prev_zones: dict[ZoneId, ZoneSnapshot] = {}
        prev_snapshot: Optional[SystemSnapshot] = None
        
        for hour in range(timeline.total_hours + 1):
            timestamp = timeline.start_time + timedelta(hours=hour)
            
            # Find active events
            active_events = [e for e in timeline.events if e.is_active_at(hour)]
            active_names = [e.name for e in active_events]
            
            # Determine checkpoint type
            if hour == 0:
                cp_type = CheckpointType.INITIAL
            elif hour == timeline.total_hours:
                cp_type = CheckpointType.FINAL
            elif active_events:
                cp_type = CheckpointType.EVENT
            else:
                cp_type = CheckpointType.HOURLY
            
            # Create zone snapshots
            zones = {}
            for zone_id, config in SWEDEN_ZONES_CONFIG.items():
                zones[zone_id] = self._create_zone_snapshot(
                    zone_id,
                    config,
                    prev_zones.get(zone_id),
                    active_events,
                )
            
            # Create system snapshot
            snapshot = self._create_system_snapshot(
                hour, timestamp, zones, active_names, prev_snapshot, cp_type
            )
            
            timeline.checkpoints.append(snapshot)
            prev_zones = zones
            prev_snapshot = snapshot
        
        # Generate summary
        timeline.summary = self._generate_summary(timeline)
        timeline.is_complete = True
        
        logger.success(f"Simulation complete: {len(timeline.checkpoints)} checkpoints")
        return timeline
    
    def _generate_summary(self, timeline: Timeline) -> SimulationSummary:
        """Analyze timeline and generate summary with key moments."""
        
        summary = SimulationSummary(
            name=timeline.name,
            total_hours=timeline.total_hours,
            num_checkpoints=len(timeline.checkpoints),
        )
        
        key_moments = []
        prev_active: set[str] = set()
        
        for cp in timeline.checkpoints:
            hour = cp.hour
            current_active = set(cp.active_events)
            
            # Event starts
            for event_name in current_active - prev_active:
                key_moments.append(KeyMoment(
                    hour=hour,
                    severity="warning",
                    category="event_start",
                    title=f"🚨 EVENT STARTED: {event_name}",
                    description=f"{event_name} begins affecting the system",
                ))
            
            # Event ends
            for event_name in prev_active - current_active:
                key_moments.append(KeyMoment(
                    hour=hour,
                    severity="info",
                    category="event_end",
                    title=f"✅ EVENT ENDED: {event_name}",
                    description=f"{event_name} impact subsiding",
                ))
            
            prev_active = current_active
            
            # Zone deficits
            for zone_id, zone in cp.zones.items():
                if zone.is_deficit:
                    key_moments.append(KeyMoment(
                        hour=hour,
                        severity="critical" if zone.balance_mw < -500 else "warning",
                        category="deficit",
                        zone=zone_id,
                        title=f"⚠️ BALANCE DEFICIT ON {zone_id.value} AT HOUR {hour}",
                        description=f"{zone_id.value} has {abs(zone.balance_mw):.0f} MW deficit",
                        value=abs(zone.balance_mw),
                        unit="MW",
                    ))
                
                # Price spikes (>50% above baseline)
                baseline = self.BASELINE_PRICES[zone_id]
                if zone.spot_price_eur_mwh > baseline * 1.5:
                    pct = (zone.spot_price_eur_mwh / baseline - 1) * 100
                    key_moments.append(KeyMoment(
                        hour=hour,
                        severity="warning",
                        category="price_spike",
                        zone=zone_id,
                        title=f"📈 PRICE SPIKE: {zone_id.value} +{pct:.0f}%",
                        description=f"Price at €{zone.spot_price_eur_mwh:.0f}/MWh",
                        value=zone.spot_price_eur_mwh,
                        unit="EUR/MWh",
                    ))
            
            # Track peaks
            for zone_id, zone in cp.zones.items():
                if zone.spot_price_eur_mwh > summary.peak_price_eur:
                    summary.peak_price_eur = zone.spot_price_eur_mwh
                    summary.peak_price_hour = hour
                    summary.peak_price_zone = zone_id
            
            if cp.system_balance_mw < summary.lowest_balance_mw:
                summary.lowest_balance_mw = cp.system_balance_mw
                summary.lowest_balance_hour = hour
            
            if cp.cpi_pressure_bps > summary.max_cpi_pressure_bps:
                summary.max_cpi_pressure_bps = cp.cpi_pressure_bps
            
            if cp.alert_level > 0:
                summary.total_alert_hours += 1
            
            if cp.system_balance_mw < 0:
                summary.total_deficit_hours += 1
        
        # Use last checkpoint for total cost
        if timeline.checkpoints:
            summary.total_system_cost_eur = timeline.checkpoints[-1].cumulative_cost_eur
        
        # Deduplicate similar consecutive events
        seen = {}
        deduped = []
        for moment in key_moments:
            key = (moment.category, moment.zone)
            if key not in seen or moment.hour - seen[key] > 2:
                deduped.append(moment)
                seen[key] = moment.hour
        
        summary.key_moments = deduped
        return summary


# ============================================================================
# PRE-BUILT EVENT TEMPLATES
# ============================================================================

EVENT_TEMPLATES: dict[str, SimulationEvent] = {
    "nordic_drought": SimulationEvent(
        event_type=EventType.DROUGHT,
        name="Nordic Drought",
        description="Severe drought reduces hydro reservoir levels across northern regions",
        start_hour=12,
        duration_hours=48,
        affected_zones=[ZoneId.SE1, ZoneId.SE2],
        severity=0.6,
        production_impact_pct={"hydro": 0.4},
        price_impact_eur=15,
    ),
    "nuclear_outage": SimulationEvent(
        event_type=EventType.NUCLEAR_OUTAGE,
        name="Nuclear Outage",
        description="Unplanned reactor shutdown at major nuclear plant",
        start_hour=6,
        duration_hours=72,
        affected_zones=[ZoneId.SE3],
        severity=0.5,
        production_impact_pct={"nuclear": 0.5},
        price_impact_eur=25,
    ),
    "cold_wave": SimulationEvent(
        event_type=EventType.COLD_WAVE,
        name="Arctic Cold Wave",
        description="Extreme cold snap increases heating demand nationwide",
        start_hour=0,
        duration_hours=72,
        affected_zones=[],
        severity=0.7,
        demand_impact_pct=0.4,
        price_impact_eur=20,
    ),
    "wind_lull": SimulationEvent(
        event_type=EventType.WIND_CALM,
        name="Scandinavian Wind Lull",
        description="High pressure system reduces wind generation",
        start_hour=24,
        duration_hours=48,
        affected_zones=[],
        severity=0.8,
        production_impact_pct={"wind": 0.7},
        price_impact_eur=10,
    ),
    "gas_crisis": SimulationEvent(
        event_type=EventType.GAS_PRICE_SPIKE,
        name="European Gas Crisis",
        description="Major gas supply disruption spikes electricity prices continent-wide",
        start_hour=0,
        duration_hours=168,
        affected_zones=[],
        severity=0.9,
        production_impact_pct={"other": 0.3},
        price_impact_eur=50,
    ),
    "cable_failure": SimulationEvent(
        event_type=EventType.CABLE_FAILURE,
        name="Baltic Cable Failure",
        description="Undersea interconnector damage reduces import capacity",
        start_hour=18,
        duration_hours=96,
        affected_zones=[ZoneId.SE4],
        severity=0.8,
        price_impact_eur=30,
    ),
}


def get_event_template(name: str) -> Optional[SimulationEvent]:
    """Get a copy of an event template."""
    template = EVENT_TEMPLATES.get(name)
    if template:
        return template.model_copy(deep=True)
    return None


def list_event_templates() -> list[str]:
    """List available event template names."""
    return list(EVENT_TEMPLATES.keys())
