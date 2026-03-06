#!/usr/bin/env python3
"""
TAD AI - Simulation CLI
Phase 3: Run full attack simulations
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simulation import SimulationEngine

def main():
    parser = argparse.ArgumentParser(description="TAD AI - Attack Simulation")
    parser.add_argument("address", help="Target contract address")
    parser.add_argument("--chain", default="ethereum", help="Target chain")
    parser.add_argument("--block", type=int, help="Fork block number")
    parser.add_argument("--model", default="deepseek", help="AI Model provider")
    parser.add_argument("--rpc", default=os.getenv("RPC_URL_MAINNET"), help="RPC Provider URL")
    
    args = parser.parse_args()
    
    if not args.rpc:
        print("❌ Error: --rpc or RPC_URL_MAINNET env var required")
        sys.exit(1)
        
    engine = SimulationEngine(model_provider=args.model, rpc_url=args.rpc)
    
    try:
        result = engine.run_simulation(
            address=args.address,
            chain=args.chain,
            block_number=args.block
        )
        
        print("\n" + "="*50)
        print("🏁 SIMULATION RESULTS")
        print("="*50)
        print(f"Target: {result.contract_address}")
        print(f"Model:  {result.model_used}")
        print(f"Status: {'✅ PWNED' if result.exploit_successful else '🛡️ SECURE (or failed)'}")
        print(f"Profit: ${result.net_profit_usd:.2f}")
        print(f"Report: {result.report_path}")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n🚫 Simulation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
