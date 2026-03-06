#!/usr/bin/env python3
"""
Main Analysis Script - Phase 2
Full integration: Sandbox + AI Agent + Exploit Generation
"""

import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sandbox import SandboxManager
from contract_fetcher import ContractFetcher
from agent import create_agent, ModelProvider
from exploit_manager import ExploitManager


def main():
    parser = argparse.ArgumentParser(
        description="TAD AI Phase 2 - Smart Contract Analysis with AI Agent"
    )
    parser.add_argument("address", help="Contract address")
    parser.add_argument("--chain", default="ethereum", 
                       choices=["ethereum", "bsc", "polygon", "arbitrum"])
    parser.add_argument("--block", type=int, help="Fork block")
    parser.add_argument("--model", default="deepseek",
                       choices=["deepseek", "qwen", "kimi", "anthropic"])
    parser.add_argument("--rpc", default=os.getenv("RPC_URL_MAINNET"))
    parser.add_argument("--output", default="reports")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  TAD AI - Smart Contract Security Sandbox")
    print("  Phase 2: AI Agent Integration")
    print("=" * 70)
    print()
    
    if not args.rpc:
        print("❌ Error: --rpc or RPC_URL_MAINNET required")
        sys.exit(1)
    
    # Step 1: Fetch contract
    print("📥 Step 1: Fetching contract...")
    fetcher = ContractFetcher(args.chain)
    contract = fetcher.fetch_source(args.address)
    
    if not contract:
        print("❌ Failed to fetch contract")
        sys.exit(1)
    
    print(f"   Name: {contract.get('contract_name', 'Unknown')}")
    print()
    
    # Save contract
    contract_path = fetcher.save_contract(contract)
    
    # Step 2: Setup sandbox
    print("🔒 Step 2: Starting sandbox...")
    manager = SandboxManager()
    sandbox = manager.create_sandbox(
        "analysis", args.rpc, args.block, args.chain
    )
    
    if not sandbox.start():
        print("❌ Failed to start sandbox")
        sys.exit(1)
    
    print(f"   RPC: {sandbox.get_rpc_url()}")
    print()
    
    # Step 3: Initialize AI Agent
    print(f"🤖 Step 3: Initializing {args.model} agent...")
    try:
        agent = create_agent(args.model)
        print(f"   Model: {agent.model}")
        print(f"   Provider: {agent.provider.value}")
        print()
    except ValueError as e:
        print(f"❌ {e}")
        sandbox.stop()
        sys.exit(1)
    
    # Step 4: AI Analysis
    print("🔍 Step 4: Running AI security analysis...")
    source_code = contract.get('source_code', '')
    
    if not source_code:
        print("❌ No source code available")
        sandbox.stop()
        sys.exit(1)
    
    response = agent.analyze_contract(
        contract_source=source_code,
        contract_address=args.address,
        contract_name=contract.get('contract_name', 'Contract')
    )
    
    print("\n" + "=" * 70)
    print("SECURITY ANALYSIS REPORT")
    print("=" * 70)
    print(response.raw_response)
    print()
    
    # Save report
    report_dir = Path(args.output)
    report_dir.mkdir(exist_ok=True)
    report_file = report_dir / f"analysis_{args.address[:8]}_{args.model}.md"
    
    with open(report_file, "w") as f:
        f.write(f"# Security Analysis Report\n\n")
        f.write(f"**Contract:** {contract.get('contract_name', 'Unknown')}\n")
        f.write(f"**Address:** {args.address}\n")
        f.write(f"**Chain:** {args.chain}\n")
        f.write(f"**Model:** {args.model}\n")
        f.write(f"**Cost:** ${response.cost:.4f}\n")
        f.write(f"**Tokens:** {response.tokens_used:,}\n\n")
        f.write("---\n\n")
        f.write(response.raw_response)
    
    print(f"💾 Report saved to {report_file}")
    
    # Step 5: Generate exploits (optional)
    print("\n🔧 Step 5: Exploit generation...")
    print("   ⚠️  Exploit generation requires working Foundry tests")
    print("   This is a placeholder for Phase 2 complete integration")
    
    # Cleanup
    print("\n" + "=" * 70)
    input("Press Enter to stop sandbox...")
    
    sandbox.stop()
    
    # Summary
    print("\n📊 Summary:")
    print(f"   Contract: {contract.get('contract_name')}")
    print(f"   Model: {args.model}")
    print(f"   Cost: ${agent.total_cost:.4f}")
    print(f"   Tokens: {agent.total_tokens:,}")
    print(f"   Report: {report_file}")


if __name__ == "__main__":
    main()
