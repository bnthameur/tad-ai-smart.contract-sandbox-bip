#!/usr/bin/env python3
"""
TAD AI - Benchmarking Harness
Phase 4: Automated performance evaluation
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from agent import create_agent, ModelProvider

@dataclass
class BenchmarkResult:
    model: str
    contract: str
    vulnerability_found: bool
    exploit_successful: bool
    tokens_used: int
    cost_usd: float
    execution_time: float
    error: str = ""

class BenchmarkHarness:
    def __init__(self, dataset_path: str = "data/historical"):
        self.dataset_path = Path(dataset_path)
        self.results: List[BenchmarkResult] = []
        
    def run_benchmark(self, model_provider: str, sample_size: int = 10):
        """Run benchmark for a specific model"""
        print(f"\n{'='*60}")
        print(f"BENCHMARK: {model_provider.upper()}")
        print(f"{'='*60}\n")
        
        agent = create_agent(model_provider)
        
        # Load dataset
        manifest = self.dataset_path / "hacks.json"
        if not manifest.exists():
            print("❌ Dataset manifest not found")
            return
            
        with open(manifest) as f:
            hacks = json.load(f)[:sample_size]
        
        print(f"📊 Testing against {len(hacks)} contracts...\n")
        
        for hack in hacks:
            print(f"🎯 {hack['name']} ({hack['vulnerability_type']})")
            
            start = time.time()
            
            # Load contract source
            source_file = self.dataset_path / hack['chain'] / hack['address'] / f"{hack.get('contract_name', 'Contract')}.sol"
            
            if not source_file.exists():
                print(f"   ⚠️  Source not available, skipping")
                continue
                
            with open(source_file) as f:
                source = f.read()
            
            try:
                # Run analysis
                response = agent.analyze_contract(
                    contract_source=source,
                    contract_address=hack['address']
                )
                
                # Check if vulnerability was detected
                vuln_found = len(response.vulnerabilities) > 0
                
                # Check if exploit generated (simplified check)
                exploit_ok = len(response.exploit_code) > 100 and "contract" in response.exploit_code.lower()
                
                result = BenchmarkResult(
                    model=model_provider,
                    contract=hack['name'],
                    vulnerability_found=vuln_found,
                    exploit_successful=exploit_ok,
                    tokens_used=response.tokens_used,
                    cost_usd=response.cost,
                    execution_time=time.time() - start
                )
                
            except Exception as e:
                result = BenchmarkResult(
                    model=model_provider,
                    contract=hack['name'],
                    vulnerability_found=False,
                    exploit_successful=False,
                    tokens_used=0,
                    cost_usd=0,
                    execution_time=time.time() - start,
                    error=str(e)
                )
            
            self.results.append(result)
            print(f"   {'✅' if vuln_found else '❌'} Vuln | {'✅' if exploit_ok else '❌'} Exploit | ${result.cost_usd:.4f} | {result.execution_time:.1f}s")
        
        self._generate_report(model_provider)
    
    def _generate_report(self, model: str):
        """Generate benchmark report"""
        print(f"\n{'='*60}")
        print(f"REPORT: {model.upper()}")
        print(f"{'='*60}\n")
        
        model_results = [r for r in self.results if r.model == model]
        
        if not model_results:
            print("No results")
            return
            
        total = len(model_results)
        vuln_detected = sum(1 for r in model_results if r.vulnerability_found)
        exploits_gen = sum(1 for r in model_results if r.exploit_successful)
        total_cost = sum(r.cost_usd for r in model_results)
        avg_time = sum(r.execution_time for r in model_results) / total
        
        print(f"Total Contracts:    {total}")
        print(f"Vulns Detected:     {vuln_detected} ({vuln_detected/total*100:.1f}%)")
        print(f"Exploits Generated: {exploits_gen} ({exploits_gen/total*100:.1f}%)")
        print(f"Total Cost:         ${total_cost:.4f}")
        print(f"Avg Cost/Contract:  ${total_cost/total:.4f}")
        print(f"Avg Time/Contract:  {avg_time:.1f}s")
        
        # Save JSON report
        report_file = Path("reports") / f"benchmark_{model}_{int(time.time())}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, "w") as f:
            json.dump([asdict(r) for r in model_results], f, indent=2)
        
        print(f"\n💾 Report saved: {report_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="deepseek", help="Model to benchmark")
    parser.add_argument("--sample", type=int, default=10, help="Number of contracts")
    args = parser.parse_args()
    
    harness = BenchmarkHarness()
    harness.run_benchmark(args.model, args.sample)
