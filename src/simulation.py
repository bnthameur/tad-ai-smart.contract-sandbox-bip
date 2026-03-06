#!/usr/bin/env python3
"""
TAD AI - Real-Time Simulation Engine
Phase 3: Automated Exploit Execution Pipeline

Orchestrates the entire attack lifecycle:
1. Forks the chain at a specific state
2. Unleashes the AI agent to find vulnerabilities
3. Compiles and executes the exploit
4. Calculates financial impact (Profit vs Gas)
"""

import time
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path

from sandbox import SandboxManager
from agent import AIAgent, create_agent
from exploit_manager import ExploitManager
from contract_fetcher import ContractFetcher

@dataclass
class SimulationResult:
    contract_address: str
    vulnerability_found: bool
    exploit_successful: bool
    profit_eth: float
    gas_cost_eth: float
    net_profit_usd: float
    steps_taken: int
    execution_time: float
    model_used: str
    report_path: str

class SimulationEngine:
    def __init__(self, model_provider: str = "deepseek", rpc_url: str = None):
        self.agent = create_agent(model_provider)
        self.sandbox_manager = SandboxManager()
        self.exploit_manager = ExploitManager()
        self.fetcher = None # Lazy init based on chain
        self.rpc_url = rpc_url
        
    def run_simulation(
        self, 
        address: str, 
        chain: str, 
        block_number: Optional[int] = None,
        eth_price_usd: float = 3000.0
    ) -> SimulationResult:
        """Run a full end-to-end attack simulation"""
        start_time = time.time()
        print(f"🚀 Starting Simulation for {address} on {chain}...")
        
        # 1. Setup Environment
        self.fetcher = ContractFetcher(chain)
        
        # 2. Fetch Contract
        print("📥 Fetching source code...")
        contract_data = self.fetcher.fetch_source(address)
        if not contract_data or not contract_data.get("source_code"):
            print("❌ Failed to fetch contract source.")
            return self._empty_result(address, time.time() - start_time)
            
        # 3. Start Sandbox (Fork)
        print(f"🍴 Forking {chain} at block {block_number or 'latest'}...")
        sandbox = self.sandbox_manager.create_sandbox(
            f"sim_{address[:6]}", 
            self.rpc_url, 
            block_number, 
            chain
        )
        sandbox.start()
        
        try:
            # 4. AI Analysis
            print(f"🧠 AI Agent ({self.agent.model}) analyzing vulnerabilities...")
            analysis = self.agent.analyze_contract(
                contract_source=contract_data["source_code"],
                contract_address=address,
                contract_name=contract_data.get("contract_name", "Target")
            )
            
            # 5. Exploit Generation & Execution
            print("⚡ Generating and testing exploit...")
            # We assume the analysis contains the vulnerability description.
            # In a real loop, we would parse specific vulnerabilities.
            # For Phase 3, we take the raw analysis and ask for an exploit.
            
            success, test_file = self.exploit_manager.iterate_exploit(
                agent=self.agent,
                contract_source=contract_data["source_code"],
                contract_address=address,
                vulnerability=analysis.raw_response, # Feed full analysis as context
                max_iterations=3
            )
            
            # 6. Metrics Calculation
            result_metrics = self.exploit_manager.run_exploit_test(test_file)
            
            profit_eth = result_metrics.extracted_value
            # Approx gas cost (simplified)
            gas_cost_eth = (result_metrics.gas_used * 20) / 1e9 # 20 gwei assumption
            net_profit_usd = (profit_eth - gas_cost_eth) * eth_price_usd
            
            print(f"💰 Simulation Complete!")
            print(f"   Success: {success}")
            print(f"   Profit: {profit_eth:.4f} ETH")
            print(f"   Est. USD: ${net_profit_usd:.2f}")
            
            # 7. Generate Report
            report_path = self._save_report(address, analysis, result_metrics, net_profit_usd)
            
            return SimulationResult(
                contract_address=address,
                vulnerability_found=True, # Assumed if analysis ran
                exploit_successful=success,
                profit_eth=profit_eth,
                gas_cost_eth=gas_cost_eth,
                net_profit_usd=net_profit_usd,
                steps_taken=1, # TODO: Track iterations
                execution_time=time.time() - start_time,
                model_used=self.agent.model,
                report_path=str(report_path)
            )
            
        finally:
            sandbox.stop()

    def _save_report(self, address, analysis, metrics, profit_usd) -> Path:
        Path("reports").mkdir(exist_ok=True)
        path = Path(f"reports/sim_{address}_{int(time.time())}.md")
        with open(path, "w") as f:
            f.write(f"# Simulation Report: {address}\n\n")
            f.write(f"## Results\n")
            f.write(f"- **Exploit Successful:** {metrics.success}\n")
            f.write(f"- **Profit:** ${profit_usd:.2f}\n")
            f.write(f"- **Gas Used:** {metrics.gas_used}\n\n")
            f.write(f"## AI Analysis\n{analysis.raw_response}\n")
        return path

    def _empty_result(self, address, time_taken):
        return SimulationResult(address, False, False, 0, 0, 0, 0, time_taken, self.agent.model, "")

if __name__ == "__main__":
    # Test
    import os
    rpc = os.getenv("RPC_URL_MAINNET")
    if rpc:
        engine = SimulationEngine(rpc_url=rpc)
        # Test with a known address (e.g., WETH or a dummy) if needed
        print("Engine initialized. Use scripts/simulate_attack.py to run.")
