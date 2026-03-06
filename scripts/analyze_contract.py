#!/usr/bin/env python3
"""
Main analysis script - Phase 1
Analyzes a smart contract using AI agents in a sandboxed environment
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sandbox import SandboxManager, SandboxConfig
from contract_fetcher import ContractFetcher


def main():
    parser = argparse.ArgumentParser(
        description="TAD AI - Smart Contract Security Analysis"
    )
    parser.add_argument(
        "address",
        help="Contract address to analyze"
    )
    parser.add_argument(
        "--chain",
        default="ethereum",
        choices=["ethereum", "bsc", "polygon", "arbitrum"],
        help="Blockchain network"
    )
    parser.add_argument(
        "--block",
        type=int,
        help="Fork block number (default: latest)"
    )
    parser.add_argument(
        "--model",
        default="deepseek",
        choices=["deepseek", "qwen", "kimi", "anthropic"],
        help="AI model to use"
    )
    parser.add_argument(
        "--rpc",
        default=os.getenv("RPC_URL_MAINNET"),
        help="RPC URL for forking"
    )
    parser.add_argument(
        "--output",
        default="reports",
        help="Output directory for reports"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  TAD AI - Smart Contract Security Sandbox")
    print("  Phase 1: Environment Setup")
    print("=" * 60)
    print()
    
    # Validate inputs
    if not args.rpc:
        print("❌ Error: --rpc required or set RPC_URL_MAINNET env var")
        sys.exit(1)
    
    # Step 1: Fetch contract source
    print("📥 Step 1: Fetching contract source...")
    fetcher = ContractFetcher(args.chain)
    contract = fetcher.fetch_source(args.address)
    
    if not contract:
        print("❌ Failed to fetch contract. Exiting.")
        sys.exit(1)
    
    print(f"   Contract: {contract.get('contract_name', 'Unknown')}")
    print(f"   Compiler: {contract.get('compiler_version', 'Unknown')}")
    print()
    
    # Save contract
    contract_path = fetcher.save_contract(contract)
    print(f"💾 Contract saved to: {contract_path}")
    print()
    
    # Step 2: Setup sandbox
    print("🔒 Step 2: Setting up sandbox environment...")
    manager = SandboxManager()
    sandbox = manager.create_sandbox(
        name="analysis",
        rpc_url=args.rpc,
        fork_block=args.block,
        chain=args.chain
    )
    
    # Step 3: Start sandbox
    print("🚀 Step 3: Starting Anvil fork...")
    if not sandbox.start():
        print("❌ Failed to start sandbox. Exiting.")
        sys.exit(1)
    
    print(f"   Sandbox RPC: {sandbox.get_rpc_url()}")
    print()
    
    # Step 4: Analysis (Phase 1 - basic structure only)
    print("🤖 Step 4: AI Analysis (Phase 1 placeholder)...")
    print("   ⚠️  Full AI agent integration coming in Phase 2")
    print("   Current capabilities:")
    print("   - Contract source fetching ✓")
    print("   - Sandbox environment ✓")
    print("   - Blockchain forking ✓")
    print()
    
    # Keep running until user stops
    print("=" * 60)
    print("✅ Sandbox ready for analysis!")
    print("   Press Ctrl+C to stop and cleanup")
    print("=" * 60)
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🔄 Cleaning up...")
    finally:
        sandbox.stop()
        print("✅ Done!")


if __name__ == "__main__":
    main()
