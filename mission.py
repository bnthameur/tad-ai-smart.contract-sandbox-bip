#!/usr/bin/env python3
"""
TAD AI - Mission CLI
Run autonomous exploitation missions with the 4-agent swarm.
"""

import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.swarm.mission_controller import MissionController
from src.contract_fetcher import ContractFetcher

def main():
    parser = argparse.ArgumentParser(
        description="TAD AI - Autonomous Exploitation Mission",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 60-minute mission to extract 0.1 ETH
  python mission.py 0xContractAddress --chain ethereum
  
  # Aggressive 30-minute mission for 1 ETH
  python mission.py 0xContractAddress --duration 30 --target 1.0
  
  # Use different AI model
  python mission.py 0xContractAddress --model anthropic
        """
    )
    
    parser.add_argument("address", help="Target contract address")
    parser.add_argument("--chain", default="ethereum", help="Blockchain (ethereum, bsc, polygon)")
    parser.add_argument("--model", default="deepseek", 
                       help="AI model (deepseek, anthropic, openai, google, qwen, kimi)")
    parser.add_argument("--duration", type=int, default=60, help="Mission duration in minutes (default: 60)")
    parser.add_argument("--target", type=float, default=0.1, help="Target profit in ETH (default: 0.1)")
    parser.add_argument("--rpc", default=os.getenv("RPC_URL_MAINNET"), help="RPC URL")
    parser.add_argument("--local-source", help="Path to local Solidity file (skip fetching)")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  TAD AI - AUTONOMOUS EXPLOITATION MISSION")
    print("  4-Agent Swarm: Strategist → Developer → Executor → Evaluator")
    print("=" * 70)
    print()
    
    # Fetch contract source
    if args.local_source:
        print(f"📄 Loading local source: {args.local_source}")
        with open(args.local_source) as f:
            source = f.read()
    else:
        if not args.rpc:
            print("❌ Error: --rpc or RPC_URL_MAINNET required for fetching")
            sys.exit(1)
        
        print(f"🔍 Fetching contract from {args.chain}...")
        fetcher = ContractFetcher(args.chain)
        contract = fetcher.fetch_source(args.address)
        
        if not contract or not contract.get("source_code"):
            print("❌ Failed to fetch contract source")
            sys.exit(1)
        
        source = contract["source_code"]
        print(f"   Name: {contract.get('contract_name', 'Unknown')}")
        print(f"   Lines: {len(source.splitlines())}")
    
    print()
    
    # Start mission
    controller = MissionController(
        contract_address=args.address,
        chain=args.chain,
        contract_source=source,
        model_provider=args.model,
        max_duration_minutes=args.duration,
        target_profit_eth=args.target,
        rpc_url=args.rpc
    )
    
    try:
        final_state = controller.run_mission()
        report = controller.get_report()
        
        print("\n" + "=" * 70)
        print("  MISSION REPORT")
        print("=" * 70)
        print(f"Status:          {report['status'].upper()}")
        print(f"Duration:        {report['duration']}")
        print(f"Total Profit:    {report['total_profit_eth']:.4f} ETH (${report['total_profit_usd']:.2f})")
        print(f"Attempts:        {report['attempts_count']} (Successful: {report['successful_attempts']})")
        
        if report['best_strategy']:
            print(f"Best Strategy:   {report['best_strategy']}")
            print(f"Best Profit:     ${report['best_profit_usd']:.2f}")
        
        print("=" * 70)
        
        # Exit code based on success
        sys.exit(0 if report['status'] == 'success' else 1)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Mission aborted by user")
        sys.exit(130)

if __name__ == "__main__":
    main()
