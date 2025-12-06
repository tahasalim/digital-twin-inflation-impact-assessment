#!/usr/bin/env python3
"""Test script for multi-agent system."""
import asyncio
from src.agents.multi_agent import get_multi_agent_system

async def main():
    print("Initializing multi-agent system...")
    system = get_multi_agent_system()
    
    print("\nGetting agent tree...")
    nodes = system.get_agent_tree()
    print(f"Agent Nodes: {len(nodes)}")
    
    for node in nodes[:10]:  # Show first 10
        print(f"  - {node.name} ({node.role}) - Domain: {node.domain}")
    
    print("\n\nRunning nordic drought simulation...")
    result = await system.run_scenario(
        scenario_name="nordic_drought_test",
        trigger_event="nordic_drought",
        duration_hours=6,
        trigger_magnitude=0.7
    )
    
    print(f"\n✅ Simulation Complete!")
    print(f"   Predictions: {len(result['predictions'])}")
    print(f"   Signals: {len(result['signals'])}")
    print(f"   Domino Chains: {len(result['domino_chains'])}")
    
    if result['predictions']:
        print("\nSample Predictions:")
        for pred in result['predictions'][:5]:
            print(f"  - {pred['metric']}: {pred['predicted_value']:.2f} "
                  f"(confidence: {pred['confidence']:.2%})")

if __name__ == "__main__":
    asyncio.run(main())
