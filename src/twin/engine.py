"""Digital Twin Core Engine - State Management and Simulation Branching."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field

from src.models.energy import (
    BiddingZone,
    GridConnection,
    EnergySystemState,
    ZoneId,
    SWEDEN_ZONES_CONFIG,
    NORDIC_CONNECTIONS,
)


class TwinBranch(BaseModel):
    """A simulation branch forked from reality."""
    
    branch_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    parent_branch_id: Optional[str] = None
    
    name: str
    description: str
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Timeline
    branch_point: datetime  # When this branch diverges from reality
    current_time: datetime  # Current simulation time
    
    # State
    state: EnergySystemState
    
    # History of states for replay
    state_history: list[EnergySystemState] = Field(default_factory=list)


class DigitalTwinEngine:
    """
    Core Digital Twin Engine for Swedish Energy System.
    
    Manages:
    - Real-time state synchronization ("reality")
    - Simulation branches ("what-if" scenarios)
    - State forking and comparison
    """
    
    def __init__(self):
        self.reality_state: Optional[EnergySystemState] = None
        self.branches: dict[str, TwinBranch] = {}
        self._initialized = False
        
    def initialize(self) -> EnergySystemState:
        """Initialize the digital twin with default Swedish energy system."""
        
        # Skip if already initialized
        if self._initialized and self.reality_state is not None:
            logger.debug("Digital Twin already initialized, skipping...")
            return self.reality_state
        
        logger.info("Initializing Swedish Energy Digital Twin...")
        
        # Create zones from config
        zones = {}
        for zone_id, config in SWEDEN_ZONES_CONFIG.items():
            # Start with reasonable default values
            zones[zone_id] = BiddingZone(
                zone_id=zone_id,
                name=config["name"],
                description=config["description"],
                total_capacity_mw=config["total_capacity_mw"],
                current_production_mw=config["total_capacity_mw"] * 0.6,  # 60% utilization
                current_consumption_mw=config["total_capacity_mw"] * 0.5,
                hydro_share=config["hydro_share"],
                nuclear_share=config["nuclear_share"],
                wind_share=config["wind_share"],
                other_share=1 - config["hydro_share"] - config["nuclear_share"] - config["wind_share"],
                spot_price_eur_mwh=self._get_default_price(zone_id),
            )
        
        # Create connections
        connections = []
        for i, conn in enumerate(NORDIC_CONNECTIONS):
            connections.append(GridConnection(
                connection_id=f"conn_{i:03d}",
                from_zone=conn["from"],
                to_zone=conn["to"],
                capacity_mw=conn["capacity_mw"],
                current_flow_mw=0,  # Will be calculated
            ))
        
        # Calculate totals
        total_prod = sum(z.current_production_mw for z in zones.values())
        total_cons = sum(z.current_consumption_mw for z in zones.values())
        
        # Create initial state
        self.reality_state = EnergySystemState(
            timestamp=datetime.utcnow(),
            is_simulation=False,
            zones=zones,
            connections=connections,
            total_production_mw=total_prod,
            total_consumption_mw=total_cons,
            total_import_mw=0,
            total_export_mw=0,
            volume_weighted_avg_price_eur=sum(z.spot_price_eur_mwh for z in zones.values()) / 4,
            price_spread_se1_se4_eur=zones[ZoneId.SE4].spot_price_eur_mwh - zones[ZoneId.SE1].spot_price_eur_mwh,
            estimated_hourly_cost_meur=total_cons * 50 / 1_000_000,  # Rough estimate
        )
        
        self._initialized = True
        logger.success(f"Digital Twin initialized with {len(zones)} zones, {len(connections)} connections")
        
        return self.reality_state
    
    def _get_default_price(self, zone_id: ZoneId) -> float:
        """Get default spot price by zone (typical pattern: low in north, high in south)."""
        base_prices = {
            ZoneId.SE1: 25.0,   # Cheapest - hydro surplus
            ZoneId.SE2: 35.0,
            ZoneId.SE3: 50.0,
            ZoneId.SE4: 65.0,   # Most expensive - import dependent
        }
        return base_prices.get(zone_id, 50.0)
    
    def get_reality(self) -> EnergySystemState:
        """Get current reality state."""
        if not self._initialized or self.reality_state is None:
            raise RuntimeError("Digital twin not initialized. Call initialize() first.")
        return self.reality_state
    
    def update_reality(self, new_state: EnergySystemState) -> None:
        """Update reality with new data (e.g., from Nord Pool API)."""
        new_state.is_simulation = False
        new_state.simulation_id = None
        self.reality_state = new_state
        logger.debug(f"Reality updated: {new_state.timestamp}")
    
    def fork_branch(
        self,
        name: str,
        description: str = "",
        from_branch_id: Optional[str] = None,
    ) -> TwinBranch:
        """
        Create a new simulation branch.
        
        Fork from reality (default) or another branch.
        """
        if from_branch_id:
            parent = self.branches.get(from_branch_id)
            if not parent:
                raise ValueError(f"Branch {from_branch_id} not found")
            source_state = parent.state
            parent_id = from_branch_id
        else:
            source_state = self.get_reality()
            parent_id = None
        
        # Clone state for simulation
        branch_id = str(uuid4())[:8]
        sim_state = source_state.clone_for_simulation(branch_id)
        
        branch = TwinBranch(
            branch_id=branch_id,
            parent_branch_id=parent_id,
            name=name,
            description=description,
            branch_point=source_state.timestamp,
            current_time=source_state.timestamp,
            state=sim_state,
        )
        
        self.branches[branch_id] = branch
        logger.info(f"Created simulation branch: {name} ({branch_id})")
        
        return branch
    
    def get_branch(self, branch_id: str) -> TwinBranch:
        """Get a simulation branch by ID."""
        branch = self.branches.get(branch_id)
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")
        return branch
    
    def advance_branch(
        self,
        branch_id: str,
        delta: timedelta,
        save_history: bool = True,
    ) -> EnergySystemState:
        """
        Advance a simulation branch forward in time.
        
        The actual physics/market simulation happens in the SimulationEngine.
        """
        branch = self.get_branch(branch_id)
        
        if save_history:
            branch.state_history.append(branch.state.model_copy(deep=True))
        
        branch.current_time += delta
        branch.state.timestamp = branch.current_time
        
        return branch.state
    
    def compare_branches(
        self,
        branch_id_a: str,
        branch_id_b: Optional[str] = None,
    ) -> dict:
        """
        Compare two branches (or a branch vs reality).
        
        Returns differences in key metrics.
        """
        state_a = self.get_branch(branch_id_a).state
        
        if branch_id_b:
            state_b = self.get_branch(branch_id_b).state
            label_b = branch_id_b
        else:
            state_b = self.get_reality()
            label_b = "reality"
        
        comparison = {
            "branch_a": branch_id_a,
            "branch_b": label_b,
            "timestamp_a": state_a.timestamp.isoformat(),
            "timestamp_b": state_b.timestamp.isoformat(),
            "zones": {},
            "totals": {},
        }
        
        # Compare each zone
        for zone_id in ZoneId:
            zone_a = state_a.zones[zone_id]
            zone_b = state_b.zones[zone_id]
            
            comparison["zones"][zone_id.value] = {
                "price_diff_eur": zone_a.spot_price_eur_mwh - zone_b.spot_price_eur_mwh,
                "price_diff_pct": (zone_a.spot_price_eur_mwh / zone_b.spot_price_eur_mwh - 1) * 100 if zone_b.spot_price_eur_mwh else 0,
                "production_diff_mw": zone_a.current_production_mw - zone_b.current_production_mw,
                "consumption_diff_mw": zone_a.current_consumption_mw - zone_b.current_consumption_mw,
            }
        
        # Compare totals
        comparison["totals"] = {
            "avg_price_diff_eur": state_a.volume_weighted_avg_price_eur - state_b.volume_weighted_avg_price_eur,
            "production_diff_mw": state_a.total_production_mw - state_b.total_production_mw,
            "consumption_diff_mw": state_a.total_consumption_mw - state_b.total_consumption_mw,
            "spread_diff_eur": state_a.price_spread_se1_se4_eur - state_b.price_spread_se1_se4_eur,
        }
        
        return comparison
    
    def list_branches(self) -> list[dict]:
        """List all simulation branches."""
        return [
            {
                "branch_id": b.branch_id,
                "name": b.name,
                "description": b.description,
                "created_at": b.created_at.isoformat(),
                "branch_point": b.branch_point.isoformat(),
                "current_time": b.current_time.isoformat(),
                "history_length": len(b.state_history),
            }
            for b in self.branches.values()
        ]
    
    def delete_branch(self, branch_id: str) -> None:
        """Delete a simulation branch."""
        if branch_id in self.branches:
            del self.branches[branch_id]
            logger.info(f"Deleted branch: {branch_id}")


# Global singleton
_twin_engine: Optional[DigitalTwinEngine] = None


def get_twin_engine() -> DigitalTwinEngine:
    """Get the global digital twin engine instance."""
    global _twin_engine
    if _twin_engine is None:
        _twin_engine = DigitalTwinEngine()
    return _twin_engine
