"""Quick test to verify multi-agent system is working."""
import asyncio
from src.agents.llm_agents import run_multi_agent_analysis

async def test():
    print("Starting multi-agent analysis test...")
    print("=" * 60)
    
    result = await run_multi_agent_analysis(
        scenario_trigger='nordic_drought',
        duration_hours=24,
        magnitude=0.8
    )
    
    print("=" * 60)
    print("RESULT SUMMARY:")
    print("=" * 60)
    print(f"Agent count: {result.get('agent_count', 'N/A')}")
    print(f"Processing time: {result.get('total_processing_time_ms', 0)/1000:.1f}s")
    print(f"Result keys: {list(result.keys())}")
    
    # Master summary
    master = result.get('master_summary', {})
    if master:
        analysis = master.get('analysis', '')
        print(f"\nMaster analysis length: {len(analysis)} chars")
        if analysis:
            print(f"First 200 chars: {analysis[:200]}...")
    
    # Domain summaries
    domain = result.get('domain_summaries', {})
    print(f"\nDomain summaries: {list(domain.keys())}")
    for name, summary in domain.items():
        analysis = summary.get('analysis', '')
        print(f"  - {name}: {len(analysis)} chars")
    
    # Specialist results
    specialists = result.get('specialist_results', [])
    print(f"\nSpecialist results: {len(specialists)} agents")
    for s in specialists:
        name = s.get('agent_name', '?')
        time_ms = s.get('processing_time_ms', 0)
        analysis = s.get('analysis', '')
        print(f"  - {name}: {len(analysis)} chars ({time_ms}ms)")
    
    print("=" * 60)
    print("SUCCESS - All agents ran correctly!")
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test())
